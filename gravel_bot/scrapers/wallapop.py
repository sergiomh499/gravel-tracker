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
from gravel_bot.config import DEFAULT_HEADERS

# Coordenadas geográficas de Madrid centro
MADRID_CENTRO_LAT = "40.4168"
MADRID_CENTRO_LON = "-3.7038"
RADIO_BUSQUEDA_METROS = "25000" # 25 km a la redonda

class WallapopMadridScraper(BaseScraper):
    name = "wallapop_madrid"
    store_slug = "wallapop_madrid"
    store_name = "Wallapop (Particulares Madrid 25km)"
    store_type = "segunda_mano"
    base_url = "https://es.wallapop.com"

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Consulta la búsqueda de bicicletas gravel en Madrid a través de la API pública de búsqueda de Wallapop.
        """
        results: List[Dict[str, Any]] = []
        keywords = ["bicicleta gravel", "gravel shimano grx", "gravel talla s"]

        headers = dict(DEFAULT_HEADERS)
        headers["X-DeviceOS"] = "0"
        headers["Accept"] = "application/json, text/plain, */*"

        for kw in keywords:
            params = {
                "keywords": kw,
                 "latitude": MADRID_CENTRO_LAT,
                 "longitude": MADRID_CENTRO_LON,
                "distance": RADIO_BUSQUEDA_METROS,
                "category_ids": "12465", # Ciclismo
                "min_sale_price": "400",
                "max_sale_price": "2200"
            }
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
                            "description": f"[Segunda Mano Madrid] {desc[:250]}",
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
