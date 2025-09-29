# Dockerfile para ServicioEjecucion
FROM python:3.9-slim

# Instalar dependencias del sistema necesarias para scrapers
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    git \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements primero (para cache de Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Inicializar submodules
RUN git submodule update --init --recursive

# Crear directorios necesarios
RUN mkdir -p scraped_output backups

# Variables de entorno para Chrome (necesario para Falabella)
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_PATH=/usr/bin/chromium

# Exponer puerto (si necesario para logs/monitoreo)
EXPOSE 8000

# Comando por defecto - mostrar ayuda
CMD ["python", "-c", "print('ServicioEjecucion Docker Container Ready!\\nUse: docker run -e MONGODB_CONNECTION_STRING=your_string container_name python scraper_orchestrator.py --help')"]