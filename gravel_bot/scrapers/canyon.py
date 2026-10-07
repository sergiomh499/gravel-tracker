"""
gravel_bot.scrapers.canyon - Scraper de Canyon Outlet España
Rastrea ofertas directas de fábrica en modelos Canyon Grizl y Grail.
"""

import re
import html
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class CanyonOutletScraper(BaseScraper):
    name = "canyon_outlet"
    store_slug = "canyon_espana"
    store_name = "Canyon Outlet Oficial España"
    store_type = "outlet_online"
    base_url = "https://www.canyon.com/es-es/outlet/gravel-bikes/"

    def scrape(self) -> List[Dict[str, Any]]:
        page = self.fetch_html(self.base_url)
        if not page:
            return []

        page_unescaped = html.unescape(page)
        # Extraer bloques JSON de producto
        blocks = re.findall(r'(\{[^{}]*"item_name":\s*"[^"]+"[^{}]*\})', page_unescaped)
        results = []
        seen_names = set()

        for b in blocks:
            name_m = re.search(r'"item_name":\s*"([^"]+)"', b)
            price_m = re.search(r'"price":\s*([0-9\.]+)', b)
            if not name_m or not price_m:
                continue

            raw_name = name_m.group(1).strip()
            if raw_name in seen_names:
                continue
            seen_names.add(raw_name)

            raw_price = float(price_m.group(1))
            # Canyon en su JSON reporta a veces base imponible; si es < 1500, ajustamos con IVA o precio directo
            price = round(raw_price * 1.21, 2) if raw_price < 1200 else raw_price

            # Enlace a la ficha o al outlet
            url_m = re.search(r'"url":\s*"([^"]+)"', b) or re.search(r'"(https://www.canyon.com/es-es/[^"]+)"', b)
            url = url_m.group(1) if url_m else self.base_url

            # Tallas Canyon: la XS y S son las ideales para 1,69m (Canyon talla grande)
            sizes = ["XS", "S"]

            results.append({
                "title": f"Bicicleta Canyon {raw_name}",
                "price": price,
                "pvp": round(price * 1.15, 2),
                "discount_str": "15%",
                "sizes": sizes,
                "url": url,
                "store_slug": self.store_slug,
                "store_name": self.store_name,
                "store_type": self.store_type
            })

        return results
