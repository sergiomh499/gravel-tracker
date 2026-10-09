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
            name_lower = name.lower()
            if any(w in name_lower for w in ['neumatico', 'neumático', 'cubierta', 'zapatilla', 'maillot', 'culotte', 'rueda', 'camara', 'cámara']):
                continue
            p_match = (
                re.search(r'class="price[^"]*"[^>]*>([^<]+)</span>', a) or
                re.search(r'bon-data-price="([^"]+)"', a) or
                re.search(r'(\d{3,4}[\.,]\d{2})\s*(?:&nbsp;)?€', a) or
                re.search(r'itemprop="price"\s*content="([1-9]\d{2,})"', a)
            )
            if not p_match:
                continue
            price = self.clean_price(p_match.group(1))
            if price < 400:
                continue
            # 3. PVP real
            reg_m = re.search(r'class="regular-price[^"]*"[^>]*>([^<]+)</span>', a) or re.search(r'class="regular-price-dis"[^>]*>([^<]+)</span>', a)
            pvp = self.clean_price(reg_m.group(1)) if reg_m else price
            if pvp < price:
                pvp = price

            # 4. Tallas reales detectadas
            size_matches = set(re.findall(r'class="bonattribute-btn[^"]*"[^>]*title="([^"]+)"', a) + re.findall(r'talla-([a-z0-9]+)', a, re.I))
            if not size_matches:
                size_matches = set(re.findall(r'\b(?:talla|size|t\.)\s*([a-z0-9]+)\b', f"{name} {link}", re.I))
            sizes = sorted([s.upper().strip() for s in size_matches if s.strip() and len(s.strip()) <= 4])
            disc_pct = round((pvp - price) / pvp * 100) if pvp > price else 0

            results.append({
                "title": name,
                "price": price,
                "pvp": pvp,
                "discount_str": f"{disc_pct}%" if disc_pct > 0 else "0%",
                "sizes": sizes,
                "url": link,
                "store_slug": self.store_slug,
                "store_name": self.store_name,
                "store_type": self.store_type
            })

        return results
