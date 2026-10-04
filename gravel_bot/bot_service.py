"""
gravel_bot.bot_service - Servicio Interactivo de Telegram Bot (Polling y Comandos)
Soporta personalización multiusuario por perfil (altura, presupuesto, transmisión),
cálculo dinámico de talla por fabricante y validación automática de enlaces y fichas.
"""
from __future__ import annotations
import os
import time
from typing import Dict, Any, Optional, List, Tuple
import json
import threading
import traceback
import http.server
import socketserver
import urllib.request
import urllib.error
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
def register_bot_commands():
    """Registra el menú de comandos oficial de Telegram para autocompletar."""
    if not TELEGRAM_BOT_TOKEN:
        return
    commands = [
        {"command": "ranking", "description": "🏆 Podio y Tier List para tu fisionomía"},
        {"command": "catalogo", "description": "🚲 Ver gravels en stock (ej: /catalogo S+)"},
        {"command": "chollazos", "description": "💥 Gangas por % descuento (ej: /chollazos 1200)"},
        {"command": "ficha", "description": "📄 Ficha y dónde comprar (ej: /ficha kalima)"},
        {"command": "historial", "description": "📈 Evolución de precios (ej: /historial jakar)"},
        {"command": "tiendas", "description": "📍 Tiendas físicas en Madrid recomendadas"},
        {"command": "stats", "description": "📊 Estadísticas globales de catálogo y precios"},
        {"command": "perfil", "description": "👤 Ver tu perfil y tallaje dinámico"},
        {"command": "altura", "description": "📏 Ajustar tu estatura (ej: /altura 169)"},
        {"command": "presupuesto", "description": "💰 Ajustar presupuesto (ej: /presupuesto 1000)"},
        {"command": "holgura", "description": "🎯 Margen para chollos (ej: /holgura 15)"},
        {"command": "transmision", "description": "⚙️ Preferencia 1x / 2x / indiferente"},
        {"command": "add", "description": "📥 Analizar bici pegando una URL"},
        {"command": "help", "description": "ℹ️ Ayuda completa y guía de uso"}
    ]
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
        data = json.dumps({"commands": commands}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        print(f"⚠️ No se pudo registrar setMyCommands en Telegram: {e}")

def send_reply(chat_id: int, text: str):
    """Envía un mensaje formateado a Telegram con auto-chunking seguro (<3800 chars) y fallback a texto plano."""
    if not TELEGRAM_BOT_TOKEN or not text:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    chunks = []
    if len(text) <= 3800:
        chunks = [text]
    else:
        paragraphs = text.split("\n\n")
        curr = ""
        for p in paragraphs:
            if len(curr) + len(p) + 2 > 3800:
                if curr:
                    chunks.append(curr.strip())
                curr = p + "\n\n"
            else:
                curr += p + "\n\n"
        if curr.strip():
            chunks.append(curr.strip())

    for chunk in chunks[:4]:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception as e:
            # Si Telegram rechaza el parseo HTML, reenviar en texto plano
            try:
                payload.pop("parse_mode", None)
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10):
                    pass
            except Exception as e2:
                print(f"❌ Error enviando respuesta Telegram: {e2}")
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

