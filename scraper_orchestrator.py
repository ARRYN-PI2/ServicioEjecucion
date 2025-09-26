import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ScraperOrchestrator:
    def __init__(self):
        self.scrapers_dir = Path('scrapers')
        self.output_dir = Path('scraped_output')
        self.output_dir.mkdir(exist_ok=True)
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Configurar logging para el orchestrator"""
        logger = logging.getLogger('ScraperOrchestrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
        
    def ejecutar_scraper(self, scraper_name: str, paginas: int = 2) -> Optional[str]:
        """
        Ejecuta un scraper específico con número de páginas configurado
        
        Args:
            scraper_name: 'alkosto', 'exito' (falabella pendiente)
            paginas: Número de páginas a scraper (default: 2 para lotes pequeños)
            
        Returns:
            Path del archivo JSON generado o None si hay error
        """
        # Mapeo de rutas reales de los scrapers
        scraper_paths = {
            'alkosto': self.scrapers_dir / 'alkosto' / 'alkosto_scraper',
            'exito': self.scrapers_dir / 'exito' / 'exito_scraper',
            # 'falabella': pendiente cuando esté listo con main.py
        }
        
        if scraper_name not in scraper_paths:
            self.logger.error(f"Scraper no soportado: {scraper_name}")
            return None
            
        scraper_path = scraper_paths[scraper_name]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{scraper_name}_products_{timestamp}.json"
        
        if not scraper_path.exists():
            self.logger.error(f"Scraper no encontrado: {scraper_path}")
            return None
            
        try:
            self.logger.info(f"Ejecutando {scraper_name} con {paginas} páginas")
            
            # Comando con ruta corregida - ejecutar desde directorio del scraper
            cmd = [
                'python', 'main.py',
                '--paginas', str(paginas),
                '--output', str(output_file)
            ]
            
            # Ejecutar con timeout para evitar procesos colgados
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=600,  # 10 minutos máximo por scraper
                cwd=str(scraper_path)  # Ejecutar desde la carpeta del scraper
            )
            
            if result.returncode == 0:
                self.logger.info(f"Scraper {scraper_name} completado exitosamente")
                return str(output_file)
            else:
                self.logger.error(f"Error en {scraper_name}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout en scraper {scraper_name} ({paginas} páginas)")
            return None
        except Exception as e:
            self.logger.error(f"Excepción en {scraper_name}: {e}")
            return None
    
    def ejecutar_pipeline_completo(self, 
                                 scrapers: List[str] = None, 
                                 paginas: int = 2) -> Dict[str, any]:
        """
        Ejecuta pipeline completo con todos los scrapers especificados
        
        Args:
            scrapers: Lista de scrapers ['alkosto', 'exito'] (falabella omitido temporalmente)
            paginas: Páginas por scraper (para control de lotes)
            
        Returns:
            Diccionario con estadísticas de ejecución
        """
        if scrapers is None:
            scrapers = ['alkosto', 'exito']  # Falabella omitido hasta que tenga main.py
            
        resultados = {
            'inicio': datetime.now().isoformat(),
            'scrapers_ejecutados': 0,
            'archivos_generados': [],
            'errores': [],
            'productos_procesados': 0
        }
        
        self.logger.info(f"=== INICIANDO PIPELINE - {len(scrapers)} scrapers, {paginas} páginas c/u ===")
        
        # Ejecutar cada scraper
        for scraper in scrapers:
            archivo_output = self.ejecutar_scraper(scraper, paginas)
            
            if archivo_output and Path(archivo_output).exists():
                resultados['scrapers_ejecutados'] += 1
                resultados['archivos_generados'].append(archivo_output)
                
                # Procesar con ProductUploader
                try:
                    from product_uploader import ProductUploader
                    uploader = ProductUploader()
                    stats = uploader.upload_from_file(archivo_output)
                    resultados['productos_procesados'] += stats.get('inserted', 0) + stats.get('updated', 0)
                    uploader.close()
                    
                except Exception as e:
                    error_msg = f"Error procesando {archivo_output}: {e}"
                    self.logger.error(error_msg)
                    resultados['errores'].append(error_msg)
            else:
                error_msg = f"Falló scraper {scraper}"
                resultados['errores'].append(error_msg)
        
        resultados['fin'] = datetime.now().isoformat()
        
        # Log de resumen
        self.logger.info(f"=== PIPELINE COMPLETADO ===")
        self.logger.info(f"Scrapers exitosos: {resultados['scrapers_ejecutados']}/{len(scrapers)}")
        self.logger.info(f"Productos procesados: {resultados['productos_procesados']}")
        self.logger.info(f"Errores: {len(resultados['errores'])}")
        
        return resultados

# CLI para uso manual
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrator de Scrapers ARRYN")
    parser.add_argument('--scrapers', nargs='+', 
                       choices=['alkosto', 'exito'],  # Falabella removido temporalmente
                       default=['alkosto', 'exito'],
                       help='Scrapers a ejecutar (alkosto, exito)')
    parser.add_argument('--paginas', type=int, default=2,
                       help='Número de páginas por scraper (default: 2)')
    
    args = parser.parse_args()
    
    orchestrator = ScraperOrchestrator()
    resultados = orchestrator.ejecutar_pipeline_completo(args.scrapers, args.paginas)
    
    print(json.dumps(resultados, indent=2, default=str))