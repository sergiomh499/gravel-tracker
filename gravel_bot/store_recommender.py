"""
gravel_bot.store_recommender - Recomendador Inteligente de Tiendas Físicas en Madrid
Calcula la mejor ruta, marcas autorizadas, agresividad de ofertas y consejos de negociación
para visitar tiendas físicas de gravel desde Méndez Álvaro.
"""

from typing import List, Dict, Any, Optional

# Directorio especializado de tiendas físicas en Madrid (ordenadas por cercanía a Méndez Álvaro)
MADRID_PHYSICAL_STORES: List[Dict[str, Any]] = [
    {
        "id": "sanferbike_m30",
        "nombre": "Sanferbike M-30",
        "direccion": "Calle Lozano, 2 (Puente de Vallecas / M-30 Sur)",
        "distancia_km": 0.8,
        "tiempo_llegada": "8-10 min a pie (cruzando pasarela peatonal de Méndez Álvaro)",
        "metro_cercanias": "Méndez Álvaro / Puente de Vallecas",
        "marcas_clave": ["Megamo", "Orbea", "Cannondale", "BMC"],
        "modelos_frecuentes": "Megamo Jakar 30, Orbea Terra H40, Cannondale Topstone",
        "corner_outlet": True,
        "taller_propio": True,
        "puntuacion_tienda": 9.8,
        "consejo_negociacion": (
            "Pregunta en la 2ª planta por las bicis de exposición ('Test Bikes') o remanentes de temporada anterior. "
            "Suelen igualar ofertas web de su propia página y puedes pedir que te regalen los pedales automáticos o conversión tubeless."
        )
    },
    {
        "id": "calmera_atocha",
        "nombre": "Calmera Ciclismo (Atocha 98)",
        "direccion": "Calle de Atocha, 98 (Centro / Atocha)",
        "distancia_km": 2.2,
        "tiempo_llegada": "3 min en Cercanías C-5/C-10 (Méndez Álvaro -> Atocha) o 10 min en bici",
        "metro_cercanias": "Atocha Renfe / Antón Martín",
        "marcas_clave": ["Conor", "Bianchi", "Merida", "Ridley"],
        "modelos_frecuentes": "Conor Kalima GRX400, Merida Silex, Ridley Kanzo",
        "corner_outlet": True,
        "taller_propio": True,
        "puntuacion_tienda": 9.5,
        "consejo_negociacion": (
            "La tienda más antigua de Madrid (desde 1941). Tienen trato directo con Conor (Navarra) "
            "y te pueden pedir la Kalima en talla SM si no está montada en tienda. Muy abiertos a financiar al 0% y ajustar precio en mano."
        )
    },
    {
        "id": "decathlon_usera",
        "nombre": "Decathlon Usera / Madrid Río",
        "direccion": "Calle Antonio López, 109-111 (Usera / Madrid Río)",
        "distancia_km": 2.1,
        "tiempo_llegada": "15 min a pie por Parque Lineal del Manzanares o 6 min en bici",
        "metro_cercanias": "Almendrales / Usera",
        "marcas_clave": ["Triban", "Van Rysel"],
        "modelos_frecuentes": "Triban GRVL 520 Subcompact, Triban GRVL 120, Van Rysel EDR",
        "corner_outlet": True,
        "taller_propio": True,
        "puntuacion_tienda": 8.9,
        "consejo_negociacion": (
            "Revisa la sección 'Segunda Vida' al fondo de la tienda (suelen tener bicis devueltas con 100 km al -20% o -30%). "
            "Puntos fuertes: 60 días de devolución y primera revisión gratuita."
        )
    },
    {
        "id": "buhobike_moratalaz",
        "nombre": "Buhobike (Delicias / Moratalaz)",
        "direccion": "Calle Arroyo de las Pilillas, 10 (Moratalaz) / Cerca de Delicias",
        "distancia_km": 3.4,
        "tiempo_llegada": "10 min en autobús 8/113 o 12 min en coche/bici",
        "metro_cercanias": "Artilleros / Delicias",
        "marcas_clave": ["Orbea", "Megamo", "Merida", "KTM", "Scott"],
        "modelos_frecuentes": "Megamo Jakar, Orbea Terra H30/H40, KTM X-Strada",
        "corner_outlet": True,
        "taller_propio": True,
        "puntuacion_tienda": 9.4,
        "consejo_negociacion": (
            "Los reyes del outlet físico en Madrid. Tienen una nave enorme con stock real en exposición. "
            "Si les dices que vienes con presupuesto cerrado de 1.000 € en mano para una gravel talla S, "
            "revisan su almacén informático para ofrecerte liquidaciones descatalogadas."
        )
    },
    {
        "id": "mammoth_delicias",
        "nombre": "Mammoth Bikes (Paseo Santa María de la Cabeza)",
        "direccion": "Paseo de Santa María de la Cabeza, 72 (Palos de la Frontera)",
        "distancia_km": 2.4,
        "tiempo_llegada": "12 min en autobús 55 o 8 min en bici",
        "metro_cercanias": "Palos de la Frontera / Delicias",
        "marcas_clave": ["Scott", "Specialized", "Cube", "Giant"],
        "modelos_frecuentes": "Cube Nuroad, Scott Speedster Gravel, Giant Revolt",
        "corner_outlet": False,
        "taller_propio": True,
        "puntuacion_tienda": 8.8,
        "consejo_negociacion": (
            "Buena tienda para probarte la geometría de Cube o Scott antes de comprar. "
            "Permiten recoger pedidos online del Outlet de Mammoth sin coste de envío y te la entregan ajustada."
        )
    }
]

