# -------- Base --------
FROM python:3.10-slim

# Evita prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# -------- Dependências do sistema --------
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# -------- Variáveis GDAL (IMPORTANTE) --------
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# -------- Diretório de trabalho --------
WORKDIR /app

# -------- Copiar requirements --------
COPY requirements.txt .

# -------- Instalar Python deps --------
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -------- Copiar código --------
COPY . .

# -------- Comando padrão --------
ENTRYPOINT ["python", "main.py"]
