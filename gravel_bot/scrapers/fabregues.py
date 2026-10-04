"""
gravel_bot.scrapers.fabregues - Scraper para Fabregues Bicicletas (Distribuidor Megamo, Orbea, Scott)
"""

import re
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class FabreguesScraper(BaseScraper):
    name = "fabregues"
    store_slug = "fabregues"
    store_name = "Fabregues Bicicletas"
    store_type = "online"
    base_url = "https://fabreguesbicicletas.com/es/bicicletas/bicicletas/gravel-cx"

    def scrape(self) -> List[Dict[str, Any]]:
        html_content = self.fetch_html(self.base_url)
        if not html_content:
            return []

        # En Fabregues, cada producto está envuelto en div con clase js-product-miniature-wrapper
        wrappers = re.split(r'<div class=\"js-product-miniature-wrapper', html_content)[1:]
        results = []

        for w in wrappers:
            # 1. Título y Enlace
            title_m = re.search(r'<h[23][^>]*class=\"[^\"]*product-title[^\"]*\"[^>]*>\s*<a[^>]*href=\"([^\"]+)\"[^>]*>([^<]+)</a>', w)
            if not title_m:
                continue

            link, raw_title = title_m.groups()
            title = self.clean_text(raw_title)

            # 2. Precio oferta
            price_m = re.search(r'<span\s+class=\"product-price\"[^>]*content=\"([^\"]*)\"[^>]*>', w)
            if price_m and price_m.group(1):
                price = self.clean_price(price_m.group(1))
            else:
                p_text_m = re.search(r'class=\"product-price\"[^>]*>\s*([0-9\.,]+)\s*€', w)
                price = self.clean_price(p_text_m.group(1)) if p_text_m else 0.0

            # 3. PVP original
            old_price_m = re.search(r'<span class=\"regular-price[^\"]*\">([^<]+)</span>', w)
            pvp = self.clean_price(old_price_m.group(1)) if old_price_m else price
            if pvp == 0.0 or pvp < price:
                pvp = price

            # 4. Descuento
            disc_m = re.search(r'<li class=\"product-flag discount\">([^<]+)</li>', w)
            discount_str = disc_m.group(1).strip() if disc_m else "0%"

            # 5. Tallas
            sizes = set(re.findall(r'talla-([a-z0-9]+)', w, re.IGNORECASE))
            sizes_list = [s.upper() for s in sizes]

            if price > 200: # Filtrar posibles accesorios o repuestos
                results.append({
                    "title": title,
                    "price": price,
                    "pvp": pvp,
                    "discount_str": discount_str,
                    "sizes": sorted(sizes_list),
                    "url": link,
                    "store_slug": self.store_slug,
                    "store_name": self.store_name,
                    "store_type": self.store_type
                })

        return results