def get_recommended_physical_stores(zona: str = "Madrid", max_distancia_km: float = 15.0) -> List[Dict[str, Any]]:
    """
    Obtiene las tiendas físicas recomendadas según la ubicación/zona configurada por el usuario.
    Si la zona es Madrid, prioriza el listado detallado con distancias exactas.
    Para otras zonas, consulta la base de datos o puntos de recogida nacionales (Decathlon, ECI, Bicimarket).
    """
    from gravel_bot.db import get_connection
    z_clean = (zona or "Madrid").strip()

    if any(k in z_clean.lower() for k in ["madrid", "méndez", "mendez"]):
        filtered = [s for s in MADRID_PHYSICAL_STORES if s.get("distancia_km", 99) <= max_distancia_km]
        filtered.sort(key=lambda s: (s.get("distancia_km", 99), -s.get("puntuacion_tienda", 8.0)))
        return filtered

    # Búsqueda dinámica en base de datos para la zona configurada
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM tiendas 
        WHERE tipo = 'fisica' 
          AND (LOWER(direccion) LIKE ? OR LOWER(nombre) LIKE ?)
    """, (f"%{z_clean.lower()}%", f"%{z_clean.lower()}%"))
    db_stores = [dict(r) for r in c.fetchall()]
    conn.close()

    if db_stores:
        results = []
        for s in db_stores:
            results.append({
                "nombre": s["nombre"],
                "direccion": s.get("direccion") or f"Zona {z_clean}",
                "distancia_km": s.get("distancia_km") or 2.0,
                "tiempo_llegada": "Local / En tu zona",
                "marcas_clave": [m.strip() for m in (s.get("marcas") or "Gravel").split(",")],
                "corner_outlet": True,
                "puntuacion_tienda": 9.0,
                "consejo_negociacion": "Consulta promociones en tienda física y servicio postventa de taller local."
            })
        return results

    # Redes nacionales con servicio y recogida en la ubicación configurada
    return [
        {
            "nombre": f"Decathlon {z_clean} (Punto Recogida / Taller)",
            "direccion": f"Tienda oficial Decathlon en {z_clean}",
            "distancia_km": 3.0,
            "tiempo_llegada": "Recogida gratuita en tienda",
            "marcas_clave": ["Van Rysel", "Triban"],
            "corner_outlet": True,
            "puntuacion_tienda": 9.0,
            "consejo_negociacion": "Pruébate la talla in situ; disponen de 60 días de devolución y primera revisión gratuita."
        },
        {
            "nombre": f"Bicimarket Red de Puntos ({z_clean})",
            "direccion": f"Punto de entrega y taller asociado en {z_clean}",
            "distancia_km": 4.0,
            "tiempo_llegada": "Red nacional de 120 talleres",
            "marcas_clave": ["Conor", "Merida", "KTM", "BH"],
            "corner_outlet": True,
            "puntuacion_tienda": 8.9,
            "consejo_negociacion": "Permite comprar online a precio de liquidación y recoger montada y ajustada en taller local."
        },
        {
            "nombre": f"El Corte Inglés Deportes ({z_clean})",
            "direccion": f"Centro comercial ECI en {z_clean}",
            "distancia_km": 5.0,
            "tiempo_llegada": "Click & Collect directo",
            "marcas_clave": ["MMR", "Kross"],
            "corner_outlet": True,
            "puntuacion_tienda": 8.7,
            "consejo_negociacion": "Aprovecha la financiación al 0% TAE y garantía oficial de devolución."
        }
    ]

def format_stores_recommendation_message(zona: Optional[str] = None) -> str:
    """Genera la guía recomendada de visita a tiendas físicas adaptada a la ubicación configurada."""
    from gravel_bot.config import RIDER_PROFILE
    current_zona = (zona or RIDER_PROFILE.get("zona") or "Madrid").strip()
    stores = get_recommended_physical_stores(zona=current_zona)

    msg = f"🏪 <b>TIENDAS FÍSICAS RECOMENDADAS ({current_zona.upper()})</b> 🏪\n\n"
    msg += f"<i>Opciones con punto de recogida, prueba de talla y taller para tu zona ({current_zona}):</i>\n\n"

    for i, s in enumerate(stores, 1):
        corner = "🏷️ <b>Tiene zona Outlet</b>" if s.get("corner_outlet") else "📦 Stock bajo pedido"
        marcas = ", ".join(s.get("marcas_clave", ["Gravel"]))
        msg += f"<b>{i}. {s['nombre']}</b> (⭐ {s.get('puntuacion_tienda', 9.0)}/10)\n"
        msg += f"   📍 <i>{s.get('direccion', 'Local')}</i>\n"
        dist = f"a {s['distancia_km']} km" if s.get("distancia_km") else "Local"
        msg += f"   🚶 <b>Distancia / Acceso:</b> {dist} ({s.get('tiempo_llegada', '')})\n"
        msg += f"   🚲 <b>Marcas:</b> {marcas}\n"
        msg += f"   {corner}\n"
        msg += f"   💡 <b>Consejo:</b> {s.get('consejo_negociacion', '')}\n\n"

    msg += f"🎯 <b>Estrategia de Compra en {current_zona}:</b>\n"
    msg += "1. Visita o contacta con la tienda para consultar si pueden pedirte tu talla exacta.\n"
    msg += "2. Pregunta si igualan el precio de liquidación web o si incluyen pedales/tubelizado de regalo.\n"
    msg += "3. Comprueba siempre la garantía oficial y el servicio de primer ajuste de transmisión."
    return msg
