"""
gravel_bot.scrapers.bikestocks - Scraper de Bikestocks Ciclismo
Almacén logístico en San Fernando de Henares (Madrid) y tienda online (BH, Orbea, Conor, Stevens).
"""

import re
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class BikestocksScraper(BaseScraper):
    name = "bikestocks"
    store_slug = "bikestocks_online"
    store_name = "Bikestocks Ciclismo"
    store_type = "online"
    base_url = "https://www.bikestocks.es/buscar?controller=search&s=gravel"

    def scrape(self) -> List[Dict[str, Any]]:
        html_content = self.fetch_html(self.base_url)
        if not html_content:
            return []

        articles = re.findall(r'<article[^>]*class="[^"]*product-miniature[^"]*"[^>]*>(.*?)</article>', html_content, re.DOTALL)
        results = []

        for a in articles:
            # 1. Enlace y título
            l_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*thumbnail[^"]*"', a) or re.search(r'itemprop="url"\s*href="([^"]+)"', a)
            t_match = re.search(r'alt="([^"]*GRAVEL[^"]*)"', a, re.I) or re.search(r'>([^<]*GRAVEL[^<]*)</a>', a, re.I)

            if not l_match or not t_match:
                continue

            link = l_match.group(1)
            raw_name = t_match.group(1).strip()
            name = re.sub(r'\s+data-[a-zA-Z\-]+=.*$', '', raw_name).strip()

            # 2. Precio desde bon-data-price o itemprop price
            p_match = re.search(r'bon-data-price="([^"]+)"', a) or re.search(r'class="regular-price-dis"[^>]*>([^<]+)</span>', a) or re.search(r'(\d+[\.,]\d{2})\s*€', a)
            if not p_match:
                continue

            price = self.clean_price(p_match.group(1))
            if price < 400.0:
                continue

            # Tallas detectadas en los botones de atributos
            size_matches = re.findall(r'class="bonattribute-btn[^"]*"[^>]*title="([^"]+)"', a)
            sizes = [s.strip().upper() for s in size_matches if s.strip()] or ["S", "M"]

            pvp = round(price * 1.15, 2)

            results.append({
                "title": name,
                "price": price,
                "pvp": pvp,
                "discount_str": "15%",
                "sizes": sizes,
                "url": link,
                "store_slug": self.store_slug,
                "store_name": self.store_name,
                "store_type": self.store_type
            })

        return results
