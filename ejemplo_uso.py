"""
Ejemplo de uso del ProductUploader
"""

from product_uploader import ProductUploader
import json

def ejemplo_basico():
    """Ejemplo básico de uso"""
    print("🚀 Iniciando ejemplo de ProductUploader...")
    
    # Crear instancia del uploader
    uploader = ProductUploader()
    
    try:
        # Ejemplo 1: Subir desde archivo
        print("\n📂 Subiendo desde archivo...")
        stats = uploader.upload_from_file('sample_product.json')
        print(f"Resultados: {stats}")
        
        # Ejemplo 2: Subir desde string JSON
        print("\n📝 Subiendo desde string JSON...")
        producto_json = {
            "contador_extraccion_total": 15,
            "contador_extraccion": 15,
            "titulo": "Samsung Galaxy TV 55\" QLED 4K Smart TV",
            "marca": "SAMSUNG",
            "precio_texto": "COP 2,599,000",
            "precio_valor": 2599000,
            "moneda": "COP",
            "tamaño": "55\"",
            "calificacion": "4.8",
            "detalles_adicionales": "Smart TV con Tizen OS",
            "fuente": "ejemplo.com",
            "categoria": "televisores",
            "imagen": "https://ejemplo.com/imagen.jpg",
            "link": "https://ejemplo.com/producto",
            "pagina": 1,
            "fecha_extraccion": "2025-09-05T10:00:00",
            "extraction_status": "OK"
        }
        
        stats = uploader.upload_from_json_string(json.dumps(producto_json))
        print(f"Resultados: {stats}")
        
        print("\n✅ Ejemplo completado exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en el ejemplo: {e}")
    
    finally:
        # Cerrar conexiones
        uploader.close()

def ejemplo_multiples_productos():
    """Ejemplo con múltiples productos"""
    print("🚀 Iniciando ejemplo con múltiples productos...")
    
    productos = [
        {
            "contador_extraccion_total": 20,
            "contador_extraccion": 20,
            "titulo": "LG OLED 65\" 4K Smart TV",
            "marca": "LG",
            "precio_texto": "COP 3,499,000",
            "precio_valor": 3499000,
            "moneda": "COP",
            "tamaño": "65\"",
            "calificacion": "4.9",
            "detalles_adicionales": "OLED Technology",
            "fuente": "test.com",
            "categoria": "televisores",
            "imagen": "https://test.com/lg.jpg",
            "link": "https://test.com/lg-oled",
            "pagina": 1,
            "fecha_extraccion": "2025-09-05T11:00:00",
            "extraction_status": "OK"
        },
        {
            "contador_extraccion_total": 21,
            "contador_extraccion": 21,
            "titulo": "Sony Bravia 75\" 4K HDR Smart TV",
            "marca": "SONY",
            "precio_texto": "COP 4,299,000",
            "precio_valor": 4299000,
            "moneda": "COP",
            "tamaño": "75\"",
            "calificacion": "4.7",
            "detalles_adicionales": "HDR Technology",
            "fuente": "test.com",
            "categoria": "televisores",
            "imagen": "https://test.com/sony.jpg",
            "link": "https://test.com/sony-bravia",
            "pagina": 1,
            "fecha_extraccion": "2025-09-05T11:15:00",
            "extraction_status": "OK"
        }
    ]
    
    uploader = ProductUploader()
    
    try:
        # Convertir lista a JSON string
        productos_json = json.dumps(productos)
        stats = uploader.upload_from_json_string(productos_json)
        
        print(f"📊 Productos procesados: {len(productos)}")
        print(f"📈 Resultados: {stats}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        uploader.close()

if __name__ == "__main__":
    # Ejecutar ejemplos
    ejemplo_basico()
    print("\n" + "="*50 + "\n")
    ejemplo_multiples_productos()
