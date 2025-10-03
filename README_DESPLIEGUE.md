# README - Despliegue ServicioEjecucion

## ⚠️ **ADVERTENCIA DE SEGURIDAD**

**IMPORTANTE:** Este documento contiene plantillas y referencias a configuraciones sensibles. 
- **NUNCA** incluyas credenciales reales, IPs o contraseñas en la documentación
- **SIEMPRE** usa variables de entorno y secrets encriptados
- **VERIFICA** que los archivos .env estén en .gitignore
- **REEMPLAZA** los valores de ejemplo con tus credenciales reales solo en entornos seguros

## 🎯 **Información General del Despliegue**

Este documento contiene toda la información técnica para el despliegue, configuración y mantenimiento del sistema ServicioEjecucion en producción.

## 🏗️ **Arquitectura de Despliegue**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│  GitHub Actions │───▶│   AWS EC2       │
│  (Source Code)  │    │   (CI/CD)       │    │  (Production)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │ Docker Container│
                                               │   (Persistent)  │
                                               └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │  MongoDB Atlas  │
                                               │   (Database)    │
                                               └─────────────────┘
```

## 🖥️ **Especificaciones del Servidor**

### **AWS EC2 Instance**
```yaml
Tipo: t2.micro (o superior)
OS: Amazon Linux 2023
IP Pública: [CONFIGURADA_EN_SECRETS]
Usuario: ec2-user
Región: us-east-2 (Ohio)
Storage: 8GB EBS (mínimo)
Security Groups: 
  - SSH (22): IP específica del administrador
  - HTTP (8080): 0.0.0.0/0 (opcional, para monitoreo)
```

### **Recursos Mínimos Requeridos**
```yaml
CPU: 1 vCore
RAM: 1GB
Disk: 8GB
Network: 1 Mbps
Docker: >= 20.0
Docker Compose: >= 2.0
```

## 🐳 **Configuración Docker**

### **Container Specifications**
```dockerfile
Base Image: python:3.11-slim
Working Dir: /app
Exposed Ports: 8080
Restart Policy: unless-stopped
Health Check: Cada 30s
Memory Limit: 512MB (recomendado)
CPU Limit: 0.5 (recomendado)
```

### **Volúmenes Persistentes**
```yaml
Logs: ./logs -> /app/logs
Scraped Data: ./scraped_output -> /app/scraped_output
Backups: ./backups -> /app/backups
```

### **Variables de Entorno**
```env
MONGODB_CONNECTION_STRING=mongodb+srv://username:<password>@cluster.mongodb.net/
MONGODB_PASSWORD=[CONFIGURADO_EN_SECRETS]
DATABASE_NAME=smartcompare_ai
COLLECTION_NAME=products
PYTHONPATH=/app
PYTHONUNBUFFERED=1
DISPLAY=:99
CHROME_BIN=/usr/bin/chromium
CHROME_PATH=/usr/bin/chromium
```

## 🚀 **Sistema de Despliegue Automático**

### **GitHub Actions Workflows**

#### **1. Deploy Workflow** (`deploy.yml`)
```yaml
Trigger: 
  - Push a main/develop
  - Manual desde GitHub UI
Duración: ~3-4 minutos
Pasos:
  1. Checkout código
  2. Configurar SSH
  3. Sincronizar archivos con rsync
  4. Instalar docker-compose (si necesario)
  5. Construir y ejecutar container
  6. Health check
  7. Reporte de estado
```

#### **2. Monitor Workflow** (`monitor.yml`)
```yaml
Trigger: Cada 6 horas (cron: '0 */6 * * *')
Duración: ~1-2 minutos
Funciones:
  - Verificar estado del container
  - Reiniciar si está parado
  - Mostrar métricas de recursos
  - Limpiar archivos viejos
  - Reportar estado de salud
```

#### **3. Management Workflow** (`manage.yml`)
```yaml
Trigger: Manual con opciones
Acciones disponibles:
  - restart: Reiniciar container
  - stop: Detener container
  - logs: Ver logs recientes
  - status: Estado y métricas
  - backup: Crear backup MongoDB
  - run-scraper: Ejecutar scrapers
  - clean-logs: Limpiar archivos
