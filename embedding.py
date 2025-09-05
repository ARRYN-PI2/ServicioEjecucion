import json
import os
import requests
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, BulkWriteError
import numpy as np

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BGEEmbeddingGenerator:
    """
    Generador de embeddings usando BGE-M3 en Ollama local
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "bge-m3:latest"
        self.verify_ollama_connection()
    
    def verify_ollama_connection(self):
        """Verificar que Ollama esté funcionando y tenga el modelo BGE-M3"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                if self.model_name in model_names:
                    logger.info(f"✅ BGE-M3 model found in Ollama")
                else:
                    logger.warning(f"⚠️  BGE-M3 model not found. Available models: {model_names}")
                    logger.info("Run: ollama pull bge-m3:latest")
            else:
                logger.error("❌ Cannot connect to Ollama")
        except Exception as e:
            logger.error(f"❌ Ollama connection error: {e}")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generar embedding para un texto usando BGE-M3
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": text
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding', [])
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def process_product_text(self, producto: Dict[str, Any]) -> str:
        """
        Combinar información del producto en un texto coherente para embeddings
        """
        # Extraer información relevante
        titulo = producto.get('titulo', '')
        marca = producto.get('marca', '')
        precio = producto.get('precio', '')
        tamaño = producto.get('tamaño', '')
        categoria = producto.get('categoria', '')
        
        # Crear texto combinado optimizado para embeddings
        texto_completo = f"{titulo} {marca} {categoria} {tamaño} televisor"
        
        # Limpiar y normalizar
        texto_completo = ' '.join(texto_completo.split())
        texto_completo = texto_completo.replace('N/A', '').strip()
        
        return texto_completo

