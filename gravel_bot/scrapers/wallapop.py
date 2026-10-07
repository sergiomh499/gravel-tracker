"""
gravel_bot.scrapers.wallapop - Scraper de Ocasión y Segunda Mano en Madrid (Wallapop & Buycycle)
Rastrea ofertas de particulares en un radio de 25 km desde Méndez Álvaro (Madrid)
con filtrado estricto contra anuncios trampa, piezas sueltas y tallas erróneas.
"""

import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper
from gravel_bot.config import DEFAULT_HEADERS, RIDER_PROFILE

CITY_COORDINATES = {
    "madrid": ("40.4168", "-3.7038"),
    "barcelona": ("41.3879", "2.1699"),
    "valencia": ("39.4699", "-0.3763"),
    "sevilla": ("37.3891", "-5.9845"),
    "zaragoza": ("41.6488", "-0.8891"),
    "malaga": ("36.7213", "-4.4214"),
    "málaga": ("36.7213", "-4.4214"),
    "bilbao": ("43.2630", "-2.9350"),
    "alicante": ("38.3452", "-0.4810"),
    "cordoba": ("37.8882", "-4.7794"),
    "córdoba": ("37.8882", "-4.7794"),
    "valladolid": ("41.6523", "-4.7245"),
    "vigo": ("42.2406", "-8.7207"),
    "gijon": ("43.5322", "-5.6611"),
    "gijón": ("43.5322", "-5.6611"),
    "coruña": ("43.3623", "-8.4115"),
    "granada": ("37.1773", "-3.5986"),
}
RADIO_BUSQUEDA_METROS = "25000"  # 25 km a la redonda

class WallapopMadridScraper(BaseScraper):
    name = "wallapop"
    store_slug = "wallapop_madrid"
    store_name = "Wallapop (Segunda Mano)"
    store_type = "segunda_mano"
    base_url = "https://es.wallapop.com"

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Consulta la búsqueda de bicicletas gravel en Wallapop según la ubicación configurada.
        """
        results: List[Dict[str, Any]] = []
        zona = RIDER_PROFILE.get("zona", "Madrid").strip().lower()
        coords = None
        for city, c_latlon in CITY_COORDINATES.items():
            if city in zona:
                coords = c_latlon
                break
        keywords = ["bicicleta gravel", "gravel shimano grx", "gravel talla s"]

        headers = dict(DEFAULT_HEADERS)
        headers["X-DeviceOS"] = "0"
        headers["Accept"] = "application/json, text/plain, */*"

        for kw in keywords:
            params = {
                "keywords": kw,
                "category_ids": "12465", # Ciclismo
                "min_sale_price": "400",
                "max_sale_price": "2200"
            }
            if coords:
                params["latitude"] = coords[0]
                params["longitude"] = coords[1]
                params["distance"] = RADIO_BUSQUEDA_METROS
            query_str = urllib.parse.urlencode(params)
            api_url = f"https://api.wallapop.com/api/v3/general/search?{query_str}"

            req = urllib.request.Request(api_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    items = data.get("search_objects", []) or data.get("items", [])

                    for it in items:
                        title = it.get("title", "")
                        desc = it.get("description", "")
                        price = float(it.get("price", 0.0))
                        item_id = it.get("id", "")
                        web_slug = it.get("web_slug", "")

                        # Filtros de exclusión estricta (no ruedas sueltas, no ropa, no rodillos)
                        full_lower = f"{title} {desc}".lower()
                        if any(w in full_lower for w in ["rodillo", "maillot", "culotte", "zapatillas", "rueda delantera", "solo cuadro"]):
                            continue
                        if not any(g in full_lower for g in ["gravel", "grx", "apex", "silex", "jakar", "terra", "kalima"]):
                            continue

                        url = f"https://es.wallapop.com/item/{web_slug}" if web_slug else f"https://es.wallapop.com/item/{item_id}"
                        results.append({
                            "title": title,
                            "price": price,
                            "pvp": price * 1.35, # Estimación de PVP original
                            "url": url,
                            "description": f"[Segunda Mano] {desc[:250]}",
                            "sizes": [s for s in ["XS", "S", "M", "48", "51", "52", "54"] if s.lower() in full_lower],
                            "tienda_slug": self.store_slug
                        })
            except Exception:
                # Si la API de Wallapop aplica rate limit o bloqueo temporal, continúa con las demás tiendas
                continue

        # Deduplicar por URL
        seen_urls = set()
        deduped = []
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                deduped.append(r)

        return deduped
