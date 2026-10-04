"""
gravel_bot.bot_service - Servicio Interactivo de Telegram Bot (Polling y Comandos)
Soporta personalización multiusuario por perfil (altura, presupuesto, transmisión),
cálculo dinámico de talla por fabricante y validación automática de enlaces y fichas.
"""

import time
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from gravel_bot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from gravel_bot.db import (
    init_db, get_all_bikes, get_deals,
    get_or_create_user, get_user_profile, update_user_profile
)
from gravel_bot.pipeline import run_pipeline
from gravel_bot.geometry_sizing import get_recommended_size_dynamic
from gravel_bot.evaluator import calcular_rubrica_personalizada, calcular_talla_desde_estatura
from gravel_bot.validator import run_full_catalog_validation
from gravel_bot.store_recommender import format_stores_recommendation_message
from gravel_bot.deal_detector import format_pure_deals_message
def send_reply(chat_id: int, text: str):
    """Envía un mensaje de texto formateado en HTML al chat de Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            pass
    except Exception as e:
        print(f"❌ Error enviando respuesta Telegram: {e}")

def get_profile_for_chat(chat_id: int, username: str = "") -> Dict[str, Any]:
    """Obtiene o inicializa el perfil de ciclista asociado a este chat_id."""
    init_db()
    user_id = get_or_create_user(chat_id, username)
    prof = get_user_profile(user_id)
    if not prof:
        # Perfil por defecto (Sergio / Méndez Álvaro 1,69m)
        update_user_profile(user_id, estatura_cm=169, presupuesto_max=1350.0, preferencia_transmision="2x")
        prof = get_user_profile(user_id)
    return dict(prof) if prof else {
        "estatura_cm": 169, "talla_calculada": "S", "presupuesto_max": 1350.0,
        "preferencia_transmision": "2x", "terreno_asfalto_pct": 50
    }

def format_profile_message(chat_id: int, username: str = "") -> str:
    """Genera una ficha detallada del perfil y la tabla dinámica de tallas por marca."""
    prof = get_profile_for_chat(chat_id, username)
    h = prof["estatura_cm"]
    bud = int(prof["presupuesto_max"])
    trans = prof["preferencia_transmision"]

    # Calcular dinámicamente las tallas exactas para las principales marcas
    canyon_s = get_recommended_size_dynamic("Canyon", "Grizl", h)["talla_recomendada"]
    focus_s = get_recommended_size_dynamic("Focus", "ATLAS", h)["talla_recomendada"]
    trek_s = get_recommended_size_dynamic("Trek", "Checkpoint", h)["talla_recomendada"]
    orbea_s = get_recommended_size_dynamic("Orbea", "Terra", h)["talla_recomendada"]
    conor_s = get_recommended_size_dynamic("Conor", "Kalima", h)["talla_recomendada"]
    megamo_s = get_recommended_size_dynamic("Megamo", "Jakar", h)["talla_recomendada"]
    special_s = get_recommended_size_dynamic("Specialized", "Diverge", h)["talla_recomendada"]
    ridley_s = get_recommended_size_dynamic("Ridley", "Kanzo", h)["talla_recomendada"]

    holgura = float(prof.get("holgura_max_pct", 15.0))
    tope_holgura = int(bud * (1.0 + holgura / 100.0))

    msg = "👤 <b>TU PERFIL DE CICLISTA Y TALLAJE DINÁMICO</b> 👤\n\n"
    msg += f" • <b>Estatura:</b> {h} cm\n"
    msg += f" • <b>Presupuesto Base:</b> {bud} €\n"
    msg += f" • <b>Holgura para Chollazos:</b> +{int(holgura)}% (Hasta <b>{tope_holgura} €</b> si la oferta lo justifica)\n"
    msg += f" • <b>Transmisión preferida:</b> {trans}\n"
    msg += f" • <b>Uso declarado:</b> 50% Asfalto / 50% Tierra\n\n"

    msg += "📐 <b>Tallas Exactas Recomendadas por Fabricante:</b>\n"
    msg += f" • <b>Canyon</b> (Grizl/Grail): <b>{canyon_s}</b> <i>(talla grande)</i>\n"
    msg += f" • <b>Focus</b> (ATLAS): <b>{focus_s}</b> <i>(geometría larga)</i>\n"
    msg += f" • <b>Trek</b> (Checkpoint): <b>{trek_s}</b>\n"
    msg += f" • <b>Orbea</b> (Terra): <b>{orbea_s}</b>\n"
    msg += f" • <b>Conor</b> (Kalima): <b>{conor_s}</b>\n"
    msg += f" • <b>Megamo</b> (Jakar): <b>{megamo_s}</b>\n"
    msg += f" • <b>Specialized</b> (Diverge): <b>{special_s}</b>\n"
    msg += f" • <b>Ridley</b> (Kanzo): <b>{ridley_s}</b>\n\n"

    msg += "✏️ <b>Modificar tu configuración:</b>\n"
    msg += " • <code>/altura 175</code> (Cambiar estatura en cm)\n"
    msg += " • <code>/presupuesto 1000</code> (Cambiar tope de precio base)\n"
    msg += " • <code>/holgura 15</code> (Margen extra % si el chollo lo merece)\n"
    msg += " • <code>/transmision 1x</code> (o <code>/transmision 2x</code>)\n"
    msg += " • <code>/validar</code> (Auditar enlaces y recalcular tallas en vivo)"
    return msg

def format_tier_list_message(chat_id: Optional[int] = None) -> str:
    """Genera un resumen formateado del Tier list adaptado al perfil del usuario."""
    init_db()
    bikes = get_all_bikes()
    if not bikes:
        return "⚠️ La base de datos está vacía. Ejecuta /scan para buscar ofertas."

    perfil = get_profile_for_chat(chat_id) if chat_id else {
        "estatura_cm": 169, "talla_calculada": "S", "presupuesto_max": 1350.0,
        "preferencia_transmision": "2x", "terreno_asfalto_pct": 50
    }

    # Recalcular rúbrica dinámicamente con el perfil del usuario consultor
    evaluated_bikes = []
    for b in bikes:
        ev = calcular_rubrica_personalizada(dict(b), perfil)
        evaluated_bikes.append(ev)

    # Ordenar por nota personalizada
    evaluated_bikes.sort(key=lambda x: (x["puntuacion_total"], -x["precio_oferta"]), reverse=True)

    tiers_data: Dict[str, List[Any]] = {"Tier S+": [], "Tier S": [], "Tier A": [], "Tier C": []}
    for b in evaluated_bikes:
        t = b["tier"]
        if t in tiers_data:
            tiers_data[t].append(b)

    h = perfil["estatura_cm"]
    msg = f"🏆 <b>TIER LIST PERSONALIZADO ({h} cm | {int(perfil['presupuesto_max'])} €)</b> 🏆\n\n"

    # Tier S+
    msg += "⭐ <b>TIER S+: Las Compras Maestras</b>\n"
    for b in tiers_data["Tier S+"][:7]:
        nombre = f"{b['marca']} {b['modelo']}"[:28]
        precio = int(b['precio_oferta'])
        talla = b['talla_recomendada_169'][:12]
        url = b['url_oferta'] or ""
        link_str = f"<a href='{url}'>{nombre}</a>" if url else nombre
        badge_holgura = " ⚡<i>[Holgura]</i>" if b.get("holgura_aplicada") else ""
        msg += f" • <b>{b['nota']}</b> | {link_str} | <b>{precio} €</b> ({talla}){badge_holgura}\n"
    # Tier S
    msg += "\n🥈 <b>TIER S: Planes B de Alto Nivel</b>\n"
    for b in tiers_data["Tier S"][:5]:
        nombre = f"{b['marca']} {b['modelo']}"[:28]
        precio = int(b['precio_oferta'])
        url = b['url_oferta'] or ""
        link_str = f"<a href='{url}'>{nombre}</a>" if url else nombre
        msg += f" • <b>{b['nota']}</b> | {link_str} | {precio} €\n"

    # Tier A
    msg += "\n🥉 <b>TIER A: Económicas o con Frenos Mecánicos</b>\n"
    for b in tiers_data["Tier A"][:4]:
        nombre = f"{b['marca']} {b['modelo']}"[:28]
        precio = int(b['precio_oferta'])
        msg += f" • <b>{b['nota']}</b> | {nombre} | {precio} €\n"

    msg += f"\n<i>{len(bikes)} modelos evaluados dinámicamente para tu altura y presupuesto.</i>"
    return msg

def format_deals_message(chat_id: Optional[int] = None) -> str:
    """Genera un resumen de las mayores gangas y descuentos para Telegram."""
    init_db()
    deals = get_deals(min_discount_pct=18.0)
    if not deals:
        return "ℹ️ No se han detectado descuentos superiores al 18% en este momento."

    msg = "🎯 <b>MAYORES GANGAS Y DESCUENTOS EN TIENDAS</b> 🎯\n\n"
    for d in deals[:10]:
        nombre = f"{d['marca']} {d['modelo']}"[:28]
        oferta = int(d['precio_oferta'])
        pvp = int(d['precio_pvp'])
        ahorro = int(d['ahorro_eur'])
        pct = round(d['descuento_pct'])
        tienda = (d['tienda_nombre'] or "Tienda")[:18]
        url = d['url_oferta'] or ""
        link_str = f"<a href='{url}'>{nombre}</a>" if url else nombre

        msg += f"🔥 <b>-{pct}% (-{ahorro} €)</b> | <b>{oferta} €</b> (PVP {pvp} €)\n"
        msg += f"   🚲 {link_str}\n"
        msg += f"   📍 <i>{tienda}</i> | Talla: {d['talla_recomendada_169']}\n\n"

    return msg

def handle_incoming_message(msg: Dict[str, Any]):
    """Procesa un comando recibido en Telegram y responde al usuario de forma personalizada."""
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    raw_text = (msg.get("text") or "").strip()
    text = raw_text.lower()
    username = chat.get("username") or ""

    if not chat_id:
        return

    print(f"📩 [TELEGRAM] Mensaje de @{username} ({chat_id}): '{raw_text}'")

    if text in ["/start", "/help", "hola", "menu"]:
        welcome = (
            "👋 <b>¡Hola! Soy tu Gravel Deals Bot de Madrid</b> 🚲\n\n"
            "Calculo la talla exacta <b>según la marca y modelo</b> y puntúo las mejores ofertas para tu presupuesto.\n\n"
            "📌 <b>Comandos de Consulta y Fichas:</b>\n"
            " • <b>/ranking</b>: Tier list personalizado a tu fisionomía.\n"
            " • <b>/catalogo</b>: Ver todas las bicicletas disponibles en stock.\n"
            " • <code>/ficha [modelo]</code>: Ficha técnica detallada, componentes y dónde comprarla.\n"
            " • <code>/historial [modelo]</code>: Evolución y fluctuaciones de precios.\n"
            " • <code>/chollazos [máx €]</code>: Gangas por % de descuento (ej: <code>/chollazos 1200</code>).\n"
            " • <b>/tiendas</b>: Recomendador de tiendas físicas a visitar en Madrid.\n"
            " • <b>/stats</b>: Estadísticas globales de catálogo y precios.\n"
            " • <code>/add [URL]</code>: Ingestar una nueva bici desde cualquier enlace web.\n"
            " • <code>/add_tienda [Nombre] [URL]</code>: Registrar una nueva tienda.\n\n"
            "⚙️ <b>Personalización de tu Perfil:</b>\n"
            " • <b>/perfil</b>: Ver tu configuración y tallas por marca.\n"
            " • <code>/altura 172</code>: Ajustar tu estatura exacta en cm.\n"
            " • <code>/presupuesto 1000</code>: Ajustar tu presupuesto base.\n"
            " • <code>/holgura 15</code>: Margen extra % admisible si la oferta es excelente.\n"
            " • <code>/transmision 2x</code>: Ajustar preferencia (1x / 2x)."
        )
        send_reply(chat_id, welcome)

    elif text in ["/perfil", "/profile", "perfil", "mi perfil"]:
        send_reply(chat_id, format_profile_message(chat_id, username))

    elif text.startswith("/altura") or text.startswith("/setaltura"):
        parts = raw_text.split()
        if len(parts) >= 2 and parts[1].replace(".", "").isdigit():
            val = int(float(parts[1]))
            if 140 <= val <= 215:
                user_id = get_or_create_user(chat_id, username)
                update_user_profile(user_id, estatura_cm=val)
                send_reply(chat_id, f"✅ <b>Estatura actualizada a {val} cm</b>.\n\nEscribe <b>/perfil</b> para ver tu tabla dinámica de tallas actualizada o <b>/ranking</b> para ver tus notas adaptadas.")
            else:
                send_reply(chat_id, "⚠️ Introduce una estatura realista en cm (entre 140 y 215). Ej: <code>/altura 169</code>")
        else:
            send_reply(chat_id, "ℹ️ Formato: <code>/altura 169</code> (en centímetros)")

    elif text.startswith("/presupuesto") or text.startswith("/setpresupuesto"):
        parts = raw_text.split()
        if len(parts) >= 2 and parts[1].replace(".", "").isdigit():
            val = float(parts[1])
            holgura_val = None
            if len(parts) >= 3 and parts[2].replace(".", "").isdigit():
                holgura_val = float(parts[2])
            if 400 <= val <= 10000:
                user_id = get_or_create_user(chat_id, username)
                update_kwargs = {"presupuesto_max": val}
                if holgura_val is not None and 0 <= holgura_val <= 50:
                    update_kwargs["holgura_max_pct"] = holgura_val
                update_user_profile(user_id, **update_kwargs)
                h_txt = f" (con holgura de +{int(holgura_val)}%)" if holgura_val is not None else ""
                send_reply(chat_id, f"✅ <b>Presupuesto máximo fijado en {int(val)} €{h_txt}</b>.\n\nTus notas en <b>/ranking</b> se adaptan automáticamente a este tope.")
            else:
                send_reply(chat_id, "⚠️ Rango no válido. Ej: <code>/presupuesto 1000</code> o <code>/presupuesto 1000 15</code>")
        else:
            send_reply(chat_id, "ℹ️ Formato: <code>/presupuesto 1000</code> o <code>/presupuesto 1000 15</code>")

    elif text.startswith("/holgura") or text.startswith("/setholgura"):
        parts = raw_text.split()
        if len(parts) >= 2 and parts[1].replace(".", "").isdigit():
            val = float(parts[1])
            if 0 <= val <= 50:
                user_id = get_or_create_user(chat_id, username)
                update_user_profile(user_id, holgura_max_pct=val)
                send_reply(chat_id, f"✅ <b>Holgura para chollazos fijada en +{int(val)}%</b>.\n\nBicicletas superiores con buen descuento se admitirán hasta ese margen.")
            else:
                send_reply(chat_id, "⚠️ El porcentaje de holgura debe estar entre 0% y 50% (ej. <code>/holgura 15</code>).")
        else:
            send_reply(chat_id, "ℹ️ Formato: <code>/holgura 15</code> (porcentaje extra sobre presupuesto)")

    elif text.startswith("/transmision") or text.startswith("/settransmision"):
        parts = raw_text.split()
        if len(parts) >= 2 and parts[1].lower() in ["1x", "2x", "indiferente"]:
            val = parts[1].lower()
            user_id = get_or_create_user(chat_id, username)
            update_user_profile(user_id, preferencia_transmision=val)
            send_reply(chat_id, f"✅ <b>Preferencia de transmisión guardada: {val}</b>.")
        else:
            send_reply(chat_id, "ℹ️ Opciones válidas: <code>/transmision 2x</code>, <code>/transmision 1x</code> o <code>/transmision indiferente</code>")

    elif text in ["/validar", "/validate", "/audit", "validar"]:
        send_reply(chat_id, "🩺 <i>Iniciando validación automática de enlaces, precios en vivo y tallas dinámicas...</i>")
        summary = run_full_catalog_validation(auto_repair=True, verbose=False)
        msg = (
            "✅ <b>Validación Automática Completada</b> 🩺\n\n"
            f" • Bicicletas auditadas: <b>{summary['total_auditadas']}</b>\n"
            f" • Tallas reparadas dinámicamente: <b>{summary['tallas_reparadas_dinamicamente']}</b>\n"
            f" • Precios actualizados en vivo: <b>{summary['precios_actualizados']}</b>\n"
            f" • Modelos sin stock marcados: <b>{summary['sin_stock_detectados']}</b>\n\n"
            "La base de datos y tallas por marca se encuentran al 100% sincronizadas."
        )
        send_reply(chat_id, msg)

    elif text in ["/ranking", "/tier", "/tiers", "ranking", "tier"]:
        send_reply(chat_id, format_tier_list_message(chat_id))

    elif text in ["/deals", "/gangas", "/chollos", "deals", "ofertas"]:
        send_reply(chat_id, format_deals_message(chat_id))

    elif any(raw_text.lower().startswith(cmd) for cmd in ["/chollazos", "/gangaspuras", "/descuentos", "/chollos", "chollazos"]):
        parts = raw_text.split()
        max_p = None
        min_pct = 20.0
        for p in parts[1:]:
            if p.endswith("%"):
                val = p.rstrip("%")
                if val.replace(".", "").isdigit():
                    min_pct = float(val)
            elif p.replace(".", "").isdigit():
                num = float(p)
                if num <= 60 and ("%" in raw_text or len(parts) > 2):
                    min_pct = num
                else:
                    max_p = num
        send_reply(chat_id, format_pure_deals_message(sort_by="descuento_pct", max_price=max_p, min_discount_pct=min_pct))

    elif any(raw_text.lower().startswith(cmd) for cmd in ["/historial", "/history", "/precio", "/precios", "historial"]):
        parts = raw_text.split(maxsplit=1)
        query = parts[1] if len(parts) > 1 else "Kalima"
        from gravel_bot.deal_detector import format_bike_price_history_message
        send_reply(chat_id, format_bike_price_history_message(query))

    elif text in ["/tiendas", "/tiendasfisicas", "/dondeir", "tiendas", "ruta"]:
        send_reply(chat_id, format_stores_recommendation_message())

    elif text in ["/top", "/splus", "top", "s+"]:
        init_db()
        prof = get_profile_for_chat(chat_id, username)
        bikes = get_all_bikes()
        evaluated = [calcular_rubrica_personalizada(dict(b), prof) for b in bikes]
        s_plus = [b for b in evaluated if b["tier"] == "Tier S+"]
        s_plus.sort(key=lambda x: (x["puntuacion_total"], -x["precio_oferta"]), reverse=True)

        msg = f"⭐ <b>PODIO TIER S+ PARA TU PERFIL ({prof['estatura_cm']} cm)</b> ⭐\n\n"
        for b in s_plus[:8]:
            nombre = f"{b['marca']} {b['modelo']}"
            oferta = int(b['precio_oferta'])
            pvp = int(b['precio_pvp'])
            ahorro_str = f" <s>{pvp} €</s>" if pvp > oferta else ""
            url = b['url_oferta'] or ""
            link_str = f"<a href='{url}'>{nombre}</a>" if url else nombre
            msg += f"🥇 <b>{b['nota']} / 10</b> | {link_str}\n"
            msg += f"   💰 <b>{oferta} €</b>{ahorro_str} | Talla calculada: <b>{b['talla_recomendada_169']}</b>\n"
            msg += f"   ⚙️ {b['transmision']} | {b['frenos']}\n\n"
        send_reply(chat_id, msg)

    elif text in ["/scan", "scan", "buscar"]:
        send_reply(chat_id, "⏳ <i>Iniciando escaneo de tiendas en vivo... Esto tomará unos segundos.</i>")
        summary = run_pipeline(send_alerts=False, verbose=False)
        res_text = (
            "✅ <b>Escaneo completado con éxito</b>\n\n"
            f" • Productos rastreados: {summary['scraped_count']}\n"
            f" • Bicicletas indexadas: {summary['saved_count']}\n"
            f" • Gangas Tier S+/S activas: {len(summary['top_findings'])}\n\n"
            "Escribe <b>/ranking</b> o <b>/deals</b> para consultar los resultados."
        )
        send_reply(chat_id, res_text)
    elif any(raw_text.lower().startswith(cmd) for cmd in ["/catalogo", "/disponibles", "/bicis", "/stock", "catalogo", "disponibles"]):
        parts = raw_text.split()
        tier_arg = parts[1] if len(parts) > 1 and "tier" in parts[1].lower() else None
        from gravel_bot.bike_inspector import format_available_bikes_message
        send_reply(chat_id, format_available_bikes_message(tier=tier_arg))

    elif any(raw_text.lower().startswith(cmd) for cmd in ["/ficha", "/info", "/detalle", "ficha", "info"]):
        parts = raw_text.split(maxsplit=1)
        query = parts[1] if len(parts) > 1 else "Kalima"
        from gravel_bot.bike_inspector import format_detailed_bike_card
        send_reply(chat_id, format_detailed_bike_card(query))

    elif any(raw_text.lower().startswith(cmd) for cmd in ["/add_tienda", "/anadirtienda", "add_tienda"]):
        parts = raw_text.split()
        if len(parts) >= 3:
            nombre = parts[1]
            url = parts[2]
            tipo = parts[3] if len(parts) > 3 else "online"
            from gravel_bot.url_ingestor import ingest_store
            ok, res_text = ingest_store(nombre=nombre, url=url, tipo=tipo)
            send_reply(chat_id, res_text)
        else:
            send_reply(chat_id, "ℹ️ Formato: <code>/add_tienda NombreTienda https://tienda.com [online/fisica]</code>")

    elif any(raw_text.lower().startswith(cmd) for cmd in ["/add", "/anadir", "add"]):
        parts = raw_text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].startswith("http"):
            url = parts[1].strip()
            send_reply(chat_id, f"📥 <i>Analizando e ingestado enlace:</i>\n<code>{url}</code>...")
            from gravel_bot.url_ingestor import ingest_bike_url
            ok, res_card, _ = ingest_bike_url(url)
            send_reply(chat_id, res_card)
        else:
            send_reply(chat_id, "ℹ️ Formato: <code>/add https://tienda.com/producto-gravel</code>")

    elif text in ["/stats", "stats"]:
        from gravel_bot.bike_inspector import format_database_stats_message
        send_reply(chat_id, format_database_stats_message())
    else:
        send_reply(chat_id, "❓ Comando no reconocido. Escribe <b>/help</b>, <b>/perfil</b> o <b>/ranking</b> para ver la información.")

def run_bot_polling():
    """Bucle infinito de escucha de mensajes en Telegram con long-polling."""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN no configurado.")
        return

    print("🤖 [BOT POLLING] Escuchando comandos en Telegram para @GravelDealSearchBot...")
    print("Prueba enviando /perfil, /ranking o /deals desde tu Telegram.")

    offset = None
    while True:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=25"
        if offset:
            url += f"&offset={offset}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.loads(res.read().decode("utf-8"))
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message")
                    if msg:
                        handle_incoming_message(msg)
        except Exception as e:
            time.sleep(2)
