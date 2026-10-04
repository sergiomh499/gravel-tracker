"""
gravel_bot - Sistema Modular de Rastreo, Valoración y Notificación de Bicicletas Gravel
"""

__version__ = "2.0.0"

from gravel_bot.config import RIDER_PROFILE, ALERT_CRITERIA
from gravel_bot.db import init_db, get_all_bikes, get_deals, upsert_bike
from gravel_bot.evaluator import detect_bike_specs, calcular_rubrica
from gravel_bot.pipeline import run_pipeline
from gravel_bot.notifier import send_telegram_alert

__all__ = [
    "RIDER_PROFILE",
    "ALERT_CRITERIA",
    "init_db",
    "get_all_bikes",
    "get_deals",
    "upsert_bike",
    "detect_bike_specs",
    "calcular_rubrica",
    "run_pipeline",
    "send_telegram_alert"
]
