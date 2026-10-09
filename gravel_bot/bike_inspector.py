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
        dist_str = f" (~{distancia} km)" if distancia else ""
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
    tallas_disp = bike.get('tallas_disponibles')
    if tallas_disp and tallas_disp not in ["Consultar tienda", ""]:
        msg += f" • <b>Tallas en Stock:</b> <code>{tallas_disp}</code>\n"
    # Sección 3: Valoración y Rúbrica
    msg += f"\n🏆 <b>VALORACIÓN Y RÚBRICA CALIBRADA C1..C6:</b>\n"
    msg += f" • <b>Clasificación:</b> <b>{bike.get('tier', 'Tier S')}</b>\n"
    msg += f" • <b>Puntuación Global:</b> <b>{bike.get('nota', 0.0)} / 10</b> ({bike.get('puntuacion_total', 0)}/100 pts)\n"
    msg += f"   - C1 Frenos (25 pts): <code>{bike.get('c1_frenos', 0)}/25</code>\n"
    msg += f"   - C2 Transmisión 50/50 (25 pts): <code>{bike.get('c2_transmision', 0)}/25</code>\n"
    msg += f"   - C3 Cuadro & Horquilla (20 pts): <code>{bike.get('c3_cuadro', 0)}/20</code>\n"
    msg += f"   - C4 Relación Precio VFM (20 pts): <code>{bike.get('c4_precio', 0)}/20</code>\n"
    msg += f"   - C5 Talla 1,69 m (10 pts): <code>{bike.get('c5_talla', 0)}/10</code>\n"
    c6_val = float(bike.get('c6_garantia') or 0.0)
    msg += f"   - C6 Garantía & Canal (+5 pts bonus): <code>+{c6_val:.1f}/5</code>\n"
    if bike.get('especificaciones_verificadas'):
        msg += " • 🛡️ <i>Especificaciones verificadas contra matriz de autoridad técnica</i>\n"
    if bike.get('audit_status'):
        status_icon = "✅ Verificado en stock" if bike.get('audit_status') == "verificado" else ("⚠️ Sin stock" if bike.get('audit_status') == "sin_stock" else f"🔍 {str(bike.get('audit_status')).capitalize()}")
        fecha_aud = f" ({bike.get('fecha_auditoria')})" if bike.get('fecha_auditoria') else ""
        msg += f" • 🌐 <i>Estado de Enlace: {status_icon}{fecha_aud}</i>\n"
    if bike.get('notas_veredicto'):
        msg += f" • <i>Veredicto: {bike['notas_veredicto']}</i>\n"
    # Sección 4: Estadísticas de precio
    msg += f"\n📊 <b>ESTADÍSTICAS HISTÓRICAS DEL MODELO:</b>\n"
    msg += f" • Mínimo histórico detectado: <b>{int(bike['min_historico'])} €</b>\n"
    msg += f" • Máximo registrado: <b>{int(bike['max_historico'])} €</b>\n"
    msg += f" • Fluctuaciones registradas: <b>{bike['historial_conteo']}</b> registros acumulados\n"

    return msg
format_bike_inspection_message = format_detailed_bike_card

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

