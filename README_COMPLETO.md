# ServicioEjecucion - Sistema de Gestión de Productos MongoDB

## 📋 Descripción General

Este repositorio contiene un **sistema completo de gestión de productos para MongoDB** especializado en datos de televisores extraídos de sitios de e-commerce. El sistema permite cargar, respaldar y gestionar productos de manera eficiente en MongoDB Atlas.

## 🏗️ Arquitectura del Sistema

El proyecto está compuesto por los siguientes componentes principales:

### 1. **ProductUploader** (`product_uploader.py`)
Sistema de carga masiva de productos desde archivos JSON a MongoDB.

**Características:**
- ✅ Conexión segura a MongoDB Atlas
- ✅ Procesamiento en lotes optimizado
- ✅ Generación automática de IDs únicos
- ✅ Operaciones upsert (actualizar o insertar)
- ✅ Parsing automático de precios y calificaciones
- ✅ Logging detallado con métricas

### 2. **MongoBackupManager** (`mongo_backup.py`)
Herramienta para backup y limpieza de colecciones MongoDB.

**Características:**
- 🔄 Backup completo de colecciones
- 🗑️ Limpieza segura con confirmación
- 📊 Estadísticas detalladas de colecciones
- 🔄 Conversión automática de tipos MongoDB para JSON
- 📝 Operaciones combinadas backup + limpieza

## 📁 Estructura del Proyecto

```
ServicioEjecucion/
├── product_uploader.py      # Sistema principal de carga
├── mongo_backup.py          # Gestor de backups y limpieza
├── ejemplo_uso.py          # Ejemplos de implementación
├── products.json           # Datos principales (140+ productos)
├── multiple_products.json  # Archivo de ejemplo
├── requirements.txt        # Dependencias del proyecto
├── TEST_CASES.md          # Casos de prueba documentados
├── README.md              # Documentación básica
├── README_COMPLETO.md     # Esta documentación completa
├── backups/               # Respaldos automáticos
│   ├── products_backup_20250905_012650.json
│   ├── products_backup_20250905_012711.json
│   └── products_backup_20250905_012945.json
└── __pycache__/           # Cache de Python
```

## 🚀 Configuración e Instalación

### 1. **Instalar Dependencias**
```bash
pip install -r requirements.txt
```

### 2. **Configurar Variables de Entorno**
Crea un archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
```

Configura las siguientes variables:
```env
MONGODB_CONNECTION_STRING=mongodb+srv://username:<db_password>@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_PASSWORD=tu_password_aqui
DATABASE_NAME=smartcompare_ai
COLLECTION_NAME=products
```

## 💻 Uso del Sistema

### **ProductUploader - Carga de Productos**

#### Desde línea de comandos:
```bash
# Cargar desde archivo JSON
python product_uploader.py --file products.json

# Cargar desde string JSON
python product_uploader.py --json '{"titulo": "TV Test", "marca": "Samsung"}'

# Ver ayuda
python product_uploader.py --help
```

#### Como módulo Python:
```python
from product_uploader import ProductUploader

# Crear instancia
uploader = ProductUploader()

# Cargar desde archivo
stats = uploader.upload_from_file('products.json')
print(f"Productos procesados: {stats['total_processed']}")

# Cargar desde JSON string
json_data = '{"titulo": "TV Test", "marca": "Samsung"}'
stats = uploader.upload_from_json_string(json_data)

# Cerrar conexión
uploader.close()
```

### **MongoBackupManager - Gestión de Backups**

#### Desde línea de comandos:
```bash
# Solo backup
python mongo_backup.py --collection products --backup-only

# Backup y limpieza
python mongo_backup.py --collection products --confirm-clear

# Solo estadísticas
python mongo_backup.py --collection products --stats-only

# Ver ayuda
python mongo_backup.py --help
```

#### Como módulo Python:
```python
from mongo_backup import MongoBackupManager

# Crear instancia
manager = MongoBackupManager()

# Crear backup
backup_path = manager.backup_collection('products')

# Obtener estadísticas
stats = manager.get_collection_stats('products')
print(f"Total documentos: {stats['total_documents']}")

# Backup y limpieza
results = manager.backup_and_clear('products', confirm_clear=True)

