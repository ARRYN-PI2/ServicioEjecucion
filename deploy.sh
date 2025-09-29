#!/bin/bash

# Script de despliegue rápido para ServicioEjecucion en EC2
# Uso: ./deploy.sh

set -e

echo "🚀 Iniciando despliegue de ServicioEjecucion en EC2..."

# Variables
EC2_HOST="18.222.44.39"
EC2_USER="ec2-user"
SSH_KEY="../../arryn-backend-key.pem"
APP_DIR="~/arryn-scrapers"
CONTAINER_NAME="arryn-scrapers"

echo "📦 Step 1: Preparando archivos locales..."

# Crear .env template si no existe
if [ ! -f .env ]; then
    cat > .env << EOF
MONGODB_CONNECTION_STRING=mongodb+srv://arryn-scrapers:uDPwk9Df5VR0vy0R@arrynpi2.1cherui.mongodb.net/
DATABASE_NAME=smartcompare_ai
COLLECTION_NAME=products
EOF
    echo "✅ Archivo .env creado. Edita las credenciales antes de continuar."
fi

# Verificar que requirements.txt existe
if [ ! -f requirements.txt ]; then
    echo "⚠️  Creando requirements.txt básico..."
    cat > requirements.txt << EOF
requests>=2.28.0
beautifulsoup4>=4.11.0
selenium>=4.0.0
pymongo>=4.0.0
python-dotenv>=0.19.0
lxml>=4.9.0
pandas>=1.5.0
jsonlines>=3.0.0
EOF
fi

echo "🔄 Step 2: Sincronizando código con EC2..."

# Rsync código (excluyendo archivos innecesarios)
rsync -avz -e "ssh -i ${SSH_KEY}" \
           --exclude='.git' \
           --exclude='__pycache__' \
           --exclude='venv' \
           --exclude='*.pyc' \
           --exclude='.env' \
           . ${EC2_USER}@${EC2_HOST}:${APP_DIR}/

echo "🏗️  Step 3: Construyendo container en EC2..."

# Ejecutar comandos en EC2
ssh -i ${SSH_KEY} ${EC2_USER}@${EC2_HOST} << EOF
    cd ${APP_DIR}
    
    # Detener container existente si existe
    if docker ps -a | grep -q ${CONTAINER_NAME}; then
        echo "🛑 Deteniendo container existente..."
        docker stop ${CONTAINER_NAME} || true
        docker rm ${CONTAINER_NAME} || true
    fi
    
    # Actualizar submodules
    echo "📥 Actualizando submodules..."
    git submodule update --init --recursive
    
    # Construir nueva imagen
    echo "🔨 Construyendo imagen Docker..."
    docker build -t arryn-scrapers:latest .
    
    # Crear directorio para variables de entorno
    mkdir -p ${APP_DIR}/config
EOF

echo "⚙️  Step 4: Configurando variables de entorno..."

# Copiar .env a EC2 (usuario debe editarlo)
scp -i ${SSH_KEY} .env ${EC2_USER}@${EC2_HOST}:${APP_DIR}/.env

echo "🧪 Step 5: Testing container..."

# Test rápido del container
ssh -i ${SSH_KEY} ${EC2_USER}@${EC2_HOST} << EOF
    cd ${APP_DIR}
    
    # Test de que el container funciona
    echo "🔍 Testing container..."
    docker run --rm --env-file .env arryn-scrapers:latest python -c "
import sys
print('✅ Python import funcionando')
try:
    import requests, pymongo, selenium
    print('✅ Dependencias principales instaladas')
except ImportError as e:
    print(f'❌ Error importando dependencias: {e}')
    sys.exit(1)
print('🎉 Container listo!')
"
EOF

echo "🏁 Step 6: Creando scripts de ejecución..."

# Crear script para ejecutar scrapers
ssh -i ${SSH_KEY} ${EC2_USER}@${EC2_HOST} << EOF
cat > ${APP_DIR}/run_scrapers.sh << 'SCRIPT'
#!/bin/bash
# Script para ejecutar scrapers con Docker
cd ${APP_DIR}

SCRAPERS=\${1:-"alkosto"}
PAGINAS=\${2:-"1"}

echo "🚀 Ejecutando scrapers: \$SCRAPERS con \$PAGINAS páginas..."

docker run --rm \\
    --env-file .env \\
    -v \${PWD}/scraped_output:/app/scraped_output \\
    -v \${PWD}/logs:/app/logs \\
    arryn-scrapers:latest \\
    python scraper_orchestrator.py --scrapers \$SCRAPERS --paginas \$PAGINAS

echo "✅ Ejecución completada. Revisa /app/scraped_output para resultados"
SCRIPT

chmod +x ${APP_DIR}/run_scrapers.sh
EOF

echo ""
echo "🎉 ¡DESPLIEGUE COMPLETADO!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Edita las credenciales en EC2: ssh ${EC2_USER}@${EC2_HOST} nano ${APP_DIR}/.env"
echo "2. Ejecuta test: ssh ${EC2_USER}@${EC2_HOST} ${APP_DIR}/run_scrapers.sh alkosto 1"
echo "3. Ejecuta production: ssh ${EC2_USER}@${EC2_HOST} ${APP_DIR}/run_scrapers.sh \"alkosto exito falabella\" 3"
echo ""
echo "🔗 Comandos útiles:"
echo "- Ver logs: ssh ${EC2_USER}@${EC2_HOST} docker logs ${CONTAINER_NAME}"
echo "- Conectar a container: ssh ${EC2_USER}@${EC2_HOST} docker exec -it ${CONTAINER_NAME} bash"
echo "- Ver archivos output: ssh ${EC2_USER}@${EC2_HOST} ls -la ${APP_DIR}/scraped_output/"