class MongoDBManager:
    """
    Gestor de conexión y operaciones con MongoDB Atlas
    """
    
    def __init__(self, connection_string: str, db_password: str):
        self.connection_string = connection_string.replace('<db_password>', db_password)
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establecer conexión con MongoDB Atlas"""
        try:
            self.client = MongoClient(self.connection_string)
            # Verificar conexión
            self.client.admin.command('ping')
            self.db = self.client['smartcompare_ai']  # Nombre de la base de datos
            logger.info("✅ Connected to MongoDB Atlas")
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    def get_collections(self):
        """Obtener referencias a las colecciones necesarias"""
        return {
            'products': self.db['products'],
            'product_embeddings': self.db['product_embeddings'],
            'embedding_metadata': self.db['embedding_metadata']
        }
    
    def save_product_with_embedding(self, producto: Dict[str, Any], 
                                  embedding: List[float], 
                                  embedding_text: str) -> bool:
        """
        Guardar producto y su embedding en MongoDB
        """
        try:
            collections = self.get_collections()
            
            # Generar ID único del producto
            product_id = f"falabella_{producto.get('contador_extraccion', '')}"
            
            # Documento del producto
            product_doc = {
                "_id": product_id,
                "product_id": product_id,
                "name": producto.get('titulo', ''),
                "brand": producto.get('marca', ''),
                "category": "Televisores",
                "subcategory": producto.get('tamaño', ''),
                "price": self.parse_price(producto.get('precio', '')),
                "currency": "COP",
                "description": producto.get('titulo', ''),
                "specifications": {
                    "screen_size": producto.get('tamaño', ''),
                    "category": producto.get('categoria', '')
                },
                "image_urls": {
                    "main": producto.get('imagen', ''),
                    "thumbnail": producto.get('imagen', '')
                },
                "source_info": {
                    "store_name": producto.get('fuente', ''),
                    "store_url": producto.get('link', ''),
                    "scraped_at": datetime.fromisoformat(producto.get('fecha_extraccion', '')),
                    "last_updated": datetime.now()
                },
                "ratings": {
                    "average_rating": self.parse_rating(producto.get('calificacion', '')),
                    "review_count": 0
                },
                "extraction_metadata": {
                    "extraction_status": producto.get('extraction_status', ''),
                    "pagina": producto.get('pagina', 1)
                }
            }
            
            # Documento del embedding
            embedding_doc = {
                "_id": f"emb_{product_id}",
                "product_id": product_id,
                "bert_embedding": embedding,
                "embedding_text": embedding_text,
                "embedding_model": "bge-m3:latest",
                "embedding_dimension": len(embedding),
                "generated_at": datetime.now(),
                "similarity_scores": {
                    "text_similarity": 0.0,
                    "feature_similarity": 0.0,
                    "combined_score": 0.0
                }
            }
            
            # Insertar o actualizar producto
            collections['products'].replace_one(
                {"_id": product_id}, 
                product_doc, 
                upsert=True
            )
            
            # Insertar o actualizar embedding
            collections['product_embeddings'].replace_one(
                {"_id": f"emb_{product_id}"}, 
                embedding_doc, 
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")
            return False
    
    def parse_price(self, precio_str: str) -> float:
        """Convertir string de precio a número"""
        try:
            if isinstance(precio_str, str) and '$' in precio_str:
                # Remover $ y comas, convertir a float
                clean_price = precio_str.replace('$', '').replace('.', '').replace(',', '')
                return float(clean_price)
            return 0.0
        except:
            return 0.0
    
    def parse_rating(self, rating_str: str) -> float:
        """Convertir string de calificación a número"""
        try:
            if isinstance(rating_str, str) and rating_str != 'N/A':
                return float(rating_str)
            return 0.0
        except:
            return 0.0
    
    def save_batch_metadata(self, total_processed: int, total_errors: int, 
                          batch_start: datetime, batch_end: datetime):
        """Guardar metadatos del batch de procesamiento"""
        try:
            collections = self.get_collections()
            metadata_doc = {
                "batch_id": f"embedding_batch_{int(batch_start.timestamp())}",
                "total_products_processed": total_processed,
                "total_errors": total_errors,
                "success_rate": (total_processed / (total_processed + total_errors)) * 100 if total_processed + total_errors > 0 else 0,
                "processing_start": batch_start,
                "processing_end": batch_end,
                "duration_seconds": (batch_end - batch_start).total_seconds(),
                "embedding_model": "bge-m3:latest",
                "source_file": "productos.json"
            }
            collections['embedding_metadata'].insert_one(metadata_doc)
            logger.info("✅ Batch metadata saved")
        except Exception as e:
            logger.error(f"Error saving batch metadata: {e}")

def main():
    """
    Función principal para procesar productos.json y generar embeddings
    """
    # Configuración
    DB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'tu_password_aqui')
    CONNECTION_STRING = "mongodb+srv://arrynMongodb:<db_password>@arrynpi2.1cherui.mongodb.net/?retryWrites=true&w=majority&appName=ArrynPI2"
    
    if DB_PASSWORD == 'tu_password_aqui':
        logger.error("❌ Please set MONGODB_PASSWORD environment variable")
        print("\nHow to set password:")
        print("export MONGODB_PASSWORD='your_actual_password'")
        return
    
    # Inicializar componentes
    logger.info("🚀 Starting embedding generation process...")
    batch_start = datetime.now()
    
    try:
        # Conectar a servicios
        embedding_generator = BGEEmbeddingGenerator()
        mongodb_manager = MongoDBManager(CONNECTION_STRING, DB_PASSWORD)
        
        # Cargar productos desde JSON
        with open('productos.json', 'r', encoding='utf-8') as f:
            productos = json.load(f)
        
        logger.info(f"📊 Processing {len(productos)} products...")
        
        # Procesar cada producto
        total_processed = 0
        total_errors = 0
        
        for i, producto in enumerate(productos, 1):
            try:
                logger.info(f"Processing product {i}/{len(productos)}: {producto.get('titulo', 'Unknown')[:50]}...")
                
                # Generar texto para embedding
                embedding_text = embedding_generator.process_product_text(producto)
                
                # Generar embedding
                embedding = embedding_generator.generate_embedding(embedding_text)
                
                if embedding:
                    # Guardar en MongoDB
                    success = mongodb_manager.save_product_with_embedding(
                        producto, embedding, embedding_text
                    )
                    
                    if success:
                        total_processed += 1
                        logger.info(f"✅ Product {i} processed successfully")
                    else:
                        total_errors += 1
                        logger.error(f"❌ Failed to save product {i}")
                else:
                    total_errors += 1
                    logger.error(f"❌ Failed to generate embedding for product {i}")
                
                # Pequeña pausa para no sobrecargar los servicios
                time.sleep(0.5)
                
            except Exception as e:
                total_errors += 1
                logger.error(f"❌ Error processing product {i}: {e}")
        
        # Guardar metadatos del batch
        batch_end = datetime.now()
        mongodb_manager.save_batch_metadata(
            total_processed, total_errors, batch_start, batch_end
        )
        
        # Resumen final
        logger.info("🏁 Processing completed!")
        logger.info(f"✅ Successfully processed: {total_processed}")
        logger.info(f"❌ Errors: {total_errors}")
        logger.info(f"⏱️  Total time: {(batch_end - batch_start).total_seconds():.2f} seconds")
        logger.info(f"📈 Success rate: {(total_processed / len(productos) * 100):.2f}%")
        
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        return

if __name__ == "__main__":
    main()