# Cerrar conexión
manager.close()
```

## 📊 Estructura de Datos

### **Formato de Entrada (JSON)**
```json
{
  "contador_extraccion_total": 12,
  "contador_extraccion": 12,
  "titulo": "TV KALLEY 60\" Pulgadas 152.4 cm 60G300 4K UHD LED Smart TV Google",
  "marca": "KALLEY",
  "precio_texto": "COP 1,699,900",
  "precio_valor": 1699900,
  "moneda": "COP",
  "tamaño": "60\"",
  "calificacion": "4.9487",
  "detalles_adicionales": "",
  "fuente": "alkosto.com",
  "categoria": "televisores",
  "imagen": "https://www.alkosto.com/media/catalog/product/cache/...",
  "link": "https://www.alkosto.com/tv-kalley-60-pulgadas-152-4-cm-60g300-4k-uhd-led-smart-tv-google-1770968",
  "pagina": 1,
  "fecha_extraccion": "2025-09-04T20:55:50",
  "extraction_status": "OK"
}
```

### **Estructura en MongoDB**
```javascript
{
  "_id": "alkosto.com_12",
  "product_id": "alkosto.com_12",
  "contador_extraccion_total": 12,
  "contador_extraccion": 12,
  "name": "TV KALLEY 60\" Pulgadas 152.4 cm 60G300 4K UHD LED Smart TV Google",
  "brand": "KALLEY",
  "category": "televisores",
  "price_text": "COP 1,699,900",
  "price_value": 1699900,
  "currency": "COP",
  "size": "60\"",
  "rating": 4.9487,
  "additional_details": "",
  "source": "alkosto.com",
  "image_url": "https://www.alkosto.com/media/catalog/product/cache/...",
  "product_link": "https://www.alkosto.com/tv-kalley-60-pulgadas-152-4-cm-60g300-4k-uhd-led-smart-tv-google-1770968",
  "page": 1,
  "extraction_date": "2025-09-04T20:55:50",
  "extraction_status": "OK",
  "created_at": ISODate("2025-09-05T01:26:50.123Z"),
  "updated_at": ISODate("2025-09-05T01:26:50.123Z")
}
```

## 🔧 Funcionalidades Detalladas

### **ProductUploader**
- **Normalización de datos**: Convierte campos del formato de entrada al formato MongoDB
- **Validación**: Verifica estructura y tipos de datos
- **IDs únicos**: Genera `product_id` basado en fuente y contador
- **Parsing inteligente**: Extrae valores numéricos de precios y calificaciones
- **Upsert operations**: Actualiza productos existentes o inserta nuevos
- **Manejo de errores**: Logging detallado para debugging
- **Estadísticas**: Reportes de inserción, actualización y errores

### **MongoBackupManager**
- **Backups JSON**: Exportación completa de colecciones
- **Conversión de tipos**: Maneja ObjectId y datetime para JSON
- **Metadatos**: Incluye información del backup (fecha, colección, total)
- **Limpieza segura**: Requiere confirmación explícita
- **Estadísticas**: Información detallada de colecciones
- **Operaciones combinadas**: Backup + limpieza en un solo comando

## 📈 Casos de Uso

### **Flujo Típico de Trabajo**
1. **Extracción**: Los datos se extraen de sitios de e-commerce
2. **Almacenamiento**: Se guardan en archivos JSON
3. **Backup preventivo**: Se respalda la colección actual
4. **Carga**: Se suben los nuevos datos con ProductUploader
5. **Verificación**: Se revisan estadísticas y logs
6. **Backup post-carga**: Se crea nuevo backup con los datos actualizados

### **Mantenimiento de la Base de Datos**
```python
# Script de mantenimiento completo
from product_uploader import ProductUploader
from mongo_backup import MongoBackupManager

# 1. Backup preventivo
manager = MongoBackupManager()
backup_path = manager.backup_collection('products')
print(f"Backup creado: {backup_path}")

# 2. Cargar nuevos productos
uploader = ProductUploader()
stats = uploader.upload_from_file('nuevos_products.json')
print(f"Productos procesados: {stats}")

# 3. Verificar estado final
final_stats = manager.get_collection_stats('products')
print(f"Total productos en BD: {final_stats['total_documents']}")

# Cerrar conexiones
uploader.close()
manager.close()
```

## 📋 Dependencias

```txt
pymongo>=4.5.0
python-dotenv>=1.0.0
```

## 🧪 Testing

Los casos de prueba están documentados en `TEST_CASES.md` e incluyen:
- Pruebas de conexión MongoDB
- Validación de formatos JSON
- Pruebas de inserción y actualización
- Verificación de backups
- Manejo de errores

## 🔒 Seguridad

- ✅ Credenciales en variables de entorno
- ✅ Conexión TLS/SSL a MongoDB Atlas
- ✅ Validación de entrada de datos
- ✅ Confirmación requerida para operaciones destructivas

## 📝 Logs y Monitoreo

El sistema genera logs detallados con:
- Timestamps de operaciones
- Contadores de documentos procesados
- Errores específicos con contexto
- Estadísticas de rendimiento
- Estados de conexión

## 🚀 Proyecto SmartCompare AI

Este servicio es parte del ecosistema **SmartCompare AI**, un sistema de comparación de precios de productos electrónicos que:
- Extrae datos de múltiples sitios e-commerce
- Almacena y normaliza información de productos
- Proporciona APIs para consulta y comparación
- Genera insights sobre precios y tendencias

## 👥 Contribución

Para contribuir al proyecto:
1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto es parte del repositorio ARRYN-PI2/ServicioEjecucion.

---

**Desarrollado para el proyecto SmartCompare AI** 🛒📊
