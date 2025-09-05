import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MongoBackupManager:
    """
    Gestor para hacer backup y limpiar colecciones de MongoDB
    """
    
    def __init__(self):
        load_dotenv()
        
        self.connection_string = os.getenv('MONGODB_CONNECTION_STRING')
        self.db_password = os.getenv('MONGODB_PASSWORD')
        self.database_name = os.getenv('DATABASE_NAME', 'smartcompare_ai')
        
        if not self.connection_string or not self.db_password:
            raise ValueError("❌ MongoDB credentials not found in .env file")
        
        # Conectar a MongoDB
        connection_str = self.connection_string.replace('<db_password>', self.db_password)
        self.client = MongoClient(connection_str)
        self.db = self.client[self.database_name]
        
        # Verificar conexión
        self.client.admin.command('ping')
        logger.info("✅ Connected to MongoDB Atlas")
    
    def backup_collection(self, collection_name: str, backup_folder: str = "backups") -> str:
        """
        Hacer backup de una colección completa
        """
        try:
            # Crear carpeta de backup si no existe
            os.makedirs(backup_folder, exist_ok=True)
            
            collection = self.db[collection_name]
            
            # Obtener todos los documentos
            logger.info(f"📦 Starting backup of collection '{collection_name}'...")
            documents = list(collection.find())
            
            if not documents:
                logger.warning(f"⚠️ Collection '{collection_name}' is empty")
                return None
            
            # Crear nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{collection_name}_backup_{timestamp}.json"
            backup_path = os.path.join(backup_folder, backup_filename)
            
            # Convertir ObjectId y datetime a string para JSON serialization
            def convert_doc_for_json(doc):
                """Convertir documento para serialización JSON"""
                if isinstance(doc, dict):
                    converted = {}
                    for key, value in doc.items():
                        if key == '_id':
                            converted[key] = str(value)
                        elif isinstance(value, datetime):
                            converted[key] = value.isoformat()
                        elif isinstance(value, dict):
                            converted[key] = convert_doc_for_json(value)
                        elif isinstance(value, list):
                            converted[key] = [convert_doc_for_json(item) if isinstance(item, dict) else item for item in value]
                        else:
                            converted[key] = value
                    return converted
                return doc
            
            # Convertir todos los documentos
            documents = [convert_doc_for_json(doc) for doc in documents]
            
            # Guardar backup
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "backup_info": {
                        "collection_name": collection_name,
                        "database_name": self.database_name,
                        "backup_date": datetime.now().isoformat(),
                        "total_documents": len(documents)
                    },
                    "documents": documents
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Backup completed: {backup_path}")
            logger.info(f"📊 Total documents backed up: {len(documents)}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            raise
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de una colección
        """
        collection = self.db[collection_name]
        
        stats = {
            "total_documents": collection.count_documents({}),
            "collection_name": collection_name,
            "database_name": self.database_name
        }
        
        # Obtener muestras de diferentes tipos de estructura
        sample_docs = list(collection.find().limit(3))
        if sample_docs:
            stats["sample_structures"] = []
            for i, doc in enumerate(sample_docs):
                stats["sample_structures"].append({
                    "document_id": str(doc.get('_id', f'doc_{i}')),
                    "fields": list(doc.keys()),
                    "field_count": len(doc.keys())
                })
        
        return stats
    
    def clear_collection(self, collection_name: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Limpiar completamente una colección
        """
        if not confirm:
            logger.warning("⚠️ Collection clear cancelled - confirmation required")
            return {"deleted": 0, "status": "cancelled"}
        
        try:
            collection = self.db[collection_name]
            
            # Contar documentos antes de eliminar
            count_before = collection.count_documents({})
            
            # Eliminar todos los documentos
            result = collection.delete_many({})
            
            logger.info(f"🗑️ Cleared collection '{collection_name}'")
            logger.info(f"📊 Documents deleted: {result.deleted_count}")
            
            return {
                "deleted": result.deleted_count,
                "status": "success",
                "count_before": count_before
            }
            
        except Exception as e:
            logger.error(f"❌ Clear collection failed: {e}")
            raise
    
    def backup_and_clear(self, collection_name: str, confirm_clear: bool = False) -> Dict[str, Any]:
        """
        Hacer backup y luego limpiar la colección
        """
        results = {}
        
        # 1. Hacer backup
        logger.info("🔄 Step 1: Creating backup...")
        backup_path = self.backup_collection(collection_name)
        results["backup_path"] = backup_path
        
        # 2. Obtener estadísticas antes del borrado
        stats = self.get_collection_stats(collection_name)
        results["stats_before"] = stats
        
        # 3. Limpiar colección si se confirma
        if confirm_clear:
            logger.info("🔄 Step 2: Clearing collection...")
            clear_result = self.clear_collection(collection_name, confirm=True)
            results["clear_result"] = clear_result
        else:
            logger.info("⏸️ Skipping collection clear - confirmation not provided")
            results["clear_result"] = {"status": "skipped"}
        
        return results
    
    def close(self):
        """Cerrar conexión"""
        if self.client:
            self.client.close()
            logger.info("🔌 MongoDB connection closed")

def main():
    """
    Función principal
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='MongoDB Backup and Clear Tool')
    parser.add_argument('--collection', '-c', type=str, default='products', 
                       help='Collection name to backup/clear')
    parser.add_argument('--backup-only', action='store_true', 
                       help='Only create backup, do not clear')
    parser.add_argument('--confirm-clear', action='store_true', 
                       help='Confirm that you want to clear the collection')
    parser.add_argument('--stats-only', action='store_true',
                       help='Only show collection statistics')
    
    args = parser.parse_args()
    
    try:
        manager = MongoBackupManager()
        
        if args.stats_only:
            # Solo mostrar estadísticas
            stats = manager.get_collection_stats(args.collection)
            print(f"\n📊 Collection Statistics:")
            print(f"   Database: {stats['database_name']}")
            print(f"   Collection: {stats['collection_name']}")
            print(f"   Total Documents: {stats['total_documents']}")
            
            if 'sample_structures' in stats:
                print(f"\n🔍 Sample Document Structures:")
                for i, sample in enumerate(stats['sample_structures'], 1):
                    print(f"   Document {i} ({sample['document_id']}):")
                    print(f"     Fields ({sample['field_count']}): {', '.join(sample['fields'][:10])}{'...' if sample['field_count'] > 10 else ''}")
        
        elif args.backup_only:
            # Solo hacer backup
            backup_path = manager.backup_collection(args.collection)
            print(f"\n✅ Backup completed: {backup_path}")
        
        else:
            # Backup y limpiar
            if not args.confirm_clear:
                print("⚠️ WARNING: This will DELETE ALL data in the collection!")
                print("Use --confirm-clear flag to proceed with deletion")
                print("Use --backup-only to create backup without deletion")
                return
            
            results = manager.backup_and_clear(args.collection, args.confirm_clear)
            
            print(f"\n🎉 Process completed:")
            print(f"   Backup: {results['backup_path']}")
            print(f"   Documents backed up: {results['stats_before']['total_documents']}")
            if results['clear_result']['status'] == 'success':
                print(f"   Documents deleted: {results['clear_result']['deleted']}")
            else:
                print(f"   Clear status: {results['clear_result']['status']}")
    
    except Exception as e:
        logger.error(f"❌ Process failed: {e}")
    
    finally:
        manager.close()

if __name__ == "__main__":
    main()