```

### **Secrets Requeridos en GitHub**
```yaml
EC2_HOST: [IP_DE_LA_INSTANCIA_EC2]
EC2_USER: ec2-user
EC2_PRIVATE_KEY: |
  -----BEGIN PRIVATE KEY-----
  [Contenido completo del archivo .pem]
  -----END PRIVATE KEY-----
MONGODB_CONNECTION_STRING: mongodb+srv://username:<password>@cluster.mongodb.net/
MONGODB_PASSWORD: [PASSWORD_DE_MONGODB]
DATABASE_NAME: smartcompare_ai
COLLECTION_NAME: products
```

## 🔧 **Configuración del Servidor**

### **Preparación Inicial de EC2**
```bash
# Conectar a EC2
ssh -i arryn-backend-key.pem ec2-user@[EC2_IP_ADDRESS]

# Actualizar sistema
sudo yum update -y

# Instalar Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Instalar Git
sudo yum install -y git

# Crear directorio del proyecto
mkdir -p ~/arryn-scrapers
cd ~/arryn-scrapers
```

### **Estructura de Directorios en EC2**
```
/home/ec2-user/arryn-scrapers/
├── .env                    # Variables de entorno
├── docker-compose.yml      # Configuración Docker
├── Dockerfile             # Imagen del container
├── docker-entrypoint.sh   # Script de inicio
├── product_uploader.py    # Script principal
├── mongo_backup.py        # Gestor de backups
├── requirements.txt       # Dependencias Python
├── logs/                  # Logs del sistema
│   ├── container.log      # Log del container
│   └── status.json        # Estado de salud
├── scraped_output/        # Datos extraídos
└── backups/              # Backups MongoDB
```

## 📊 **Monitoreo y Logging**

### **Logs del Sistema**
```yaml
Container Logs: docker-compose logs -f servicioejeucion
Sistema: /var/log/messages
Docker: journalctl -u docker
GitHub Actions: Disponibles en repo/Actions
```

### **Health Checks**
```yaml
Docker Health: docker ps (STATUS: healthy)
Container Response: docker-compose exec servicioejeucion python -c "print('OK')"
MongoDB Connection: Verificado en docker-entrypoint.sh
Status File: /app/logs/status.json (cada 5 min)
```

### **Métricas Monitoreadas**
```yaml
CPU Usage: docker stats
Memory Usage: docker stats
Disk Usage: df -h
Container Uptime: docker ps
MongoDB Connection: Health check interno
Log Files Count: ls logs/ | wc -l
Scraped Files: ls scraped_output/ | wc -l
Backup Files: ls backups/ | wc -l
```

## 🔄 **Procesos de Mantenimiento**

### **Limpieza Automática**
```yaml
Logs: Archivos >7 días eliminados automáticamente
Scraped Data: Archivos >30 días eliminados automáticamente
Docker Images: Eliminadas al hacer rebuild
Ejecutado: Cada 6 horas por monitor.yml
```

### **Backup Automático**
```yaml
MongoDB Backups: Disponibles desde GitHub Actions
Frecuencia: Manual o programable
Ubicación: /app/backups/
Formato: JSON con timestamp
Retención: Manual (sin límite automático)
```

### **Reinicio del Container**
```yaml
Automático: Si healthcheck falla
Manual: Desde GitHub Actions
Comando: docker-compose restart
Tiempo típico: 30-45 segundos
```

## 🚨 **Troubleshooting**

### **Container No Responde**
```bash
# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs --tail=100

# Reiniciar
docker-compose restart

# Rebuild completo
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **Problemas de Conexión SSH**
```bash
# Verificar permisos de la key
chmod 600 arryn-backend-key.pem

# Probar conexión
ssh -i arryn-backend-key.pem ec2-user@[EC2_IP_ADDRESS]

# Verificar security groups
# Debe permitir SSH (22) desde tu IP
```

### **Problemas de MongoDB**
```bash
# Verificar conexión dentro del container
docker-compose exec servicioejeucion python -c "
from product_uploader import ProductUploader
uploader = ProductUploader()
uploader.close()
print('OK')
"

# Verificar variables de entorno
docker-compose exec servicioejeucion env | grep MONGO
```

