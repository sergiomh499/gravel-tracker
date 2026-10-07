"""
gravel_bot.config - Configuración Centralizada del Sistema de Rastreo Gravel
"""

import os
from pathlib import Path

# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("GRAVEL_DB_PATH", str(BASE_DIR / "gravel_madrid.db"))

# Perfil del Ciclista (Sergio - Méndez Álvaro, Madrid)
RIDER_PROFILE = {
    "estatura_cm": 169,
    "estatura_m": 1.69,
    "talla_estricta": "S",
    "tallas_admisibles": ["S", "SM", "50", "51", "52"],
    "tallas_especiales": {
        "canyon": ["XS", "48"], # Canyon talla muy grande
        "focus": ["XS", "48"],  # Focus talla muy grande
    },
    "zona": "Madrid",
    "presupuesto_objetivo": 1000.0,
    "presupuesto_max_justificado": 1350.0,
}

# Cargar variables desde .env si existe
env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v

# Configuración de Alertas y Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or "8987812105:AAGEPtpXKz8kcai8TkcOILFRyIhpNqOTdJQ"
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip() or "4983947"

# Umbrales mínimos para disparar Notificación en Telegram
ALERT_CRITERIA = {
    "nota_minima": 8.5,            # Nota sobre 10 mínima requerida
    "tiers_permitidos": ["Tier S+", "Tier S"],
    "max_precio": 1450.0,          # Máximo precio absoluto a notificar
    "exigir_talla_compatible": True,
}

# User-Agent y Headers HTTP para Scrapers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

SCAN_INTERVAL_SECONDS = int(os.environ.get("GRAVEL_SCAN_INTERVAL", "3600"))
