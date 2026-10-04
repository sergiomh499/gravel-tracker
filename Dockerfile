FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias si las hubiera
COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["python", "gravel_tracker.py", "--bot"]
