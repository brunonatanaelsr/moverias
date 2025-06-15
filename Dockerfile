# Copilot: Dockerfile
# - python:3.12-slim
# - instalar build deps gcc libpq-dev; pip install -r requirements.txt
# - coletar static; CMD gunicorn movemarias.wsgi:application --bind 0.0.0.0:$PORT

FROM python:3.12-slim

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do projeto
COPY . .

# Criar diretórios necessários
RUN mkdir -p staticfiles media

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput

# Criar usuário não-root
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Expor porta
EXPOSE $PORT

# Comando de execução
CMD gunicorn movemarias.wsgi:application --bind 0.0.0.0:$PORT
