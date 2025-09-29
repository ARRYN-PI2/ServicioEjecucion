# Guía de Despliegue Docker Persistente

## 🎯 **Nuevo Sistema de Despliegue**

El sistema ahora utiliza **Docker persistente** + **GitHub Actions** en lugar de scripts bash para un mejor control y monitoreo.

## 🔑 **Configuración de Secrets en GitHub**

Ve a tu repositorio → Settings → Secrets and variables → Actions, y configura:

```
EC2_HOST=18.222.44.39
EC2_USER=ec2-user
EC2_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
[contenido completo del archivo arryn-backend-key.pem]
-----END PRIVATE KEY-----
```

## 🚀 **Despliegue Automático**

### **Deploy desde GitHub Actions:**
1. Ve a tu repositorio → Actions
2. Selecciona "Deploy to EC2"
3. Haz clic en "Run workflow"
4. Selecciona el environment (staging/production)

### **Deploy desde push:**
- Push a `main` → deploy automático a production
- Push a `develop` → deploy automático a staging

## 🐳 **Container Persistente**

El container ahora:
- ✅ **Se mantiene corriendo 24/7**
- ✅ **Se reinicia automáticamente** si se detiene
- ✅ **Genera logs de monitoreo** cada 5 minutos
- ✅ **Limpia archivos viejos** automáticamente
- ✅ **Healthcheck integrado**

## 📊 **Monitoreo**

### **Automático:**
- GitHub Action cada 6 horas verifica salud
- Container genera `logs/status.json` con métricas
- Logs rotativos (mantiene últimos 7 días)

### **Manual:**
```bash
# Ver estado del container
ssh ec2-user@18.222.44.39 'cd ~/arryn-scrapers && docker-compose ps'

# Ver logs en tiempo real
ssh ec2-user@18.222.44.39 'cd ~/arryn-scrapers && docker-compose logs -f'

# Ver métricas de salud
ssh ec2-user@18.222.44.39 'cd ~/arryn-scrapers && cat logs/status.json'
```

## 🛠️ **Gestión desde GitHub Actions**

Ve a Actions → "Container Management" para:
- 🔄 **restart**: Reiniciar container
- 🛑 **stop**: Detener container
- 📝 **logs**: Ver logs recientes
- 📊 **status**: Ver estado y métricas
- 💾 **backup**: Crear backup MongoDB
- 🕷️ **run-scraper**: Ejecutar uploader
- 🧹 **clean-logs**: Limpiar archivos viejos

## 🔧 **Comandos Directos en EC2**

```bash
# Conectar a EC2
ssh -i ../../arryn-backend-key.pem ec2-user@18.222.44.39

# Ir al directorio del proyecto
cd ~/arryn-scrapers

# Ver estado del container
docker-compose ps

# Ver logs del container
docker-compose logs -f servicioejeucion

# Ejecutar comandos dentro del container
docker-compose exec servicioejeucion python product_uploader.py --file products.json

# Crear backup
docker-compose exec servicioejeucion python mongo_backup.py --backup-only --collection products

# Ver archivos generados
ls -la scraped_output/
ls -la backups/
ls -la logs/
```

## 🆚 **Cambios vs Sistema Anterior**

| Anterior (bash) | Nuevo (Docker + GitHub Actions) |
|----------------|-----------------------------------|
| ❌ Container temporal | ✅ Container persistente 24/7 |
| ❌ Deploy manual | ✅ Deploy automático por push |
| ❌ Sin monitoreo | ✅ Monitoreo automático cada 6h |
| ❌ Sin healthcheck | ✅ Healthcheck integrado |
| ❌ Scripts locales | ✅ GitHub Actions remotas |
| ❌ Sin logging | ✅ Logs estructurados + rotación |

## 🔄 **Flujo de Trabajo Recomendado**

1. **Desarrollo**: Haz cambios en rama `develop`
2. **Deploy a staging**: Push a `develop` → deploy automático
3. **Pruebas**: Usa GitHub Actions para ejecutar scrapers
4. **Producción**: Merge a `main` → deploy automático
5. **Monitoreo**: Revisa Actions cada 6 horas o manual

## 🚨 **Troubleshooting**

### Si el container no está corriendo:
```bash
ssh ec2-user@18.222.44.39 'cd ~/arryn-scrapers && docker-compose up -d'
```

### Si GitHub Actions falla:
1. Verifica que los secrets están configurados
2. Revisa que la EC2 esté accesible
3. Verifica permisos del archivo .pem

### Si hay problemas de memoria/disco:
```bash
# Limpiar imágenes viejas
docker image prune -f

# Limpiar containers parados
docker container prune -f

# Ver uso de disco
df -h
```

## 📈 **Próximas Mejoras**

- [ ] Notificaciones Slack/Email en fallos
- [ ] Dashboard web de monitoreo
- [ ] Backup automático programado
- [ ] Scaling automático
- [ ] Métricas en tiempo real

---

**¡El sistema ahora es completamente autónomo y monitoreado! 🎉**
