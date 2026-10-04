"""
gravel_bot.bike_inspector - Detalle de Componentes, Valoración, Ficha de Compra y Estadísticas
"""

import sqlite3
from typing import Dict, Any, Optional, List, Tuple
from gravel_bot.db import get_connection

def get_detailed_bike_info(identifier: Any) -> Optional[Dict[str, Any]]:
    """
    Recupera una bicicleta completa con datos de tienda, historial de precios y estadísticas.
    """
    conn = get_connection()
    c = conn.cursor()

    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        c.execute("""
        SELECT b.*, t.nombre as tienda_nombre, t.tipo as tienda_tipo,
               t.direccion as tienda_direccion, t.distancia_km as tienda_distancia,
               t.telefono as tienda_telefono, t.whatsapp as tienda_whatsapp,
               t.url as tienda_web
        FROM bicicletas b
        LEFT JOIN tiendas t ON b.tienda_id = t.id
        WHERE b.id = ?
        """, (int(identifier),))
    else:
        query_str = f"%{str(identifier).lower()}%"
        c.execute("""
        SELECT b.*, t.nombre as tienda_nombre, t.tipo as tienda_tipo,
               t.direccion as tienda_direccion, t.distancia_km as tienda_distancia,
               t.telefono as tienda_telefono, t.whatsapp as tienda_whatsapp,
               t.url as tienda_web
        FROM bicicletas b
        LEFT JOIN tiendas t ON b.tienda_id = t.id
        WHERE b.slug = ? OR LOWER(b.modelo) LIKE ? OR LOWER(b.marca || ' ' || b.modelo) LIKE ?
        ORDER BY b.en_stock DESC, b.nota DESC
        LIMIT 1
        """, (str(identifier), query_str, query_str))

    row = c.fetchone()
    if not row:
        conn.close()
        return None

    bike = dict(row)

    # Historial de precios
    c.execute("""
    SELECT h.*, t.nombre as tienda_nombre
    FROM historial_precios h
    LEFT JOIN tiendas t ON h.tienda_id = t.id
    WHERE h.bicicleta_id = ?
    ORDER BY h.fecha_registro ASC
    """, (bike["id"],))
    history = [dict(r) for r in c.fetchall()]

    conn.close()

    # Calcular estadísticas de precios
    if history:
        precios = [h["precio"] for h in history if h.get("precio")]
        bike["min_historico"] = min(precios) if precios else bike["precio_oferta"]
        bike["max_historico"] = max(precios) if precios else bike["precio_pvp"]
        bike["historial_conteo"] = len(history)
        bike["primer_registro"] = history[0]["fecha_registro"]
        bike["ultimo_registro"] = history[-1]["fecha_registro"]
    else:
        bike["min_historico"] = bike["precio_oferta"]
        bike["max_historico"] = bike["precio_pvp"]
        bike["historial_conteo"] = 0
        bike["primer_registro"] = "Hoy"
        bike["ultimo_registro"] = "Hoy"

    bike["history"] = history
    return bike