def _process_message(msg: Dict[str, Any]):
    """Procesa un comando recibido en Telegram y responde al usuario de forma personalizada."""
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    raw_text = (msg.get("text") or "").strip()
    text = raw_text.lower()
    username = chat.get("username") or ""

    if not chat_id:
        return

    print(f"📩 [TELEGRAM] Mensaje de @{username} ({chat_id}): '{raw_text}'")

    if text in ["/start", "start"]:
        prof = get_profile_for_chat(chat_id, username)
        h = prof["estatura_cm"]
        bud = int(prof["presupuesto_max"])
        holgura = int(prof.get("holgura_max_pct", 15.0))
        tope = int(bud * (1.0 + holgura / 100.0))

        welcome = (
            "🎉 <b>¡BIENVENIDO A TU GRAVEL ASSISTANT EN MADRID!</b> 🚲\n\n"
            "He configurado automáticamente tu <b>Perfil de Ciclista</b> para cazar la gravel ideal:\n"
            f" • 📏 <b>Estatura:</b> <code>{h} cm</code> (Talla base calculada: <b>{prof['talla_calculada']}</b>)\n"
            f" • 💰 <b>Presupuesto Objetivo:</b> <code>{bud} €</code> (Hasta <b>{tope} €</b> con holgura para chollazos)\n"
            f" • 📍 <b>Ubicación:</b> Méndez Álvaro / Madrid Río (Prioridad tiendas físicas cercanas)\n"
            f" • 🧭 <b>Uso:</b> 50% Asfalto / 50% Pista y Tierra\n\n"
            "🧠 <b>¿CÓMO TE AYUDO A ELEGIR?</b>\n"
            "1. <b>Tallaje Biomecánico Dinámico:</b> Cada fabricante talla diferente. Calculo tu talla exacta según la geometría real (ej. Canyon XS, Focus 48, Conor SM, Megamo S, Trek 52).\n"
            "2. <b>Rastreo Multi-Tienda en Madrid y Online:</b> Monitorizo 14 tiendas físicas y outlets (Sanferbike M-30, Calmera Atocha, Fabregues, Mammoth, Chollometro...).\n"
            "3. <b>Historial de Precios:</b> Registro caídas y subidas de precio para detectar auténticas gangas.\n\n"
            "📌 <b>COMANDOS PRINCIPALES:</b>\n"
            " • 🏆 <b>/ranking</b>: Tu Podio y Tier List personalizado a tus 169 cm y presupuesto.\n"
            " • 🚲 <b>/catalogo</b>: Ver todas las bicicletas disponibles en stock actualmente.\n"
            " • 📄 <code>/ficha [modelo]</code>: Ficha técnica con componentes, dónde comprarla y distancia (ej: <code>/ficha Kalima</code> o <code>/ficha Jakar</code>).\n"
            " • 💥 <code>/chollazos [máx €]</code>: Gangas ordenadas por % de descuento (ej: <code>/chollazos 1200</code> o <code>/chollazos 30%</code>).\n"
            " • 📍 <b>/tiendas</b>: Tiendas físicas recomendadas para ver y probar talla desde Méndez Álvaro.\n"
            " • 📈 <code>/historial [modelo]</code>: Evolución histórica de precios de un modelo.\n"
            " • 📊 <b>/stats</b>: Estadísticas globales del catálogo y tiendas.\n"
            " • 📥 <code>/add [URL]</code>: Pega cualquier enlace de una bici para analizarla al instante.\n\n"
            "⚙️ <b>PERSONALIZACIÓN DE TU PERFIL:</b>\n"
            " • <code>/altura 172</code>: Ajustar tu estatura exacta en cm.\n"
            " • <code>/presupuesto 1200</code>: Ajustar tu presupuesto base.\n"
            " • <code>/holgura 20</code>: Margen extra % admisible en grandes ofertas.\n\n"
            "🚀 <b>¿Por dónde empezar?</b> Escribe <b>/ranking</b> para ver tus mejores opciones o <b>/ficha Kalima</b>."
        )
        send_reply(chat_id, welcome)

    elif text in ["/help", "help", "ayuda", "menu"]:
        help_msg = (
            "🚲 <b>GRAVEL BOT - GUÍA RÁPIDA DE COMANDOS</b> 🚲\n\n"
            "🏆 <b>/ranking</b>: Ver tu Tier List personalizado.\n"
            "🚲 <b>/catalogo</b>: Ver todas las bicis disponibles en stock.\n"
            "📄 <code>/ficha [modelo]</code>: Ficha técnica, componentes y dónde comprarla.\n"
            "💥 <code>/chollazos [máx €]</code>: Gangas ordenadas por % de descuento.\n"
            "📍 <b>/tiendas</b>: Tiendas físicas recomendadas en Madrid.\n"
            "📈 <code>/historial [modelo]</code>: Evolución histórica de precios.\n"
            "📊 <b>/stats</b>: Estadísticas del catálogo.\n"
            "📥 <code>/add [URL]</code>: Ingestar una nueva bici desde un enlace web.\n"
            "👤 <b>/perfil</b>: Ver o editar tu estatura y presupuesto."
        )
        send_reply(chat_id, help_msg)
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
        tier_arg = None
        max_p = None
        brand_arg = None
        if len(parts) > 1:
            arg = parts[1].strip()
            if arg.upper() in ["S+", "S", "A", "B", "C"]:
                tier_arg = f"Tier {arg.upper()}"
            elif "tier" in arg.lower():
                tier_arg = " ".join(parts[1:]).title()
            elif arg.replace(".", "").isdigit():
                max_p = float(arg)
            else:
                brand_arg = arg
        from gravel_bot.bike_inspector import format_available_bikes_message
        send_reply(chat_id, format_available_bikes_message(tier=tier_arg, max_price=max_p, brand=brand_arg))

    elif any(raw_text.lower().startswith(cmd) for cmd in ["/ficha", "/info", "/detalle", "ficha", "info"]):
        parts = raw_text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip():
            query = parts[1].strip()
            from gravel_bot.bike_inspector import format_detailed_bike_card
            send_reply(chat_id, format_detailed_bike_card(query))
        else:
            send_reply(chat_id, "ℹ️ Escribe el modelo que deseas consultar. Ejemplos:\n • <code>/ficha Kalima</code>\n • <code>/ficha Jakar</code>\n • <code>/ficha Orbea</code>\n • <code>/ficha Esker</code>")
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

