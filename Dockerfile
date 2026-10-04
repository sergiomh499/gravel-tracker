FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias si las hubiera
COPY . /app

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["python", "gravel_tracker.py", "--bot"]