### **Espacio en Disco**
```bash
# Verificar espacio
df -h

# Limpiar Docker
docker system prune -f
docker volume prune -f

# Limpiar logs manualmente
find logs/ -name "*.log" -mtime +7 -delete
find scraped_output/ -name "*.json" -mtime +30 -delete
```

## 📞 **Comandos de Emergencia**

### **Parada Completa del Sistema**
```bash
ssh ec2-user@[EC2_IP_ADDRESS] 'cd ~/arryn-scrapers && docker-compose down'
```

### **Reinicio Completo**
```bash
ssh ec2-user@[EC2_IP_ADDRESS] 'cd ~/arryn-scrapers && docker-compose down && docker-compose up -d'
```

### **Ver Estado Rápido**
```bash
ssh ec2-user@[EC2_IP_ADDRESS] 'cd ~/arryn-scrapers && docker-compose ps && docker stats --no-stream'
```

### **Deploy Manual Forzado**
```bash
# Desde GitHub: Actions → Deploy to EC2 → Run workflow
# O desde local:
git push origin main --force
```

## 🔒 **Seguridad**

### **Accesos**
```yaml
SSH: Solo desde IPs específicas
Docker: Solo acceso local en EC2
MongoDB: Conexión TLS/SSL obligatoria
GitHub Secrets: Encriptados en GitHub
```

### **Credenciales**
```yaml
EC2 Key: arryn-backend-key.pem (600 permisos)
MongoDB: Credenciales en secrets de GitHub
GitHub: Token con permisos de Actions
```

### **Puertos Abiertos**
```yaml
22 (SSH): Solo para administración
8080 (HTTP): Opcional para monitoreo web
443 (HTTPS): Para MongoDB Atlas
```

## 📈 **Métricas de Performance**

### **Tiempos Típicos**
```yaml
Deploy completo: 3-4 minutos
Container start: 30-45 segundos
Health check: 15-30 segundos
Backup MongoDB: 1-2 minutos
Scraper execution: 5-15 minutos
```

### **Recursos Utilizados**
```yaml
RAM Base: ~200MB
RAM Scraping: ~400-600MB
CPU Idle: <5%
CPU Scraping: 20-50%
Disk Growth: ~10MB/día (logs)
Network: Mínimo
```

## 🎯 **Roadmap de Mejoras**

### **Próximas Implementaciones**
- [x] ✅ Docker persistente 24/7
- [x] ✅ GitHub Actions para deploy automático
- [x] ✅ Monitoreo automático cada 6 horas
- [x] ✅ Gestión remota desde GitHub
- [x] ✅ Health checks integrados
- [x] ✅ Limpieza automática de archivos
- [ ] Notificaciones Slack/Email en fallos
- [ ] Dashboard web de métricas
- [ ] Backup programado automático
- [ ] Load balancer para múltiples containers
- [ ] Monitoreo con Prometheus/Grafana
- [ ] Logs centralizados con ELK Stack
- [ ] Auto-scaling basado en carga

---

## 📋 **Información de Contacto**

**Proyecto:** ARRYN-PI2/ServicioEjecucion  
**Ambiente:** Producción AWS EC2  
**Última Actualización:** Septiembre 2025  
**Documentación Técnica:** README_COMPLETO.md  
**Estado del Sistema:** ✅ Completamente operativo con Docker persistente

## 🎯 **Estado Actual del Despliegue**

### **Sistema Implementado:**
```yaml
Arquitectura: Docker Persistente + GitHub Actions
Container: ✅ Corriendo 24/7 con healthcheck
Monitoring: ✅ Automático cada 6 horas
Deploy: ✅ Automático por push a main/develop
Management: ✅ Remoto desde GitHub Actions
```

### **Servicios Activos:**
```yaml
Container Principal: arryn-servicioejeucion
Estado: Up X minutes (healthy)
Puerto: 8080:8080 (monitoreo)
Volúmenes: logs/, scraped_output/, backups/
Auto-restart: unless-stopped
```

### **Workflows Operativos:**
- 🚀 **deploy.yml** - Deploy automático exitoso
- 📊 **monitor.yml** - Monitoreo cada 6 horas
- 🛠️ **manage.yml** - Gestión manual disponible

---

**¿Problemas con el despliegue?** El sistema está completamente operativo. Consulta la sección de Troubleshooting o revisa los logs en GitHub Actions.
