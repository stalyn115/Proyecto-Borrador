FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código y base de datos
COPY backend_api.py .
COPY aguarico_v6.db .

# Carpeta de reportes
RUN mkdir -p /app/reportes

EXPOSE 8000

CMD ["uvicorn", "backend_api:app", "--host", "0.0.0.0", "--port", "8000"]