def format_detailed_bike_card(identifier: Any) -> str:
    """
    Formatea la ficha técnica completa de una bicicleta en HTML para Telegram y CLI.
    """
    bike = get_detailed_bike_info(identifier)
    if not bike:
        return f"ℹ️ No se ha encontrado ninguna bicicleta que coincida con '{identifier}' en la base de datos."

    nombre = f"{bike['marca']} {bike['modelo']}"
    oferta = int(bike['precio_oferta'])
    pvp = int(bike['precio_pvp'] or bike['precio_oferta'])
    ahorro = pvp - oferta
    pct = round((ahorro / pvp * 100), 1) if pvp > oferta else 0.0

    # Tienda y ubicación
    tienda = bike.get("tienda_nombre") or "Tienda Especializada"
    tipo_tienda = bike.get("tienda_tipo") or "online"
    dir_tienda = bike.get("tienda_direccion")
    distancia = bike.get("tienda_distancia")
    url = bike.get("url_oferta") or ""

    link_tienda = f"<a href='{url}'>{tienda}</a>" if url else tienda

    stock_str = "🟢 En Stock" if bike.get("en_stock", 1) else "🔴 Agotada temporalmente"

    msg = f"🚲 <b>FICHA DETALLADA: {nombre.upper()}</b>\n"
    msg += f"<i>Año: {bike.get('ano', 2025)} | Disciplina: {bike.get('disciplina', 'gravel').capitalize()} | Estado: {stock_str}</i>\n\n"

    # Sección 1: Dónde comprarla y Precios
    msg += "📍 <b>DÓNDE COMPRARLA & PRECIO ACTUALIZADO:</b>\n"
    msg += f" • <b>Comercio:</b> {link_tienda} ({tipo_tienda.capitalize()})\n"
    if dir_tienda:
        dist_str = f" (~{distancia} km de Méndez Álvaro)" if distancia else ""
        msg += f" • <b>Dirección Física:</b> {dir_tienda}{dist_str}\n"
    if url:
        msg += f" • <b>Enlace Directo:</b> <a href='{url}'>Ver Oferta en Web</a>\n"

    msg += f" • <b>Precio Actual:</b> <b>{oferta} €</b>"
    if ahorro > 0:
        msg += f" (PVP: <s>{pvp} €</s> | <b>-{pct}% / Ahorras {ahorro} €</b>)\n"
    else:
        msg += "\n"

    # Sección 2: Componentes
    msg += "\n⚙️ <b>COMPONENTES DETALLADOS:</b>\n"
    msg += f" • <b>Cuadro:</b> {bike.get('cuadro', 'Aluminio')}\n"
    msg += f" • <b>Horquilla:</b> {bike.get('horquilla', 'Carbono')}\n"
    msg += f" • <b>Transmisión:</b> {bike.get('transmision', 'N/D')} (Grupo {bike.get('tipo_transmision', 'N/D')})\n"
    msg += f" • <b>Frenos:</b> {bike.get('frenos', 'N/D')} ({bike.get('tipo_frenos', 'N/D').replace('_', ' ').capitalize()})\n"
    msg += f" • <b>Ejes:</b> {bike.get('ejes', 'Pasantes 12 mm')}\n"
    udh_str = "✅ Sí (Universal Derailleur Hanger)" if bike.get('patilla_udh') else "❌ Patilla propietaria"
    msg += f" • <b>Patilla UDH:</b> {udh_str}\n"
    msg += f" • <b>Talla Óptima (1,69 m):</b> <b>{bike.get('talla_recomendada_169', 'S')}</b>\n"

    # Sección 3: Valoración y Rúbrica
    msg += f"\n🏆 <b>VALORACIÓN Y RÚBRICA MADRID 50/50:</b>\n"
    msg += f" • <b>Clasificación:</b> <b>{bike.get('tier', 'Tier S')}</b>\n"
    msg += f" • <b>Puntuación Global:</b> <b>{bike.get('nota', 0.0)} / 10</b> ({bike.get('puntuacion_total', 0)}/100 pts)\n"
    msg += f"   - Frenos (25%): <code>{bike.get('c1_frenos', 0)}/25</code>\n"
    msg += f"   - Transmisión 50/50 (25%): <code>{bike.get('c2_transmision', 0)}/25</code>\n"
    msg += f"   - Cuadro & Horquilla (20%): <code>{bike.get('c3_cuadro', 0)}/20</code>\n"
    msg += f"   - Relación Precio (20%): <code>{bike.get('c4_precio', 0)}/20</code>\n"
    msg += f"   - Talla & Geometría (10%): <code>{bike.get('c5_talla', 0)}/10</code>\n"
    if bike.get('notas_veredicto'):
        msg += f" • <i>Veredicto: {bike['notas_veredicto']}</i>\n"

    # Sección 4: Estadísticas de precio
    msg += f"\n📊 <b>ESTADÍSTICAS HISTÓRICAS DEL MODELO:</b>\n"
    msg += f" • Mínimo histórico detectado: <b>{int(bike['min_historico'])} €</b>\n"
    msg += f" • Máximo registrado: <b>{int(bike['max_historico'])} €</b>\n"
    msg += f" • Fluctuaciones registradas: <b>{bike['historial_conteo']}</b> registros acumulados\n"

    return msg