def handle_incoming_message(msg: Dict[str, Any]):
    """Procesa un comando recibido en Telegram capturando cualquier excepción para no congelar el bot."""
    try:
        _process_message(msg)
    except Exception as e:
        print(f"❌ Error en handle_incoming_message: {e}")
        traceback.print_exc()
        chat_id = msg.get("chat", {}).get("id")
        if chat_id:
            send_reply(chat_id, f"⚠️ Error al procesar tu solicitud: {e}")

class CloudHealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"healthy","service":"gravel-bot-madrid"}\n')

    def log_message(self, format, *args):
        pass

def _start_cloud_health_server(port: int):
    try:
        import socketserver
        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True
        with ReusableTCPServer(("", port), CloudHealthHandler) as httpd:
            print(f"🌐 [CLOUD HEALTH] Servidor de comprobación activo en puerto {port} (Render / Koyeb).")
            httpd.serve_forever()
    except Exception as e:
        print(f"⚠️ [CLOUD HEALTH] No se pudo iniciar en puerto {port}: {e}")

def run_bot_polling(duration_seconds: Optional[int] = None):
    """Bucle de escucha de mensajes en Telegram con long-polling y soporte para ejecución acotada o continua en la nube."""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN no configurado.")
        return

    port_env = os.environ.get("PORT")
    if port_env and port_env.isdigit():
        threading.Thread(target=_start_cloud_health_server, args=(int(port_env),), daemon=True).start()
    print("🤖 [BOT POLLING] Registrando autocompletar de comandos en Telegram...")
    register_bot_commands()

    print("🤖 [BOT POLLING] Escuchando comandos en Telegram para @GravelDealSearchBot...")
    start_time = time.time()
    offset = None
    while True:
        if duration_seconds and (time.time() - start_time) >= duration_seconds:
            print(f"⏱️ [BOT POLLING] Sesión en la nube completada ({duration_seconds}s). Finalizando para persistir datos.")
            break
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=25"
        if offset:
            url += f"&offset={offset}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.loads(res.read().decode("utf-8"))
                updates = data.get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    msg = update.get("message")
                    if msg:
                        threading.Thread(target=handle_incoming_message, args=(msg,), daemon=True).start()
                if not updates:
                    time.sleep(1)
        except Exception as e:
            time.sleep(2)
