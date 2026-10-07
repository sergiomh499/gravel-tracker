FROM python:3.11-slim

WORKDIR /app

COPY . /app

ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Puerto de servicio web y healthcheck para Render, Railway, Fly.io, Dokku, etc.
EXPOSE 10000 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '10000'), timeout=3)" || exit 1

CMD ["python", "gravel_tracker.py", "--bot"]
