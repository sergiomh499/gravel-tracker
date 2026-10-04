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

def get_recommended_physical_stores(presupuesto: float = 1000.0, max_distancia_km: float = 5.0) -> List[Dict[str, Any]]:
    """
    Ordena y filtra las tiendas físicas de Madrid según cercanía y capacidad de oferta.
    """
    filtered = [s for s in MADRID_PHYSICAL_STORES if s["distancia_km"] <= max_distancia_km]
    # Ponderar por puntuación y proximidad
    filtered.sort(key=lambda s: (s["distancia_km"], -s["puntuacion_tienda"]))
    return filtered

def format_stores_recommendation_message() -> str:
    """Genera la guía recomendada de visita a tiendas físicas para Telegram o terminal."""
    stores = get_recommended_physical_stores()

    msg = "🏪 <b>TIENDAS FÍSICAS RECOMENDADAS PARA VISITAR (DESDE MÉNDEZ ÁLVARO)</b> 🏪\n\n"
    msg += "<i>Ruta optimizada para ver, probar talla y negociar gravels con ~1.000 €:</i>\n\n"

    for i, s in enumerate(stores, 1):
        corner = "🏷️ <b>Tiene zona Outlet</b>" if s["corner_outlet"] else "📦 Stock bajo pedido"
        marcas = ", ".join(s["marcas_clave"])
        msg += f"<b>{i}. {s['nombre']}</b> (⭐ {s['puntuacion_tienda']}/10)\n"
        msg += f"   📍 <i>{s['direccion']}</i>\n"
        msg += f"   🚶 <b>Distancia:</b> a {s['distancia_km']} km ({s['tiempo_llegada']})\n"
        msg += f"   🚲 <b>Marcas:</b> {marcas}\n"
        msg += f"   {corner}\n"
        msg += f"   💡 <b>Truco Pro:</b> {s['consejo_negociacion']}\n\n"

    msg += "🎯 <b>Estrategia Recomendada de Compra en Tienda:</b>\n"
    msg += "1. Visita primero <b>Sanferbike M-30</b> (está a 800m a pie de tu casa) para ver in situ la Megamo Jakar y la Orbea Terra.\n"
    msg += "2. Toma el Cercanías 3 min a <b>Calmera (Atocha)</b> para preguntar por disponibilidad de la Conor Kalima en talla SM.\n"
    msg += "3. Pide siempre que te igualen el precio del outlet online o incluyan pedales/tubelizado de regalo."
    return msg
