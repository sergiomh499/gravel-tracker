"""
gravel_bot.notifier - Notificador Automático de Gangas vía Telegram Bot API
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from gravel_bot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def format_alert_message(bike: Dict[str, Any]) -> str:
    """Formatea el mensaje de alerta para Telegram en HTML."""
    marca = bike.get("marca", "")
    modelo = bike.get("modelo", "")
    tier = bike.get("tier", "Tier S")
    nota = bike.get("nota", 0.0)
    oferta = bike.get("precio_oferta", 0.0)
    pvp = bike.get("precio_pvp", oferta)
    talla = bike.get("talla_recomendada_169", "S")
    trans = bike.get("transmision", "")
    frenos = bike.get("frenos", "")
    cuadro = bike.get("cuadro", "")
    tienda = bike.get("tienda_nombre", "Tienda online")
    url = bike.get("url_oferta", "")

    # Cálculo de ahorro
    ahorro_str = ""
    if pvp > oferta:
        pct = round((pvp - oferta) / pvp * 100)
        ahorro = round(pvp - oferta)
        ahorro_str = f" <s>{int(pvp)} €</s> <b>(-{pct}% | Ahorras {ahorro} €)</b>"

    tier_emoji = "🏆" if "S+" in tier else "⭐"

    msg = (
        f"{tier_emoji} <b>¡NUEVA GANGA GRAVEL DETECTADA!</b> {tier_emoji}\n\n"
        f"🚲 <b>Modelo:</b> {marca} {modelo}\n"
        f"🏅 <b>Calificación:</b> <code>{tier}</code> | <b>Nota:</b> <b>{nota} / 10</b>\n"
        f"💰 <b>Precio:</b> <b>{int(oferta)} €</b>{ahorro_str}\n"
        f"📏 <b>Talla para 1,69 m:</b> <b>{talla}</b> ✅\n"
        f"📍 <b>Tienda:</b> {tienda}\n\n"
        f"⚙️ <b>Montaje Técnico & Biomecánica:</b>\n"
        f" • <b>Transmisión:</b> {trans}\n"
        f" • <b>Frenos:</b> {frenos}\n"
        f" • <b>Cuadro:</b> {cuadro}\n"
        f" • <b>Ratio de Subida:</b> Climbing Ratio {bike.get('climbing_ratio', 0.85)} (Mín: {bike.get('lowest_gear_inches', 24.0)}\")\n\n"
    )
    return msg
def format_price_drop_message(bike: Dict[str, Any], drop_info: Dict[str, Any]) -> str:
    """Formatea el mensaje de alerta para caídas de precio significativas."""
    marca = bike.get("marca", "")
    modelo = bike.get("modelo", "")
    old_p = drop_info.get("old_price", 0.0)
    new_p = drop_info.get("new_price", 0.0)
    diff_eur = drop_info.get("drop_eur", 0.0)
    pct = drop_info.get("drop_pct", 0.0)
    url = bike.get("url_oferta", "")
    tier = bike.get("tier", "Tier S")
    talla = bike.get("talla_recomendada_169", "S")
    tienda = bike.get("tienda_nombre", "Tienda online/local")

    msg = (
        f"📉 <b>¡BAJADA DE PRECIO DETECTADA!</b> 📉\n\n"
        f"🚲 <b><a href='{url}'>{marca} {modelo}</a></b>\n"
        f"🎯 <b>Nivel:</b> {tier} ({bike.get('nota', 8.5)}/10)\n"
        f"💰 <b>Precio Anterior:</b> <s>{old_p:,.2f} €</s>\n"
        f"🔥 <b>Nuevo Precio:</b> <b>{new_p:,.2f} €</b>\n"
        f"💸 <b>Rebaja:</b> <b>-{diff_eur:,.2f} € (-{pct:.1f}%)</b>\n"
        f"📏 <b>Talla sugerida (1,69 m):</b> <b>{talla}</b>\n"
        f"📍 <b>Tienda:</b> {tienda}\n"
        f"⚙️ <b>Transmisión:</b> {bike.get('transmision', 'Consultar')}\n"
        f"🛑 <b>Frenos:</b> {bike.get('frenos', 'Consultar')}\n\n"
        f"🔗 <a href='{url}'>Ver oferta en tienda</a>"
    )
    return msg


def send_telegram_alert(bike_or_text: Any) -> bool:
    """
    Envía una alerta o mensaje formateado a Telegram.
    Acepta un diccionario de bicicleta o una cadena de texto HTML.
    """
    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID

    if isinstance(bike_or_text, str):
        msg = bike_or_text
    else:
        msg = format_alert_message(bike_or_text)
        print("\n" + "="*60)
        print("📢 [AVISO TELEGRAM PENDIENTE DE CONFIGURAR]")
        print("Para recibir alertas instantáneas en tu móvil, define:")
        print("  export TELEGRAM_BOT_TOKEN='tu_bot_token'")
        print("  export TELEGRAM_CHAT_ID='tu_chat_id'")
        print("-" * 60)
        print("Vista previa del mensaje generado:")
        print(msg.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "").replace("<s>", "").replace("</s>", "").replace("<a href='", "[").replace("'>", "] "))
        print("="*60 + "\n")
        return False

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            if res_body.get("ok"):
                label = f"{bike_or_text.get('marca', '')} {bike_or_text.get('modelo', '')}" if isinstance(bike_or_text, dict) else "Mensaje informativo"
                print(f"✅ Alerta Telegram enviada con éxito ({label})")
                return True
                print(f"❌ Error en respuesta Telegram: {res_body}")
                return False
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8", errors="ignore")
        print(f"❌ Error HTTP Telegram ({e.code}): {err_content}")
        return False
    except Exception as e:
        print(f"❌ Error de conexión con Telegram: {e}")
        return False

def test_telegram_connection() -> bool:
    """Verifica si el bot de Telegram está correctamente configurado."""
    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN no está definido.")
        return False
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID no está definido.")
        return False

    # 1. Comprobar identidad del bot (getMe)
    try:
        me_url = f"https://api.telegram.org/bot{token}/getMe"
        req = urllib.request.Request(me_url)
        with urllib.request.urlopen(req, timeout=10) as res:
            me_data = json.loads(res.read().decode("utf-8"))
            bot_name = me_data.get("result", {}).get("username", "Desconocido")
            print(f"🤖 Bot de Telegram autenticado: @{bot_name}")
    except Exception as e:
        print(f"❌ Error conectando con Telegram getMe: {e}")
        return False

    # 2. Enviar mensaje de prueba
    test_bike = {
        "marca": "Prueba",
        "modelo": "Test Bot Alert",
        "tier": "Tier S+",
        "nota": 10.0,
        "precio_oferta": 999.0,
        "precio_pvp": 1499.0,
        "talla_recomendada_169": "S (51 cm)",
        "transmision": "Shimano GRX 2x10v",
        "frenos": "Hidráulico",
        "cuadro": "Aluminio Triple Conificado",
        "tienda_nombre": "Prueba Local Madrid",
        "url_oferta": "https://github.com"
    }
    return send_telegram_alert(test_bike)
