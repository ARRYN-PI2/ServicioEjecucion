# Test Cases - Product Uploader MongoDB

## Descripción General
Test cases teóricos para validar la funcionalidad del sistema de carga de productos a MongoDB Atlas, incluyendo validación de datos, conexión a base de datos, manejo de errores y integridad de datos.

---

## TC001 - Conexión a MongoDB Atlas

### Objetivo
Verificar que el sistema establece correctamente la conexión con MongoDB Atlas usando las credenciales proporcionadas.

### Precondiciones
- Variables de entorno configuradas correctamente en `.env`
- MongoDB Atlas cluster activo y accesible
- Credenciales válidas

### Datos de Entrada
```env
MONGODB_CONNECTION_STRING=mongodb+srv://username:<db_password>@cluster.mongodb.net/
MONGODB_PASSWORD=valid_password
DATABASE_NAME=smartcompare_ai
COLLECTION_NAME=products
```

### Pasos
1. Inicializar `MongoDBManager` con las credenciales
2. Ejecutar método `connect()`
3. Verificar comando `ping` a la base de datos

### Resultado Esperado
- ✅ Conexión exitosa establecida
- ✅ Log: "Connected to MongoDB Atlas"
- ✅ Cliente MongoDB inicializado correctamente

### Resultado en Caso de Fallo
- ❌ `ConnectionFailure` exception lanzada
- ❌ Log: "MongoDB connection failed"

---

## TC002 - Validación de Credenciales Inválidas

### Objetivo
Verificar el manejo de errores cuando las credenciales de MongoDB son incorrectas.

### Precondiciones
- Credenciales inválidas configuradas

### Datos de Entrada
```env
MONGODB_PASSWORD=invalid_password
```

### Pasos
1. Intentar conexión con credenciales inválidas
2. Verificar manejo de excepción

### Resultado Esperado
- ❌ `ConnectionFailure` exception capturada
- ✅ Error loggeado apropiadamente
- ✅ Aplicación no se cuelga

---

## TC003 - Carga de Producto Individual Válido

### Objetivo
Verificar la carga exitosa de un producto individual con todos los campos válidos.

### Precondiciones
- Conexión a MongoDB establecida
- Archivo JSON válido disponible

### Datos de Entrada
```json
{
  "titulo": "iPhone 15 Pro",
  "marca": "Apple",
  "categoria": "Smartphones",
  "precio_texto": "COP 5,299,000",
  "precio_valor": 5299000,
  "moneda": "COP",
  "tamaño": "128GB",
  "calificacion": "4.5",
  "detalles_adicionales": "Titanio Natural",
  "fuente": "test_store",
  "imagen": "https://example.com/iphone15.jpg",
  "link": "https://example.com/product/123",
  "contador_extraccion": "001",
  "fecha_extraccion": "2025-09-07"
}
```

### Pasos
1. Cargar producto usando `upload_from_json()`
2. Verificar inserción en colección
3. Validar estructura del documento guardado

### Resultado Esperado
- ✅ Producto insertado con ID único: `test_store_001`
- ✅ Todos los campos mapeados correctamente
- ✅ `created_at` y `updated_at` generados automáticamente
- ✅ Log de éxito mostrado

---

## TC004 - Manejo de Producto Duplicado

### Objetivo
Verificar el comportamiento cuando se intenta insertar un producto que ya existe.

### Precondiciones
- Producto ya existe en la base de datos
- Mismo `fuente` y `contador_extraccion`

### Datos de Entrada
```json
{
  "titulo": "iPhone 15 Pro - Actualizado",
  "fuente": "test_store",
  "contador_extraccion": "001"
}
```

### Pasos
1. Intentar insertar producto con ID existente
2. Verificar operación de reemplazo (`replace_one`)

### Resultado Esperado
- ✅ Documento existente actualizado (no duplicado)
- ✅ `updated_at` actualizado
- ✅ Nuevo contenido reemplaza el anterior

---

## TC005 - Carga Masiva de Productos