def get_database_stats() -> Dict[str, Any]:
    """
    Calcula estadísticas agregadas sobre el catálogo de bicicletas y tiendas.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT count(*) FROM bicicletas")
    total_bikes = c.fetchone()[0]

    c.execute("SELECT count(*) FROM bicicletas WHERE en_stock = 1")
    in_stock = c.fetchone()[0]

    c.execute("SELECT count(*) FROM tiendas")
    total_stores = c.fetchone()[0]

    c.execute("SELECT count(*) FROM historial_precios")
    total_price_records = c.fetchone()[0]

    # Distribución por tiers
    c.execute("SELECT tier, count(*) FROM bicicletas GROUP BY tier ORDER BY count(*) DESC")
    tier_dist = dict(c.fetchall())

    # Precios y descuentos
    c.execute("""
    SELECT MIN(precio_oferta), MAX(precio_oferta), AVG(precio_oferta),
           MAX((precio_pvp - precio_oferta) / precio_pvp * 100),
           MAX(precio_pvp - precio_oferta)
    FROM bicicletas
    WHERE en_stock = 1 AND precio_pvp > precio_oferta
    """)
    p_min, p_max, p_avg, max_desc_pct, max_saving_eur = c.fetchone()

    conn.close()

    return {
        "total_bicicletas": total_bikes,
        "en_stock": in_stock,
        "sin_stock": total_bikes - in_stock,
        "tiendas": total_stores,
        "puntos_historial": total_price_records,
        "distribucion_tiers": tier_dist,
        "precio_min": p_min or 0.0,
        "precio_max": p_max or 0.0,
        "precio_medio": round(p_avg or 0.0, 1),
        "max_descuento_pct": round(max_desc_pct or 0.0, 1),
        "max_ahorro_eur": round(max_saving_eur or 0.0, 1)
    }

def format_database_stats_message() -> str:
    """
    Genera el mensaje consolidado de estadísticas del sistema.
    """
    stats = get_database_stats()

    msg = "📊 <b>ESTADÍSTICAS GLOBALES DEL CATÁLOGO DE GRAVEL</b> 📊\n\n"
    msg += f" • <b>Total Modelos en Base de Datos:</b> <b>{stats['total_bicicletas']}</b>\n"
    msg += f"   - En stock disponible: <b>{stats['en_stock']}</b>\n"
    msg += f"   - Sin stock / descatalogadas: <b>{stats['sin_stock']}</b>\n"
    msg += f" • <b>Tiendas y Fuentes Monitorizadas:</b> <b>{stats['tiendas']}</b>\n"
    msg += f" • <b>Puntos de Historial de Precios:</b> <b>{stats['puntos_historial']}</b> registros\n\n"

    msg += "🎯 <b>Distribución por Tiers de Calidad:</b>\n"
    for tier, count in stats["distribucion_tiers"].items():
        msg += f"   • {tier}: <b>{count}</b> modelos\n"

    msg += f"\n💰 <b>Rango de Precios en Oferta:</b>\n"
    msg += f" • Mínimo: <b>{int(stats['precio_min'])} €</b> | Máximo: <b>{int(stats['precio_max'])} €</b> | Promedio: <b>{int(stats['precio_medio'])} €</b>\n"
    msg += f" • Descuento récord activo: <b>-{stats['max_descuento_pct']}%</b> (Ahorro de hasta <b>{int(stats['max_ahorro_eur'])} €</b>)\n"

    return msg

def get_available_bikes_list(tier: Optional[str] = None, max_price: Optional[float] = None, brand: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Recupera todas las bicicletas disponibles en stock que cumplan con los filtros.
    """
    conn = get_connection()
    c = conn.cursor()

    query = """
    SELECT b.*, t.nombre as tienda_nombre, t.tipo as tienda_tipo
    FROM bicicletas b
    LEFT JOIN tiendas t ON b.tienda_id = t.id
    WHERE b.en_stock = 1
    """
    params: List[Any] = []

    if tier:
        query += " AND b.tier = ?"
        params.append(tier)
    if max_price:
        query += " AND b.precio_oferta <= ?"
        params.append(max_price)
    if brand:
        query += " AND LOWER(b.marca) = ?"
        params.append(brand.lower())

    query += " ORDER BY b.nota DESC, b.precio_oferta ASC"
    c.execute(query, tuple(params))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def format_available_bikes_message(tier: Optional[str] = None, max_price: Optional[float] = None, brand: Optional[str] = None) -> str:
    """
    Formatea la lista de bicicletas disponibles en stock para consulta rápida.
    """
    bikes = get_available_bikes_list(tier=tier, max_price=max_price, brand=brand)
    if not bikes:
        return "ℹ️ No se encontraron bicicletas disponibles en stock con los filtros indicados."

    filtros = []
    if tier:
        filtros.append(f"Tier: {tier}")
    if max_price:
        filtros.append(f"Máx: {int(max_price)} €")
    if brand:
        filtros.append(f"Marca: {brand.capitalize()}")
    filtros_str = f" ({', '.join(filtros)})" if filtros else ""
    total_encontradas = len(bikes)
    bikes_mostradas = bikes[:10]

    msg = f"🚲 <b>BICICLETAS DISPONIBLES EN STOCK{filtros_str}</b> ({len(bikes_mostradas)} de {total_encontradas} modelos)\n\n"
    for i, b in enumerate(bikes_mostradas, 1):
        nombre = f"{b['marca']} {b['modelo']}"
        oferta = int(b['precio_oferta'])
        pvp = int(b['precio_pvp'] or b['precio_oferta'])
        ahorro_str = f" <s>{pvp} €</s>" if pvp > oferta else ""
        url = b.get('url_oferta') or ""
        link_str = f"<a href='{url}'>{nombre}</a>" if url else nombre
        tienda = (b.get('tienda_nombre') or "Tienda")[:24]
        talla = b.get('talla_recomendada_169', 'S')

        msg += f"<b>{i}.</b> [{b['tier']}] <b>{b['nota']}/10</b> | {link_str}\n"
        msg += f"   💰 <b>{oferta} €</b>{ahorro_str} | 📏 Talla: <b>{talla}</b> | 📍 <i>{tienda}</i>\n"
        msg += f"   ⚙️ {b['transmision']} | {b['frenos']}\n\n"

    if total_encontradas > len(bikes_mostradas):
        msg += f"💡 <i>Hay {total_encontradas - len(bikes_mostradas)} modelos más en stock. Usa filtros como <code>/catalogo S+</code>, <code>/catalogo 1200</code> o <code>/chollazos</code> para afinar.</i>"
    else:
        msg += "💡 <i>Escribe <code>/ficha [nombre]</code> para ver componentes completos y dónde comprarla.</i>"
    return msg
