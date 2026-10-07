"""
gravel_bot.scrapers.cicloscorredor - Scraper de Ciclos Corredor (Vallecas / Madrid)
Tienda histórica a 2,2 km de Méndez Álvaro especializada en Bianchi, Merida Silex, Mendiz y Orbea.
"""

import re
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class CiclosCorredorScraper(BaseScraper):
    name = "ciclos_corredor"
    store_slug = "ciclos_corredor"
    store_name = "Ciclos Corredor Vallecas"
    store_type = "fisica"
    base_url = "https://cicloscorredor.com/es/busqueda?controller=search&s=gravel"

    def scrape(self) -> List[Dict[str, Any]]:
        html_content = self.fetch_html(self.base_url)
        if not html_content:
            return []

        cards = re.findall(r'<div[^>]*class="[^"]*product-thumb-container[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>', html_content, re.DOTALL)
        results = []

        for c in cards:
            t = re.search(r'<a[^>]+href="(/es/p/[^"]+)"[^>]*>\s*([^<]+)\s*</a>', c)
            p = re.search(r'([\d\.,]+)\s*€', c)

            if not t or not p:
                continue

            name = t.group(2).strip()
            link = "https://cicloscorredor.com" + t.group(1)
            price = self.clean_price(p.group(1))

            if price < 400.0:
                continue

            # Descartar e-bikes o componentes si no son gravel convencional
            name_lower = name.lower()
            if "e-bike" in name_lower or "plato" in name_lower or "maillot" in name_lower:
                continue

            # Buscar PVP o precio anterior
            old_p = re.search(r'class="regular-price[^"]*"[^>]*>([^<]+)</span>', c)
            pvp = self.clean_price(old_p.group(1)) if old_p else price
            if pvp < price:
                pvp = price

            # Tallas estimadas
            sizes = ["S", "M"]

            results.append({
                "title": name,
                "price": price,
                "pvp": pvp,
                "discount_str": f"{round((pvp - price) / pvp * 100)}%" if pvp > price else "0%",
                "sizes": sizes,
                "url": link,
                "store_slug": self.store_slug,
                "store_name": self.store_name,
                "store_type": self.store_type
            })

        return results
