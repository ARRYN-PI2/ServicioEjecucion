#!/usr/bin/env python3
"""
Orchestrator corregido para manejar imports relativos de scrapers
"""

import subprocess
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ScraperOrchestrator:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.scrapers_dir = self.base_dir / 'scrapers'
        self.output_dir = self.base_dir / 'scraped_output'
        self.logs_dir = self.base_dir / 'logs'
        
        # Crear directorios si no existen
        self.output_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.logger = self._setup_logging()
        
        # Mapeo específico de comandos por scraper
        self.scraper_commands = {
            'alkosto': {
                'method': 'module',
                'cwd': 'scrapers/alkosto',
                'command': ['python', '-m', 'alkosto_scraper.main', 'scrape'],
                'args_template': ['--categoria', 'televisores', '--paginas', '{paginas}']
            },
            'exito': {
                'method': 'module', 
                'cwd': 'scrapers/exito',
                'command': ['python', '-m', 'exito_scraper.main', 'scrape'],
                'args_template': ['--categoria', 'televisores', '--paginas', '{paginas}']
            },
            'falabella': {
                'method': 'script',
                'cwd': 'scrapers/falabella',
                'command': ['python', 'scrape_falabella_all.py'],
                'args_template': ['--category', 'televisores', '--pages', '{paginas}']
            }
        }
        
    def _setup_logging(self):
        """Configurar logging con archivo y consola"""
        logger = logging.getLogger('ScraperOrchestrator')
        logger.setLevel(logging.INFO)
        
        # Limpiar handlers existentes
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Handler para archivo
        log_file = self.logs_dir / f'orchestrator_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def ejecutar_scraper(self, scraper_name: str, paginas: int = 1) -> Dict:
        """
        Ejecuta un scraper específico con el método correcto
        
        Args:
            scraper_name: 'alkosto', 'exito', 'falabella'
            paginas: Número de páginas a scraper
            
        Returns:
            Dict con resultado de la ejecución
        """
        if scraper_name not in self.scraper_commands:
            error_msg = f"Scraper '{scraper_name}' no configurado. Disponibles: {list(self.scraper_commands.keys())}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg, "output_file": None}
            
        config = self.scraper_commands[scraper_name]
        scraper_dir = self.base_dir / config['cwd']
        
        if not scraper_dir.exists():
            error_msg = f"Directorio del scraper no encontrado: {scraper_dir}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg, "output_file": None}
            
        try:
            self.logger.info(f"Ejecutando {scraper_name} con {paginas} páginas...")
            
            # Construir comando completo
            cmd = config['command'].copy()
            
            # Agregar argumentos específicos del scraper
            for arg in config['args_template']:
                if '{paginas}' in arg:
                    cmd.append(arg.format(paginas=paginas))
                else:
                    cmd.append(arg)
            
            self.logger.info(f"Comando: {' '.join(cmd)}")
            self.logger.info(f"Directorio de trabajo: {scraper_dir}")
            
            # Ejecutar comando
            result = subprocess.run(
                cmd,
                cwd=scraper_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"✅ {scraper_name} ejecutado exitosamente")
                
                # Buscar archivo de salida generado
                output_file = self._find_output_file(scraper_dir, scraper_name)
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                error_msg = f"Error ejecutando {scraper_name}: {result.stderr}"
                self.logger.error(error_msg)
                self.logger.error(f"STDOUT: {result.stdout}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "output_file": None,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout ejecutando {scraper_name} (>10 min)"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg, "output_file": None}
            
        except Exception as e:
            error_msg = f"Excepción ejecutando {scraper_name}: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg, "output_file": None}
    
    def _find_output_file(self, scraper_dir: Path, scraper_name: str) -> Optional[str]:
        """Buscar archivo de salida más reciente del scraper"""
        possible_patterns = [
            f"productos*.json",
            f"products*.json", 
            f"{scraper_name}*.json",
            f"data/productos*.json",
            f"output/*.json"
        ]
        
        output_files = []
        for pattern in possible_patterns:
            files = list(scraper_dir.glob(pattern))
            output_files.extend(files)
        
        if output_files:
            # Retornar el más reciente
            latest_file = max(output_files, key=lambda f: f.stat().st_mtime)
            self.logger.info(f"Archivo de salida encontrado: {latest_file}")
            return str(latest_file)
        else:
            self.logger.warning(f"No se encontró archivo de salida para {scraper_name}")
            return None
    
    def ejecutar_multiple(self, scrapers: List[str], paginas: int = 1) -> Dict:
        """
        Ejecuta múltiples scrapers secuencialmente
        
        Args:
            scrapers: Lista de nombres de scrapers a ejecutar
            paginas: Páginas por scraper
            
        Returns:
            Resumen de ejecución
        """
        timestamp_inicio = datetime.now()
        self.logger.info(f"=== INICIANDO PIPELINE - {len(scrapers)} scrapers, {paginas} páginas c/u ===")
        
        resultados = {}
        archivos_generados = []
        errores = []
        productos_totales = 0
        
        for scraper in scrapers:
            self.logger.info(f"Ejecutando {scraper} con {paginas} páginas")
            
            resultado = self.ejecutar_scraper(scraper, paginas)
            resultados[scraper] = resultado
            
            if resultado["success"]:
                if resultado["output_file"]:
                    archivos_generados.append(resultado["output_file"])
                    
                    # Contar productos en el archivo
                    try:
                        productos_count = self._count_products(resultado["output_file"])
                        productos_totales += productos_count
                        self.logger.info(f"✅ {scraper}: {productos_count} productos extraídos")
                    except Exception as e:
                        self.logger.warning(f"No se pudo contar productos de {scraper}: {e}")
                else:
                    self.logger.warning(f"⚠️ {scraper}: ejecutado pero sin archivo de salida")
            else:
                errores.append(f"Falló scraper {scraper}")
                self.logger.error(f"❌ {scraper}: {resultado['error']}")
        
        timestamp_fin = datetime.now()
        duracion = (timestamp_fin - timestamp_inicio).total_seconds()
        
        # Resumen final
        scrapers_exitosos = sum(1 for r in resultados.values() if r["success"])
        
        self.logger.info(f"=== PIPELINE COMPLETADO ===")
        self.logger.info(f"Scrapers exitosos: {scrapers_exitosos}/{len(scrapers)}")
        self.logger.info(f"Productos procesados: {productos_totales}")
        self.logger.info(f"Errores: {len(errores)}")
        
        resumen = {
            "inicio": timestamp_inicio.isoformat(),
            "scrapers_ejecutados": scrapers_exitosos,
            "archivos_generados": archivos_generados,
            "errores": errores,
            "productos_procesados": productos_totales,
            "fin": timestamp_fin.isoformat()
        }
        
        # Guardar resumen
        resumen_file = self.output_dir / f"ejecucion_{timestamp_inicio.strftime('%Y%m%d_%H%M%S')}.json"
        with open(resumen_file, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, indent=2, ensure_ascii=False)
        
        print(json.dumps(resumen, indent=2, ensure_ascii=False))
        return resumen
        
    def _count_products(self, file_path: str) -> int:
        """Contar productos en archivo JSON/JSONL"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                if not content:
                    return 0
                    
                # Detectar formato
                if content.startswith('['):
                    # JSON array
                    data = json.loads(content)
                    return len(data) if isinstance(data, list) else 1
                else:
                    # JSONL - contar líneas
                    return len([line for line in content.split('\n') if line.strip()])
                    
        except Exception as e:
            self.logger.warning(f"Error contando productos en {file_path}: {e}")
            return 0

def main():
    """Función principal para ejecución desde CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Orchestrator de Scrapers ARRYN')
    parser.add_argument('--scrapers', 
                       default='alkosto',
                       help='Scrapers a ejecutar (separados por coma). Ej: alkosto,exito,falabella')
    parser.add_argument('--paginas', 
                       type=int, 
                       default=1,
                       help='Número de páginas por scraper (default: 1)')
    
    args = parser.parse_args()
    
    # Parsear lista de scrapers
    scrapers_list = [s.strip() for s in args.scrapers.split(',')]
    
    # Ejecutar orchestrator
    orchestrator = ScraperOrchestrator()
    resultado = orchestrator.ejecutar_multiple(scrapers_list, args.paginas)
    
    # Exit code basado en éxito
    exit_code = 0 if resultado["scrapers_ejecutados"] > 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()