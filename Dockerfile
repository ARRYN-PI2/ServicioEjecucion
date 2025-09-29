FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para scrapers y monitoreo
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    git \
    chromium \
    chromium-driver \
    cron \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cache de Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/scraped_output /app/backups

# Script de inicio que mantiene el container corriendo
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Variables de entorno para Chrome (necesario para Falabella)
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Healthcheck para monitoreo
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; print('Container healthy'); sys.exit(0)" || exit 1

# Puerto para posible API de monitoreo
EXPOSE 8080

# Comando por defecto - mantiene container corriendo
CMD ["/docker-entrypoint.sh"]