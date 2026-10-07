"""
gravel_bot.deal_detector - Detector Puro de Gangas por Diferencia de Precio
Identifica y clasifica ofertas basándose EXCLUSIVAMENTE en el ahorro económico real
(porcentaje de descuento y euros de diferencia respecto al PVP), sin importar componentes.
"""

from typing import List, Dict, Any, Optional
import sqlite3
from gravel_bot.db import get_connection

def get_pure_deals(
    min_discount_pct: float = 20.0,
    min_savings_eur: float = 100.0,
    sort_by: str = "descuento_pct", # "descuento_pct" o "ahorro_eur"
    solo_gravel: bool = True,
    max_price: Optional[float] = None,
    limit: int = 15,
    solo_talla_compatible: bool = False
) -> List[Dict[str, Any]]:
    """
    Recupera bicicletas ordenadas estrictamente por diferencia de precio (descuento o ahorro),
    independientemente de sus componentes, grupo o marca.
    """
    conn = get_connection()
    c = conn.cursor()
    order_clause = "descuento_pct DESC, ahorro_eur DESC" if sort_by == "descuento_pct" else "ahorro_eur DESC, descuento_pct DESC"

    query = f"""
    SELECT b.*, t.nombre as tienda_nombre, t.url as tienda_web,
           ROUND(b.precio_pvp - b.precio_oferta, 2) as ahorro_eur,
           ROUND(((b.precio_pvp - b.precio_oferta) / b.precio_pvp) * 100, 1) as descuento_pct
    FROM bicicletas b
    LEFT JOIN tiendas t ON b.tienda_id = t.id
    WHERE b.precio_pvp > b.precio_oferta
      AND b.en_stock = 1
      AND (? = 0 OR b.disciplina = 'gravel')
      AND (? = 0 OR (b.talla_recomendada_169 NOT IN ('No compatible', 'Incompatible (No gravel)') AND b.tier != 'Tier C'))
      AND (? IS NULL OR b.precio_oferta <= ?)
      AND (
          ((b.precio_pvp - b.precio_oferta) / b.precio_pvp * 100) >= ?
          OR (b.precio_pvp - b.precio_oferta) >= ?
      )
    ORDER BY {order_clause}
    LIMIT ?
    """
    c.execute(query, (1 if solo_gravel else 0, 1 if solo_talla_compatible else 0, max_price, max_price, min_discount_pct, min_savings_eur, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def format_pure_deals_message(sort_by: str = "descuento_pct", limit: int = 10, max_price: Optional[float] = None, min_discount_pct: float = 20.0, solo_talla_compatible: bool = False) -> str:
    """
    Genera el informe de Chollos Puros filtrado y ordenado por porcentaje de descuento para Telegram y CLI.
    Permite filtrar por precio máximo de oferta, porcentaje mínimo y compatibilidad estricta de talla.
    """
    deals = get_pure_deals(sort_by=sort_by, limit=limit, max_price=max_price, min_discount_pct=min_discount_pct, solo_talla_compatible=solo_talla_compatible)
    if not deals:
        precio_nota = f" por debajo de {int(max_price)} €" if max_price else ""
        return f"ℹ️ No se han detectado gangas con descuentos superiores al {int(min_discount_pct)}%{precio_nota} en este momento."

    filtros = [f"Mín: {int(min_discount_pct)}%"]
    if max_price:
        filtros.append(f"Tope: {int(max_price)} €")
    filtros_txt = " | ".join(filtros)

    msg = "💥 <b>DETECTOR DE GANGAS Y CHOLLOS POR % DE DESCUENTO</b> 💥\n"
    msg += f"<i>(Ordenado estrictamente por mayor porcentaje de descuento real sobre PVP | {filtros_txt})</i>\n\n"
    for i, d in enumerate(deals, 1):
        nombre = f"{d['marca']} {d['modelo']}"[:30]
        oferta = int(d['precio_oferta'])
        pvp = int(d['precio_pvp'])
        ahorro = int(d['ahorro_eur'])
        pct = d['descuento_pct']
        tienda = (d['tienda_nombre'] or "Tienda")[:20]
        talla = d.get('talla_recomendada_169', 'N/D')
        url = d.get('url_oferta') or ""

        link_str = f"<a href='{url}'>{nombre}</a>" if url else nombre

        # Distintivo según el nivel de descuento
        if pct >= 40.0 or ahorro >= 800:
            badge = "🔥💣 <b>MEGA-CHOLLO</b>"
        elif pct >= 30.0 or ahorro >= 400:
            badge = "⚡ <b>SUPER REBAJA</b>"
        else:
            badge = "🏷️ <b>OFERTA</b>"

        msg += f"<b>{i}. {badge} | -{pct}% (-{ahorro} €)</b>\n"
        msg += f"   🚲 {link_str}\n"
        msg += f"   💰 <b>{oferta} €</b> (<s>{pvp} €</s>) | 📍 <i>{tienda}</i>\n"
        msg += f"   📏 Talla detectada: <b>{talla}</b>\n\n"
    msg += "💡 <i>Este ranking no juzga si los frenos son mecánicos o hidráulicos; ordena únicamente por el dinero que te ahorras respecto al PVP original.</i>"
    return msg
def format_bike_price_history_message(query: str) -> str:
    """
    Genera un informe detallado con la evolución cronológica de precios de un modelo.
    """
    from gravel_bot.db import get_bike_price_history
    bike, history = get_bike_price_history(query)
    if not bike:
        return f"ℹ️ No se ha encontrado ninguna bicicleta en la base de datos que coincida con '{query}'."

    msg = f"📊 <b>HISTORIAL DE PRECIOS: {bike['marca']} {bike['modelo']}</b>\n"
    msg += f"💰 <b>Precio Actual: {int(bike['precio_oferta'])} €</b> (PVP: {int(bike.get('precio_pvp') or bike['precio_oferta'])} €)\n"
    msg += f"🏷️ <i>Tier: {bike['tier']} | Puntuación Rúbrica: {bike['nota']}/10</i>\n\n"

    if not history:
        msg += "<i>Aún no hay registros de fluctuaciones guardados para este modelo.</i>"
        return msg

    msg += "<b>Evolución cronológica de precios detectados:</b>\n"
    prev_price = None
    for h in history:
        p = int(h["precio"])
        fecha = h["fecha_registro"][:16]
        tienda = h.get("tienda_nombre") or "Tienda"

        diff_str = ""
        if prev_price is not None:
            diff = p - prev_price
            if diff < 0:
                diff_str = f" 🟢 <b>({diff} € 📉 Rebaja)</b>"
            elif diff > 0:
                diff_str = f" 🔴 <b>(+{diff} € 📈 Subida)</b>"
            else:
                diff_str = " ⚪ (Mantiene precio)"

        msg += f" • <code>{fecha}</code>: <b>{p} €</b>{diff_str} | <i>{tienda}</i>\n"
        prev_price = p

    return msg

def check_and_notify_size_alerts(bike: Dict[str, Any]) -> List[int]:
    """Comprueba si una bicicleta en stock coincide con alertas de talla pendientes de usuarios."""
    if not bike.get("en_stock"):
        return []
    modelo = (bike.get("modelo") or "").lower()
    marca = (bike.get("marca") or "").lower()
    talla_bici = str(bike.get("talla_recomendada_169") or "").upper()
    nombre_completo = f"{marca} {modelo}"

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT a.id, a.usuario_id, a.termino_modelo, a.talla_deseada, u.telegram_chat_id
    FROM alertas_talla_usuario a
    JOIN usuarios u ON a.usuario_id = u.id
    WHERE a.activa = 1 AND u.activo = 1
    """)
    alerts = c.fetchall()
    notified_users = []
    for a in alerts:
        term = a["termino_modelo"].lower()
        desired_size = a["talla_deseada"].upper()
        if term in nombre_completo:
            if desired_size in talla_bici or talla_bici.startswith(desired_size):
                chat_id = a["telegram_chat_id"]
                if chat_id:
                    from gravel_bot.bot_service import send_reply
                    msg = (
                        f"🚨 <b>¡REPOSICIÓN DETECTADA DE TU TALLA!</b> 🚨\n\n"
                        f"Hemos detectado disponibilidad de <b>{bike.get('marca', '')} {bike.get('modelo', '')}</b> en tu talla buscada (<b>{desired_size}</b>)!\n\n"
                        f" • <b>Precio:</b> {int(bike['precio_oferta'])} €\n"
                        f" • <b>Enlace:</b> <a href='{bike.get('url_oferta', '')}'>Ir a la Oferta Directa</a>\n\n"
                        f"<i>Para desactivar esta alerta escribe: <code>/borraralerta {a['id']}</code></i>"
                    )
                    try:
                        send_reply(chat_id, msg)
                        notified_users.append(a["usuario_id"])
                    except Exception as e:
                        print(f"Error notificando alerta de talla: {e}")
    conn.close()
    return notified_users

format_deals_message = format_pure_deals_message
