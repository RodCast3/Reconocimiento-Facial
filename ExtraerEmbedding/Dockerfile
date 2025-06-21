FROM python:3.10-slim

# Instalar dependencias necesarias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar el archivo de dependencias e instalar
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente, pesos y módulos
COPY . .

# Exponer el puerto 8080 (requerido por Cloud Run)
ENV PORT=8080
EXPOSE 8080

# Comando de inicio
CMD ["python", "main.py"]
