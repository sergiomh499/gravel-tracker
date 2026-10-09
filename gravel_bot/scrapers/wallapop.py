"""
gravel_bot.scrapers.wallapop - Scraper de Ocasión y Segunda Mano en Madrid (Wallapop & Buycycle)
Rastrea ofertas de particulares en un radio de 25 km desde Méndez Álvaro (Madrid)
con filtrado estricto contra anuncios trampa, piezas sueltas y tallas erróneas.
"""

import re
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
    max_pages: int = 2
    deep_pages: int = 5

    def scrape(self, deep: bool = False) -> List[Dict[str, Any]]:
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
        keywords = ["bicicleta gravel", "gravel"]

        headers = dict(DEFAULT_HEADERS)
        headers["X-DeviceOS"] = "0"
        headers["Accept"] = "application/json, text/plain, */*"
        headers["Origin"] = "https://es.wallapop.com"
        headers["Referer"] = "https://es.wallapop.com/"

        pages_to_fetch = self.deep_pages if deep else self.max_pages
        for kw in keywords:
            next_token = None
            for page_idx in range(pages_to_fetch):
                params = {
                    "keywords": kw,
                    "category_id": "17000", # Categoría Bicicletas
                    "source": "deep_link",
                    "order_by": "most_relevance",
                    "section_type": "organic_search_results"
                }
                if next_token:
                    params["next_page"] = next_token
                if coords:
                    params["latitude"] = coords[0]
                    params["longitude"] = coords[1]
                    params["distance"] = RADIO_BUSQUEDA_METROS
                query_str = urllib.parse.urlencode(params)
                api_url = f"https://api.wallapop.com/api/v3/search/section?{query_str}"

                req = urllib.request.Request(api_url, headers=headers)
                try:
                    with urllib.request.urlopen(req, timeout=10) as res:
                        data = json.loads(res.read().decode("utf-8"))
                        items = data.get("data", {}).get("section", {}).get("items", [])
                        next_token = data.get("meta", {}).get("next_page")
                    for it in items:
                        title = it.get("title", "")
                        desc = it.get("description", "")
                        price_obj = it.get("price", {})
                        price = float(price_obj.get("amount", 0.0) if isinstance(price_obj, dict) else (price_obj or 0.0))
                        if not (350 <= price <= 2500):
                            continue
                        item_id = it.get("id", "")
                        web_slug = it.get("web_slug", "")
                        # Filtros de exclusión estricta (no ruedas sueltas, no ropa, no rodillos)
                        full_lower = f"{title} {desc}".lower()
                        if any(w in full_lower for w in ["rodillo", "maillot", "culotte", "zapatillas", "rueda delantera", "solo cuadro"]):
                            continue
                        if not any(g in full_lower for g in ["gravel", "grx", "apex", "silex", "jakar", "terra", "kalima"]):
                            continue

                        url = f"https://es.wallapop.com/item/{web_slug}" if web_slug else f"https://es.wallapop.com/item/{item_id}"
                        found_sizes = set()
                        for sm in re.findall(r'\b(?:talla|size|t\.)\s*([xXsSmMlLeE0-9\/\-]+)\b', full_lower):
                            for token in re.split(r'[\s\/\-]+', sm.lower()):
                                if token in ["xxs", "xs", "s", "sm", "m", "md", "l", "lg", "xl", "xxl", "48", "49", "50", "51", "52", "53", "54", "55", "56", "58"]:
                                    found_sizes.add(token.upper())
                        if not found_sizes:
                            for token in ["xxs", "xs", "sm", "md", "xl", "xxl"]:
                                if re.search(rf'\b{token}\b', full_lower):
                                    found_sizes.add(token.upper())
                        if not found_sizes:
                            for num in ["48", "49", "50", "51", "52", "53", "54", "56"]:
                                if re.search(rf'(?:cuadro|talla|\b)\s*{num}\s*cm\b', full_lower):
                                    found_sizes.add(num)

                        sizes = sorted(list(found_sizes))
                        results.append({
                            "title": title,
                            "price": price,
                            "pvp": price * 1.35 if price > 0 else 0, # Estimación de PVP original
                            "url": url,
                            "description": f"[Segunda Mano] {desc[:250]}",
                            "sizes": sizes,
                            "tienda_slug": self.store_slug
                        })
                    if not next_token:
                        break
                except Exception:
                    break
        # Deduplicar por URL
        seen_urls = set()
        deduped = []
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                deduped.append(r)

        return deduped
