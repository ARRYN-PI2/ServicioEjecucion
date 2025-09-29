#!/bin/bash

echo "🚀 Iniciando ServicioEjecucion Container..."

# Función para manejar señales
cleanup() {
    echo "📝 Guardando logs finales..."
    echo "🛑 Deteniendo ServicioEjecucion..."
    exit 0
}

# Configurar manejo de señales
trap cleanup SIGTERM SIGINT

# Crear logs de inicio
mkdir -p /app/logs
echo "$(date): Container iniciado" >> /app/logs/container.log

# Verificar conexión a MongoDB
python -c "
try:
    from product_uploader import ProductUploader
    uploader = ProductUploader()
    uploader.close()
    print('✅ MongoDB connection OK')
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
    # No salir con error, solo logear
" >> /app/logs/container.log 2>&1

echo "✅ Container ready y monitoreando..."
echo "$(date): Container ready" >> /app/logs/container.log

# Loop infinito para mantener container corriendo
while true; do
    # Log heartbeat cada 5 minutos
    echo "$(date): Container running - Heartbeat" >> /app/logs/container.log
    
    # Verificar salud del sistema cada 5 minutos
    python -c "
import os
import json
from datetime import datetime

try:
    # Crear status file para monitoreo externo
    status = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'uptime_seconds': float(open('/proc/uptime').read().split()[0]),
        'container_logs': len([f for f in os.listdir('/app/logs') if f.endswith('.log')]) if os.path.exists('/app/logs') else 0,
        'scraped_files': len([f for f in os.listdir('/app/scraped_output') if f.endswith('.json')]) if os.path.exists('/app/scraped_output') else 0,
        'backup_files': len([f for f in os.listdir('/app/backups') if f.endswith('.json')]) if os.path.exists('/app/backups') else 0
    }

    with open('/app/logs/status.json', 'w') as f:
        json.dump(status, f, indent=2)
except Exception as e:
    print(f'Error creating status: {e}')
" 2>/dev/null
    
    # Limpiar logs viejos (mantener solo últimos 7 días)
    find /app/logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    sleep 300  # Esperar 5 minutos
done
