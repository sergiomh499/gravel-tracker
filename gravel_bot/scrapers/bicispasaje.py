"""
gravel_bot.scrapers.bicispasaje - Scraper de Bicispasaje
Rastrea ofertas de gravel (Megamo Jakar, MMR, Conor, Stevens, Mendiz) en Bicispasaje.
"""

import re
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class BicispasajeScraper(BaseScraper):
    name = "bicispasaje"
    store_slug = "bicispasaje_online"
    store_name = "Bicispasaje Outlet Ciclismo"
    store_type = "online"
    base_url = "https://www.bicispasaje.es/es/buscar?controller=search&s=bicicleta+gravel"

    def scrape(self) -> List[Dict[str, Any]]:
        html_content = self.fetch_html(self.base_url)
        if not html_content:
            return []

        articles = re.findall(r'<article[^>]*class="[^"]*product-miniature[^"]*"[^>]*>(.*?)</article>', html_content, re.DOTALL)
        results = []

        for a in articles:
            t = re.search(r'class="[^"]*product-title[^"]*"[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', a)
            p = re.search(r'itemprop="price"\s*class="price">([^<]+)</span>', a) or re.search(r'class="price[^"]*"[^>]*>([^<]+)</span>', a)

            if not t or not p:
                continue

            link = t.group(1)
            name = t.group(2).strip()
            price = self.clean_price(p.group(1))

            if price < 400.0:
                continue

            reg_p = re.search(r'class="regular-price[^"]*"[^>]*>([^<]+)</span>', a)
            pvp = self.clean_price(reg_p.group(1)) if reg_p else price
            if pvp < price:
                pvp = price

            # Tallas
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