def get_available_bikes_list(
    tier: Optional[str] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    transmission: Optional[str] = None,
    brakes: Optional[str] = None,
    size: Optional[str] = None,
    store_type: Optional[str] = None
) -> List[Dict[str, Any]]:
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

    if transmission:
        tr_low = transmission.lower().strip()
        if tr_low in ["1x", "monoplato", "mono"]:
            query += " AND b.tipo_transmision LIKE '1x%'"
        elif tr_low in ["2x", "biplato", "doble", "dobleplato"]:
            query += " AND b.tipo_transmision LIKE '2x%'"

    if brakes:
        br_low = brakes.lower().strip()
        if br_low in ["hidraulico", "hidraulicos", "hydraulic"]:
            query += " AND b.tipo_frenos = 'hidraulico'"
        elif br_low in ["mecanico", "mecanicos"]:
            query += " AND b.tipo_frenos IN ('mecanico_mono', 'mecanico_doble')"
        elif br_low in ["semihidraulico", "semi"]:
            query += " AND b.tipo_frenos = 'semihidraulico'"

    if size:
        from gravel_bot.geometry_sizing import extract_size_tokens
        size_tokens = extract_size_tokens(size)
        if size_tokens:
            size_clauses = []
            for tok in size_tokens:
                size_clauses.append("LOWER(COALESCE(b.tallas_disponibles, '')) LIKE ?")
                params.append(f"%{tok}%")
                size_clauses.append("LOWER(b.talla_recomendada_169) LIKE ?")
                params.append(f"%{tok}%")
            query += f" AND ({' OR '.join(size_clauses)})"
        else:
            query += " AND (LOWER(COALESCE(b.tallas_disponibles, '')) LIKE ? OR LOWER(b.talla_recomendada_169) LIKE ?)"
            params.extend([f"%{size.lower()}%", f"%{size.lower()}%"])
    if store_type:
        st_low = store_type.lower().strip()
        if any(w in st_low for w in ["ocasion", "cert", "reacond", "segunda"]):
            query += " AND t.tipo IN ('ocasion_certificada', 'segunda_mano_certificada', 'segunda_mano')"
        else:
            query += " AND t.tipo = ?"
            params.append(store_type)


    query += " ORDER BY b.nota DESC, b.precio_oferta ASC"
    c.execute(query, tuple(params))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_paged_available_bikes_payload(
    tier: Optional[str] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    transmission: Optional[str] = None,
    brakes: Optional[str] = None,
    size: Optional[str] = None,
    store_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 6
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Retorna el texto formateado de la página de bicicletas y el InlineKeyboardMarkup para paginar interactivamente.
    """
    bikes = get_available_bikes_list(
        tier=tier,
        max_price=max_price,
        brand=brand,
        transmission=transmission,
        brakes=brakes,
        size=size,
        store_type=store_type
    )
    if not bikes:
        return "ℹ️ No se encontraron bicicletas disponibles en stock con los filtros indicados.", None

    total = len(bikes)
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = max(1, min(page, total_pages))

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    slice_bikes = bikes[start_idx:end_idx]

    filtros = []
    if transmission:
        t_desc = "Monoplato (1x)" if transmission.lower() in ["1x", "monoplato", "mono"] else "Biplato (2x)"
        filtros.append(f"⚙️ {t_desc}")
    if brakes:
        b_desc = "Frenos Hidráulicos" if brakes.lower() in ["hidraulico", "hidraulicos"] else "Frenos Mecánicos"
        filtros.append(f"🛑 {b_desc}")
    if tier:
        filtros.append(f"Tier: {tier}")
    if max_price:
        filtros.append(f"Máx: {int(max_price)} €")
    if brand:
        filtros.append(f"Marca: {brand.capitalize()}")
    filtros_str = f" ({', '.join(filtros)})" if filtros else ""

    msg = f"🚲 <b>BICICLETAS DISPONIBLES EN STOCK{filtros_str}</b>\n"
    msg += f"<i>Mostrando {start_idx + 1}–{end_idx} de {total} modelos | Página {current_page} de {total_pages}</i>\n\n"

    for i, b in enumerate(slice_bikes, start=start_idx + 1):
        nombre = f"{b['marca']} {b['modelo']}"
        oferta = int(b['precio_oferta'])
        pvp = int(b['precio_pvp'] or b['precio_oferta'])
        ahorro_str = f" <s>{pvp} €</s>" if pvp > oferta else ""
        url = b.get('url_oferta') or ""
        link_str = f"<a href='{url}'>{nombre}</a>" if url else nombre
        tienda = (b.get('tienda_nombre') or "Tienda")[:24]
        talla = b.get('talla_recomendada_169', 'S')
        tallas_disp = b.get('tallas_disponibles')
        talla_tag = f"<b>{talla}</b>"
        if tallas_disp and tallas_disp not in ["Consultar tienda", "", talla]:
            talla_tag += f" <i>(Stock: {tallas_disp})</i>"

        msg += f"<b>{i}.</b> [{b['tier']}] <b>{b['nota']}/10</b> | {link_str}\n"
        msg += f"   💰 <b>{oferta} €</b>{ahorro_str} | 📏 Talla: {talla_tag} | 📍 <i>{tienda}</i>\n"
        msg += f"   ⚙️ {b['transmision']} | {b['frenos']}\n\n"

    # Construir teclado de paginación inline
    keyboard_rows = []
    nav_row = []
    t_token = tier or "_"
    p_token = str(int(max_price)) if max_price else "_"
    tr_token = transmission or "_"

    if current_page > 1:
        nav_row.append({"text": "⬅️ Anterior", "callback_data": f"/page:{current_page - 1}:{t_token}:{p_token}:{tr_token}"})
    nav_row.append({"text": f"📄 {current_page}/{total_pages}", "callback_data": f"/page:{current_page}:{t_token}:{p_token}:{tr_token}"})
    if current_page < total_pages:
        nav_row.append({"text": "Siguiente ➡️", "callback_data": f"/page:{current_page + 1}:{t_token}:{p_token}:{tr_token}"})

    if nav_row:
        keyboard_rows.append(nav_row)

    filter_row = [
        {"text": "⭐ Tier S+", "callback_data": f"/page:1:Tier S+:{p_token}:{tr_token}"},
        {"text": "⚙️ 2x", "callback_data": f"/page:1:{t_token}:{p_token}:2x"},
        {"text": "⚙️ 1x", "callback_data": f"/page:1:{t_token}:{p_token}:1x"}
    ]
    keyboard_rows.append(filter_row)

    reply_markup = {"inline_keyboard": keyboard_rows} if keyboard_rows else None
    return msg, reply_markup

def format_available_bikes_message(
    tier: Optional[str] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    transmission: Optional[str] = None,
    brakes: Optional[str] = None,
    size: Optional[str] = None,
    store_type: Optional[str] = None
) -> str:
    """
    Formatea la lista de bicicletas disponibles en stock para consulta rápida.
    """
    msg, _ = get_paged_available_bikes_payload(
        tier=tier,
        max_price=max_price,
        brand=brand,
        transmission=transmission,
        brakes=brakes,
        size=size,
        store_type=store_type,
        page=1,
        page_size=10
    )
    return msg

def format_bike_comparison_message(query1: str, query2: str, estatura_cm: int = 169) -> str:
    """Genera una comparación directa 1v1 frente a frente entre dos bicicletas."""
    b1 = get_detailed_bike_info(query1)
    b2 = get_detailed_bike_info(query2)
    if not b1 or not b2:
        missing = []
        if not b1:
            missing.append(f"'{query1}'")
        if not b2:
            missing.append(f"'{query2}'")
        return f"⚠️ No se encontró en el catálogo: {', '.join(missing)}.\nPrueba con: <code>/vs kalima jakar</code> o <code>/vs raymon x-grip</code>"
    from gravel_bot.geometry_sizing import get_recommended_size_dynamic
    talla1 = get_recommended_size_dynamic(b1["marca"], b1["modelo"], estatura_cm)["talla_recomendada"]
    talla2 = get_recommended_size_dynamic(b2["marca"], b2["modelo"], estatura_cm)["talla_recomendada"]

    msg = f"⚔️ <b>COMPARATIVA 1v1 FRENTE A FRENTE</b> ⚔️\n\n"
    msg += f"🅰️ <b>{b1['marca']} {b1['modelo']}</b>\n"
    msg += f" • <b>Precio:</b> {int(b1['precio_oferta'])} € (PVP: {int(b1.get('precio_pvp') or b1['precio_oferta'])} €)\n"
    msg += f" • <b>Tier / Nota:</b> {b1['tier']} | <b>{b1['nota']}/10</b>\n"
    msg += f" • <b>Transmisión:</b> {b1['transmision']}\n"
    msg += f" • <b>Frenos:</b> {b1['frenos']}\n"
    msg += f" • <b>Talla para {estatura_cm} cm:</b> <b>{talla1}</b>\n\n"

    msg += f"🅱️ <b>{b2['marca']} {b2['modelo']}</b>\n"
    msg += f" • <b>Precio:</b> {int(b2['precio_oferta'])} € (PVP: {int(b2.get('precio_pvp') or b2['precio_oferta'])} €)\n"
    msg += f" • <b>Tier / Nota:</b> {b2['tier']} | <b>{b2['nota']}/10</b>\n"
    msg += f" • <b>Transmisión:</b> {b2['transmision']}\n"
    msg += f" • <b>Frenos:</b> {b2['frenos']}\n"
    msg += f" • <b>Talla para {estatura_cm} cm:</b> <b>{talla2}</b>\n\n"

    msg += "🎯 <b>DUELO TÉCNICO:</b>\n"
    # Duelo transmisión
    t1_lower = b1['transmision'].lower()
    t2_lower = b2['transmision'].lower()
    if "2x" in t1_lower and "1x" in t2_lower:
        msg += f" • <b>Asfalto (50%):</b> Gana 🅰️ ({b1['marca']}) por biplato 2x con saltos cerrados.\n"
        msg += f" • <b>Pista / Baches (50%):</b> Gana 🅱️ ({b2['marca']}) por simplicidad y retención 1x.\n"
    elif "1x" in t1_lower and "2x" in t2_lower:
        msg += f" • <b>Asfalto (50%):</b> Gana 🅱️ ({b2['marca']}) por biplato 2x con saltos cerrados.\n"
        msg += f" • <b>Pista / Baches (50%):</b> Gana 🅰️ ({b1['marca']}) por simplicidad y retención 1x.\n"
    else:
        msg += f" • <b>Transmisión:</b> Ambas montan arquitectura similar ({b1['transmision'][:25]} vs {b2['transmision'][:25]}).\n"

    # Duelo frenos
    h1 = "hidr" in b1['frenos'].lower()
    h2 = "hidr" in b2['frenos'].lower()
    if h1 and not h2:
        msg += f" • <b>Frenada:</b> 🅰️ Gana con contundencia (Hidráulicos vs Mecánicos en 🅱️).\n"
    elif not h1 and h2:
        msg += f" • <b>Frenada:</b> 🅱️ Gana con contundencia (Hidráulicos vs Mecánicos en 🅰️).\n"

    # Diferencia precio
    diff_p = b1['precio_oferta'] - b2['precio_oferta']
    if diff_p < 0:
        msg += f" • <b>Diferencia:</b> 🅰️ es {int(abs(diff_p))} € más barata.\n"
    elif diff_p > 0:
        msg += f" • <b>Diferencia:</b> 🅱️ es {int(diff_p)} € más barata.\n"

    ganador = b1['marca'] if b1['nota'] >= b2['nota'] else b2['marca']
    msg += f"\n🏆 <b>Veredicto Global:</b> Por balance general recomendamos <b>{ganador}</b>."
    return msg
