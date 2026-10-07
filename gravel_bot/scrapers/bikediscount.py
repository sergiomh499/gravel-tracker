"""
gravel_bot.scrapers.bikediscount - Scraper de Bike-Discount (Alemania / Envíos España)
Rastrea modelos de gravel directo de fabricante y liquidaciones (Radon, Cube, etc.).
"""

import re
import html as html_lib
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class BikeDiscountScraper(BaseScraper):
    """
    Scraper especializado en Bike-Discount para rastrear Radon REGARD y ofertas gravel.
    """
    name = "bike_discount"
    store_slug = "bike_discount"
    store_name = "Bike-Discount (Alemania / Envío España)"
    store_type = "online"
    base_url = "https://www.bike-discount.de/es/gravel_bikes"

    def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        html = self.fetch_html(self.base_url)
        if not html:
            return results

        # Extraer bloques con data-product-information o cards
        matches = re.finditer(
            r'data-product-information=\"([^\"]+)\".*?<a[^>]+href=\"(https://www\.bike-discount\.de/es/[^\"]+)\"[^>]*title=\"([^\"]+)\"',
            html,
            re.DOTALL
        )

        for m in matches:
            info_raw = html_lib.unescape(m.group(1))
            link = m.group(2)
            name = m.group(3).strip()

            price_m = re.search(r'\"price\":\s*([0-9\.]+)', info_raw)
            if price_m:
                price = float(price_m.group(1))
            else:
                continue

            # Filtrar bicicletas relevantes de gravel (Radon Regard, Cube Nuroad, etc.)
            name_lower = name.lower()
            if any(k in name_lower for k in ["regard", "nuroad", "revolt", "topstone", "grizl", "gravel"]):
                results.append({
                    "title": f"Bicicleta Gravel {name}",
                    "price": price,
                    "pvp": price,
                    "url": link,
                    "sizes": ["S", "50 cm"] if "regard" in name_lower else ["S", "XS"]
                })

        return results
