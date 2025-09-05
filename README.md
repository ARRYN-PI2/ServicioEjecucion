# Product Uploader para MongoDB

Este script permite subir productos desde archivos JSON a una colección de MongoDB Atlas.

## Configuración

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno:**
   
   Copia el archivo `.env.example` a `.env` y configura tus credenciales:
   ```bash
   cp .env.example .env
   ```
   
   Edita el archivo `.env` con tus datos:
   ```
   MONGODB_CONNECTION_STRING=mongodb+srv://username:<db_password>@cluster.mongodb.net/?retryWrites=true&w=majority
   MONGODB_PASSWORD=tu_password_aqui
   DATABASE_NAME=smartcompare_ai
   COLLECTION_NAME=products
   ```

## Uso

### Desde línea de comandos

**Subir desde archivo JSON:**
```bash
python product_uploader.py --file products.json
```

**Subir desde string JSON:**
```bash
python product_uploader.py --json '{"titulo": "Producto Test", "marca": "Test", ...}'
```

### Como módulo de Python

```python
from product_uploader import ProductUploader

# Crear instancia del uploader
uploader = ProductUploader()

# Subir desde archivo
stats = uploader.upload_from_file('productos.json')

# Subir desde string JSON
json_data = '{"titulo": "TV Test", "marca": "Samsung", ...}'
stats = uploader.upload_from_json_string(json_data)

# Cerrar conexiones
uploader.close()
```

## Formato de datos

El script espera datos en el siguiente formato JSON:

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
  "imagen": "https://www.alkosto.com/...",
  "link": "https://www.alkosto.com/...",
  "pagina": 1,
  "fecha_extraccion": "2025-09-04T20:55:50",
  "extraction_status": "OK"
}
```

## Características

- ✅ Conexión segura a MongoDB Atlas
- ✅ Soporte para archivos JSON y strings JSON
- ✅ Procesamiento en lotes
- ✅ Logging detallado
- ✅ Manejo de errores
- ✅ Actualización de productos existentes (upsert)
- ✅ Generación automática de IDs únicos
- ✅ Estadísticas de inserción

## Estructura de la colección MongoDB

Los productos se almacenan con la siguiente estructura:

```javascript
{
  "_id": "alkosto.com_12",
  "product_id": "alkosto.com_12",
  "contador_extraccion_total": 12,
  "contador_extraccion": 12,
  "name": "TV KALLEY 60\" Pulgadas...",
  "brand": "KALLEY",
  "category": "televisores",
  "price_text": "COP 1,699,900",
  "price_value": 1699900,
  "currency": "COP",
  "size": "60\"",
  "rating": 4.9487,
  "additional_details": "",
  "source": "alkosto.com",
  "image_url": "https://...",
  "product_link": "https://...",
  "page": 1,
  "extraction_date": "2025-09-04T20:55:50",
  "extraction_status": "OK",
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```
