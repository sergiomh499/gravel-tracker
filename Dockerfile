FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias si las hubiera
COPY . /app

ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV TELEGRAM_BOT_TOKEN=8987812105:AAGEPtpXKz8kcai8TkcOILFRyIhpNqOTdJQ
ENV TELEGRAM_CHAT_ID=4983947

EXPOSE 10000 8080

CMD ["python", "gravel_tracker.py", "--bot"]
