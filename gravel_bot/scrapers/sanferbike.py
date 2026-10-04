"""
gravel_bot.scrapers.sanferbike - Scraper para Sanferbike M-30 (Tienda local a 800m de Méndez Álvaro)
"""

import re
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class SanferbikeScraper(BaseScraper):
    name = "sanferbike"
    store_slug = "sanferbike_m30"
    store_name = "Sanferbike M-30"
    store_type = "fisica"
    base_url = "https://www.sanferbike.com/es/buscar?controller=search&s=bicicleta+gravel"

    def scrape(self) -> List[Dict[str, Any]]:
        html_content = self.fetch_html(self.base_url)
        if not html_content:
            return []

        wrappers = re.split(r'js-product-miniature-wrapper', html_content)[1:]
        results = []

        for w in wrappers:
            # 1. Enlaces y título
            links = re.findall(r'<a[^>]*href=\"([^\"]+)\"[^>]*>([^<]+)</a>', w)
            bike_links = [l for l in links if any(k in l[1] for k in ["Bicicleta", "Megamo", "Scott", "Orbea", "Trek", "Cannondale", "BMC"])]
            if not bike_links:
                continue

            link, raw_title = bike_links[0]
            title = self.clean_text(raw_title)

            # 2. Precio oferta
            price_m = re.search(r'class=\"product-price[^\"]*\"\s+content=\"([^\"]*)\"', w)
            if not price_m:
                continue
            price = self.clean_price(price_m.group(1))

            # 3. PVP original
            old_m = re.search(r'class=\"regular-price[^\"]*\">([^<]+)</span>', w)
            pvp = self.clean_price(old_m.group(1)) if old_m else price
            if pvp == 0.0 or pvp < price:
                pvp = price

            # 4. Tallas disponibles
            sizes = set(re.findall(r'talla-([a-z0-9]+)', w, re.IGNORECASE))

            # Filtrar si es bicicleta real
            if price > 400.0:
                results.append({
                    "title": title,
                    "price": price,
                    "pvp": pvp,
                    "discount_str": f"{round((pvp - price) / pvp * 100)}%" if pvp > price else "0%",
                    "sizes": [s.upper() for s in sizes],
                    "url": link,
                    "store_slug": self.store_slug,
                    "store_name": self.store_name,
                    "store_type": self.store_type
                })

        return results
