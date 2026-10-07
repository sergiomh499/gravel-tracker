"""
gravel_bot.scrapers.bicimarket - Scraper de Bicimarket España
Rastrea la categoría de bicicletas gravel en Bicimarket (Conor, Raymon, Kross, KTM, BH).
"""

import re
import json
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class BicimarketScraper(BaseScraper):
    name = "bicimarket"
    store_slug = "bicimarket_online"
    store_name = "Bicimarket Red Tiendas / Online"
    store_type = "online"
    base_url = "https://www.bicimarket.com/es/584-gravel"

    def scrape(self) -> List[Dict[str, Any]]:
        html_content = self.fetch_html(self.base_url)
        if not html_content:
            return []

        articles = re.findall(r'<article[^>]*class="[^"]*product-miniature[^"]*"[^>]*>(.*?)</article>', html_content, re.DOTALL)
        results = []

        for a in articles:
            # 1. Extracción mediante JSON-LD estructurado si existe
            js_m = re.search(r'<script type="application/ld\+json">(.*?)</script>', a, re.DOTALL)
            name = None
            price = None
            url = None

            if js_m:
                try:
                    data = json.loads(js_m.group(1), strict=False)
                    name = data.get("name")
                    offers = data.get("offers", {})
                    price = float(offers.get("price", 0))
                    url = offers.get("url")
                except Exception:
                    # Fallback a expresiones regulares sobre el JSON
                    name_m = re.search(r'"name":\s*"([^"]+)"', js_m.group(1))
                    pr_m = re.search(r'"price":\s*"?([\d\.]+)"?', js_m.group(1))
                    url_m = re.search(r'"url":\s*"([^"]+)"', js_m.group(1))
                    if name_m and pr_m:
                        name = name_m.group(1)
                        price = float(pr_m.group(1))
                        url = url_m.group(1) if url_m else ""

            # 2. Fallback HTML
            if not name or not price:
                t_m = re.search(r'class="[^"]*product-title[^"]*"[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', a)
                p_m = re.search(r'class="price[^"]*"[^>]*>([^<]+)</span>', a)
                if t_m and p_m:
                    url = t_m.group(1)
                    name = t_m.group(2).strip()
                    price = self.clean_price(p_m.group(1))

            if name and price and price >= 400.0:
                # PVP regular si está disponible
                reg_m = re.search(r'class="regular-price[^"]*"[^>]*>([^<]+)</span>', a)
                pvp = self.clean_price(reg_m.group(1)) if reg_m else price
                if pvp < price:
                    pvp = price

                # Tallas disponibles inferidas o estándar
                sizes = ["S", "M"]

                results.append({
                    "title": f"Bicicleta Gravel {name}" if "bicicleta" not in name.lower() else name,
                    "price": price,
                    "pvp": pvp,
                    "discount_str": f"{round((pvp - price) / pvp * 100)}%" if pvp > price else "0%",
                    "sizes": sizes,
                    "url": url or self.base_url,
                    "store_slug": self.store_slug,
                    "store_name": self.store_name,
                    "store_type": self.store_type
                })

        return results
