"""
gravel_bot.geocoder - Geocodificación Inversa Ligera y Detección de Ubicación
Resuelve coordenadas GPS (latitud y longitud) a la ciudad de referencia más cercana mediante Haversine.
"""

import math
from typing import Tuple, Dict

SPAIN_CITIES: Dict[str, Tuple[float, float]] = {
    "Madrid": (40.4168, -3.7038),
    "Barcelona": (41.3879, 2.1699),
    "Valencia": (39.4699, -0.3763),
    "Sevilla": (37.3891, -5.9845),
    "Zaragoza": (41.6488, -0.8891),
    "Málaga": (36.7213, -4.4214),
    "Bilbao": (43.2630, -2.9350),
    "Alicante": (38.3452, -0.4810),
    "Córdoba": (37.8882, -4.7794),
    "Valladolid": (41.6523, -4.7245),
    "Vigo": (42.2406, -8.7207),
    "Gijón": (43.5322, -5.6611),
    "A Coruña": (43.3623, -8.4115),
    "Granada": (37.1773, -3.5986),
    "Murcia": (37.9922, -1.1307),
    "Palma de Mallorca": (39.5696, 2.6502),
    "Las Palmas": (28.1235, -15.4363),
    "Santa Cruz de Tenerife": (28.4636, -16.2518),
    "Santander": (43.4623, -3.8099),
    "Pamplona": (42.8125, -1.6458),
    "San Sebastián": (43.3183, -1.9812),
    "Toledo": (39.8628, -4.0273),
    "Badajoz": (38.8794, -6.9706),
    "Salamanca": (40.9701, -5.6635),
    "Burgos": (42.3439, -3.6969),
    "Almería": (36.8381, -2.4597),
    "Cádiz": (36.5271, -6.2886),
    "Huelva": (37.2614, -6.9447),
    "Logroño": (42.4627, -2.4449),
    "Ourense": (42.3358, -7.8639),
    "Lugo": (43.0097, -7.5560),
    "Girona": (41.9794, 2.8214),
    "Tarragona": (41.1189, 1.2445),
    "Lleida": (41.6176, 0.6200),
    "Castellón": (39.9864, -0.0513),
}

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia ortodrómica en kilómetros entre dos coordenadas usando la fórmula Haversine."""
    r_tierra = 6371.0  # Radio medio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return round(r_tierra * c, 1)

def resolve_closest_city(lat: float, lon: float) -> Tuple[str, float]:
    """
    Encuentra la ciudad española más cercana para unas coordenadas GPS y la distancia en km.
    """
    closest_city = "Madrid"
    min_dist = float("inf")
    for city, (c_lat, c_lon) in SPAIN_CITIES.items():
        dist = haversine_distance_km(lat, lon, c_lat, c_lon)
        if dist < min_dist:
            min_dist = dist
            closest_city = city
    return closest_city, min_dist
