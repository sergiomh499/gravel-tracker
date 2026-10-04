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
    min_savings_eur: float = 200.0,
    sort_by: str = "ahorro_eur", # "ahorro_eur" o "descuento_pct"
    solo_gravel: bool = True,
    limit: int = 15
) -> List[Dict[str, Any]]:
    """
    Recupera bicicletas ordenadas estrictamente por diferencia de precio (descuento o ahorro),
    independientemente de sus componentes, grupo o marca.
    """
    conn = get_connection()
    c = conn.cursor()

    order_clause = "ahorro_eur DESC, descuento_pct DESC" if sort_by == "ahorro_eur" else "descuento_pct DESC, ahorro_eur DESC"

    query = f"""
    SELECT b.*, t.nombre as tienda_nombre, t.url as tienda_web,
           ROUND(b.precio_pvp - b.precio_oferta, 2) as ahorro_eur,
           ROUND(((b.precio_pvp - b.precio_oferta) / b.precio_pvp) * 100, 1) as descuento_pct
    FROM bicicletas b
    LEFT JOIN tiendas t ON b.tienda_id = t.id
    WHERE b.precio_pvp > b.precio_oferta
      AND b.en_stock = 1
      AND (? = 0 OR b.disciplina = 'gravel')
      AND (
          ((b.precio_pvp - b.precio_oferta) / b.precio_pvp * 100) >= ?
          OR (b.precio_pvp - b.precio_oferta) >= ?
      )
    ORDER BY {order_clause}
    LIMIT ?
    """
    c.execute(query, (1 if solo_gravel else 0, min_discount_pct, min_savings_eur, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def format_pure_deals_message(sort_by: str = "ahorro_eur", limit: int = 10) -> str:
    """
    Genera el informe de Chollos Puros por Diferencia de Precio para Telegram y CLI.
    """
    deals = get_pure_deals(sort_by=sort_by, limit=limit)
    if not deals:
        return "ℹ️ No se han detectado gangas con descuentos superiores al 20% en este momento."

    criterio_txt = "Mayor Ahorro en Euros (€)" if sort_by == "ahorro_eur" else "Mayor Porcentaje de Descuento (%)"

    msg = "💥 <b>DETECTOR DE GANGAS Y CHOLLOS PUROS</b> 💥\n"
    msg += f"<i>(Filtrado exclusivamente por diferencia de precio PVP vs Oferta - {criterio_txt})</i>\n\n"

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
