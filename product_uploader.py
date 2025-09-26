import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from dotenv import load_dotenv
import hashlib

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MongoDBManager:
    """
    Gestor de conexión y operaciones con MongoDB Atlas
    """
    
    def __init__(self, connection_string: str, db_password: str, database_name: str = "smartcompare_ai"):
        self.connection_string = connection_string.replace('<db_password>', db_password)
        self.database_name = database_name
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establecer conexión con MongoDB Atlas"""
        try:
            self.client = MongoClient(self.connection_string)
            # Verificar conexión
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            logger.info("✅ Connected to MongoDB Atlas")
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    def get_collection(self, collection_name: str):
        """Obtener referencia a una colección específica"""
        return self.db[collection_name]
    
    def parse_price(self, precio_texto: str) -> float:
        """Extraer valor numérico del precio"""
        try:
            # Remover texto no numérico y convertir
            price_clean = precio_texto.replace('COP', '').replace(',', '').replace('.', '').strip()
            return float(price_clean)
        except (ValueError, AttributeError):
            return 0.0
    
    def parse_rating(self, calificacion: str) -> float:
        """Convertir calificación a float"""
        try:
            return float(calificacion) if calificacion else 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def calcular_hash_producto(self, producto: Dict[str, Any]) -> str:
        """Generar hash único del producto basado en campos clave"""
        campos_hash = [
            producto.get('titulo', '').lower().strip(),
            producto.get('marca', '').lower().strip(),
            producto.get('fuente', '').lower().strip(),
            str(producto.get('precio_valor', 0))
    ]
        hash_string = '|'.join(campos_hash)
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    def save_product(self, producto: Dict[str, Any], collection_name: str = "products") -> bool:
        """
        Guardar producto en MongoDB
        """
        try:
            collection = self.get_collection(collection_name)
        
            # Generar ID único del producto basado en la fuente y contador
            fuente = producto.get('fuente', 'unknown')
            contador = producto.get('contador_extraccion', '')
            product_id = f"{fuente}_{contador}"
            
            # Generar hash único del producto
            product_hash = self.calcular_hash_producto(producto)
            
            # Documento del producto basado en el formato proporcionado
            product_doc = {
                "_id": product_id,
                "product_id": product_id,
                "product_hash": product_hash,
                "contador_extraccion_total": producto.get('contador_extraccion_total', 0),
                "contador_extraccion": producto.get('contador_extraccion', 0),
                "name": producto.get('titulo', ''),
                "brand": producto.get('marca', ''),
                "category": producto.get('categoria', ''),
                "price_text": producto.get('precio_texto', ''),
                "price_value": producto.get('precio_valor', 0),
                "currency": producto.get('moneda', 'COP'),
                "size": producto.get('tamaño', ''),
                "rating": self.parse_rating(producto.get('calificacion', '')),
                "additional_details": producto.get('detalles_adicionales', ''),
                "source": producto.get('fuente', ''),
                "image_url": producto.get('imagen', ''),
                "product_link": producto.get('link', ''),
                "page": producto.get('pagina', 1),
                "extraction_date": producto.get('fecha_extraccion', ''),
                "extraction_status": producto.get('extraction_status', ''),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Insertar o actualizar el documento
            result = collection.replace_one(
                {"_id": product_id}, 
                product_doc, 
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"✅ Product inserted: {product_id}")
                return True
            elif result.modified_count > 0:
                logger.info(f"🔄 Product updated: {product_id}")
                return True
            else:
                logger.info(f"ℹ️ Product unchanged: {product_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error saving product {product_id}: {e}")
            return False
    
    def save_products_batch(self, productos: List[Dict[str, Any]], collection_name: str = "products") -> Dict[str, int]:
        """
        Guardar múltiples productos en lote
        """
        stats = {"inserted": 0, "updated": 0, "errors": 0}
        
        for producto in productos:
            try:
                if self.save_product(producto, collection_name):
                    stats["inserted"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error processing product: {e}")
                stats["errors"] += 1
        
        return stats
    
    def close_connection(self):
        """Cerrar conexión con MongoDB"""
        if self.client:
            self.client.close()
            logger.info("🔌 MongoDB connection closed")

class ProductUploader:
    """
    Clase principal para cargar productos desde JSON a MongoDB
    """
    
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()
        
        self.connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        self.db_password = os.getenv('MONGODB_PASSWORD')
        self.database_name = os.getenv('DATABASE_NAME', 'smartcompare_ai')
        self.collection_name = os.getenv('COLLECTION_NAME', 'products')
        
        if not self.connection_string or not self.db_password:
            raise ValueError("❌ MongoDB connection string and password must be set in .env file")
        
        self.mongo_manager = MongoDBManager(
            self.connection_string, 
            self.db_password,
            self.database_name
        )
    
    def load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Cargar datos desde archivo JSON
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Si es una lista, devolverla directamente
                if isinstance(data, list):
                    return data
                # Si es un objeto único, convertirlo a lista
                elif isinstance(data, dict):
                    return [data]
                else:
                    raise ValueError("Invalid JSON format")
                    
        except FileNotFoundError:
            logger.error(f"❌ File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON format: {e}")
            raise
    
    def upload_from_file(self, file_path: str) -> Dict[str, int]:
        """
        Cargar productos desde archivo JSON y subirlos a MongoDB
        """
        logger.info(f"📂 Loading products from: {file_path}")
        
        # Cargar datos del archivo
        productos = self.load_json_file(file_path)
        logger.info(f"📊 Found {len(productos)} products to upload")
        
        # Subir productos a MongoDB
        stats = self.mongo_manager.save_products_batch(productos, self.collection_name)
        
        logger.info(f"📈 Upload completed - Inserted: {stats['inserted']}, Updated: {stats['updated']}, Errors: {stats['errors']}")
        
        return stats
    
    def upload_from_json_string(self, json_string: str) -> Dict[str, int]:
        """
        Cargar productos desde string JSON y subirlos a MongoDB
        """
        try:
            data = json.loads(json_string)
            
            # Si es una lista, usarla directamente
            if isinstance(data, list):
                productos = data
            # Si es un objeto único, convertirlo a lista
            elif isinstance(data, dict):
                productos = [data]
            else:
                raise ValueError("Invalid JSON format")
            
            logger.info(f"📊 Found {len(productos)} products to upload from JSON string")
            
            # Subir productos a MongoDB
            stats = self.mongo_manager.save_products_batch(productos, self.collection_name)
            
            logger.info(f"📈 Upload completed - Inserted: {stats['inserted']}, Updated: {stats['updated']}, Errors: {stats['errors']}")
            
            return stats
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON format: {e}")
            raise
    
    def close(self):
        """Cerrar conexiones"""
        self.mongo_manager.close_connection()

def main():
    """
    Función principal para ejecutar el script desde línea de comandos
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload products from JSON to MongoDB')
    parser.add_argument('--file', '-f', type=str, help='JSON file path to upload')
    parser.add_argument('--json', '-j', type=str, help='JSON string to upload')
    
    args = parser.parse_args()
    
    if not args.file and not args.json:
        logger.error("❌ Please provide either --file or --json parameter")
        return
    
    try:
        uploader = ProductUploader()
        
        if args.file:
            stats = uploader.upload_from_file(args.file)
        elif args.json:
            stats = uploader.upload_from_json_string(args.json)
        
        print(f"\n🎉 Upload Summary:")
        print(f"   • Inserted: {stats['inserted']}")
        print(f"   • Updated: {stats['updated']}")
        print(f"   • Errors: {stats['errors']}")
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
    finally:
        uploader.close()
        
        
        

if __name__ == "__main__":
    main()