### Objetivo
Verificar la carga exitosa de múltiples productos desde un archivo JSON.

### Precondiciones
- Archivo con múltiples productos válidos
- Conexión a MongoDB establecida

### Datos de Entrada
```json
[
  {"titulo": "Producto 1", "fuente": "store1", "contador_extraccion": "001"},
  {"titulo": "Producto 2", "fuente": "store1", "contador_extraccion": "002"},
  {"titulo": "Producto 3", "fuente": "store2", "contador_extraccion": "001"}
]
```

### Pasos
1. Ejecutar `upload_from_file('multiple_products.json')`
2. Verificar procesamiento de cada producto
3. Validar estadísticas finales

### Resultado Esperado
- ✅ Todos los productos procesados
- ✅ Estadísticas correctas: `{'successful': 3, 'failed': 0, 'total': 3}`
- ✅ IDs únicos generados para cada producto

---

## TC006 - Validación de Parsing de Precios

### Objetivo
Verificar la correcta conversión de texto de precios a valores numéricos.

### Datos de Prueba
| Entrada | Resultado Esperado |
|---------|-------------------|
| "COP 1,299,000" | 1299000.0 |
| "COP 999.999" | 999999.0 |
| "$50,000" | 50000.0 |
| "Precio no disponible" | 0.0 |
| "" | 0.0 |
| null | 0.0 |

### Pasos
1. Ejecutar `parse_price()` con cada entrada
2. Verificar resultado numérico

### Resultado Esperado
- ✅ Conversiones correctas según tabla
- ✅ Manejo robusto de valores inválidos

---

## TC007 - Validación de Parsing de Calificaciones

### Objetivo
Verificar la correcta conversión de calificaciones a valores float.

### Datos de Prueba
| Entrada | Resultado Esperado |
|---------|-------------------|
| "4.5" | 4.5 |
| "5" | 5.0 |
| "3.2" | 3.2 |
| "" | 0.0 |
| "N/A" | 0.0 |
| null | 0.0 |

### Pasos
1. Ejecutar `parse_rating()` con cada entrada
2. Verificar conversión a float

### Resultado Esperado
- ✅ Conversiones correctas según tabla
- ✅ Valores inválidos devuelven 0.0

---

## TC008 - Manejo de Archivo JSON Inválido

### Objetivo
Verificar el manejo de errores cuando el archivo JSON tiene formato incorrecto.

### Datos de Entrada
```json
{
  "titulo": "Producto"
  "marca": "Sin coma"  // JSON inválido
}
```

### Pasos
1. Intentar cargar archivo con JSON malformado
2. Verificar captura de excepción

### Resultado Esperado
- ❌ `JSONDecodeError` capturada
- ✅ Error loggeado apropiadamente
- ✅ Proceso continúa sin crash

---

## TC009 - Archivo No Encontrado

### Objetivo
Verificar el manejo cuando el archivo especificado no existe.

### Datos de Entrada
- Ruta: `"archivo_inexistente.json"`

### Pasos
1. Intentar cargar archivo inexistente
2. Verificar manejo de excepción

### Resultado Esperado
- ❌ `FileNotFoundError` capturada
- ✅ Mensaje de error claro al usuario
- ✅ Aplicación no termina abruptamente

---

## TC010 - Backup Automático

### Objetivo
Verificar que se crea backup automático antes de operaciones masivas.

### Precondiciones
- Datos existentes en la colección
- Permisos de escritura en directorio `/backups`

### Pasos
1. Ejecutar carga masiva
2. Verificar creación de archivo backup
3. Validar contenido del backup

### Resultado Esperado
- ✅ Archivo backup creado en `/backups`
- ✅ Formato: `products_backup_YYYYMMDD_HHMMSS.json`
- ✅ Contenido completo de la colección respaldado

---

## TC011 - Uso desde Línea de Comandos

### Objetivo
Verificar funcionamiento correcto de la interfaz CLI.

### Datos de Entrada
```bash
python product_uploader.py --file products.json
```

### Pasos
1. Ejecutar comando desde terminal
2. Verificar procesamiento de argumentos
3. Validar salida del programa

### Resultado Esperado
- ✅ Argumentos parseados correctamente
- ✅ Archivo procesado exitosamente
- ✅ Estadísticas mostradas en terminal

---

## TC012 - Uso como Módulo Python

### Objetivo
Verificar integración como módulo importable.

### Datos de Entrada
```python
from product_uploader import ProductUploader
uploader = ProductUploader()
stats = uploader.upload_from_file('test.json')
```

### Pasos
1. Importar módulo
2. Crear instancia
3. Ejecutar método
4. Verificar retorno

### Resultado Esperado
- ✅ Importación exitosa
- ✅ Instancia creada correctamente
- ✅ Estadísticas retornadas como diccionario

---

## TC013 - Variables de Entorno Faltantes

### Objetivo
Verificar manejo cuando variables de entorno requeridas no están configuradas.

### Precondiciones
- Archivo `.env` sin variables requeridas

### Pasos
1. Eliminar variables críticas del `.env`
2. Intentar inicializar aplicación
3. Verificar manejo de error

### Resultado Esperado
- ❌ Error claro indicando variables faltantes
- ✅ Mensaje instructivo para el usuario
- ✅ Aplicación termina limpiamente

---

## TC014 - Límites de Datos

### Objetivo
Verificar manejo de archivos muy grandes y límites de memoria.

### Datos de Entrada
- Archivo JSON con 10,000+ productos

### Pasos
1. Cargar archivo grande
2. Monitorear uso de memoria
3. Verificar tiempo de procesamiento

### Resultado Esperado
- ✅ Procesamiento completado sin crash
- ✅ Memoria controlada (no memory leaks)
- ✅ Progreso reportado adecuadamente

---

## TC015 - Integridad de Datos Post-Inserción

### Objetivo
Verificar que los datos guardados mantienen integridad y formato correcto.

### Pasos
1. Insertar producto de prueba
2. Recuperar desde MongoDB
3. Comparar datos originales vs guardados

### Resultado Esperado
- ✅ Todos los campos preservados
- ✅ Tipos de datos correctos
- ✅ Timestamps automáticos presentes
- ✅ ID único generado correctamente

---

## Métricas de Éxito

### Cobertura de Pruebas
- ✅ Conexión a BD: 100%
- ✅ Operaciones CRUD: 100%
- ✅ Manejo de errores: 100%
- ✅ Validación de datos: 100%
- ✅ Interfaces (CLI/módulo): 100%

### Criterios de Aceptación
- Todos los test cases pasan exitosamente
- No hay memory leaks en operaciones masivas
- Tiempo de respuesta < 2 segundos para productos individuales
- Backup automático funciona en 100% de casos
- Manejo robusto de errores sin crashes

---

## Herramientas de Testing Recomendadas

### Para Implementación
- **pytest**: Framework de testing principal
- **pymongo-inmemory**: MongoDB en memoria para tests
- **unittest.mock**: Mocking de conexiones
- **coverage.py**: Medición de cobertura de código

### Para Datos de Prueba
- **factory_boy**: Generación de datos de prueba
- **faker**: Datos sintéticos realistas

### Ejemplo de Implementación
```python
import pytest
from unittest.mock import patch, MagicMock
from product_uploader import ProductUploader, MongoDBManager

class TestProductUploader:
    
    @patch('product_uploader.MongoClient')
    def test_connection_success(self, mock_client):
        # TC001 - Conexión exitosa
        mock_client.return_value.admin.command.return_value = True
        manager = MongoDBManager("connection_string", "password")
        assert manager.client is not None
    
    def test_price_parsing(self):
        # TC006 - Parsing de precios
        manager = MongoDBManager("test", "test")
        assert manager.parse_price("COP 1,299,000") == 1299000.0
        assert manager.parse_price("") == 0.0
```

---

Este documento proporciona una base sólida para validar todas las funcionalidades críticas del sistema de carga de productos, asegurando robustez, confiabilidad y mantenibilidad del código.
