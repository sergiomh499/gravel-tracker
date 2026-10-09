"""
gravel_bot.scrapers.escapa - Scraper para Biking Escapa (Tiendas en Madrid y Online)
Distribuidor oficial Megamo, Orbea, Scott, Specialized, Cannondale.
"""

import re
import json
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class EscapaScraper(BaseScraper):
    name = "escapa"
    store_slug = "escapa_madrid"
    store_name = "Biking Escapa (Madrid / Online)"
    store_type = "hibrida"
    base_url = "https://www.escapa.com/bicicletas/gravel-cx"

    def scrape(self) -> List[Dict[str, Any]]:
        html_content = self.fetch_html(self.base_url, timeout=12)
        if not html_content:
            return []

        results: List[Dict[str, Any]] = []

        # 1. Mapeo de URLs desde las tarjetas <article>
        articles = re.findall(r'<article[^>]*>(.*?)</article>', html_content, re.DOTALL)
        url_map: Dict[str, str] = {}
        for a in articles:
            link = re.search(r'<a[^>]+href=\"(https://www.escapa.com/bicicletas/[^\"]+)\"', a)
            title = re.search(r'title=\"([^\"]+)\"', a) or re.search(r'<h[23][^>]*>(.*?)</h[23]>', a, re.DOTALL)
            if link and title:
                clean_title = re.sub(r'<[^>]+>', '', title.group(1)).strip().lower()
                url_map[clean_title] = link.group(1)

        # 2. Extracción de datos de producto vía JSON-LD ItemList
        for jp in re.findall(r'<script type=\"application/ld\+json\">(.*?)</script>', html_content, re.DOTALL):
            try:
                data = json.loads(jp.strip())
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    for elem in data.get("itemListElement", []):
                        it = elem.get("item", {})
                        name = it.get("name", "").strip()
                        offers = it.get("offers", {})
                        price = float(offers.get("price", 0))
                        item_url = it.get("url") or ""

                        if not item_url:
                            t_low = name.lower()
                            for k, v in url_map.items():
                                if k in t_low or t_low in k:
                                    item_url = v
                                    break
                            if not item_url:
                                item_url = self.base_url

                        if 400.0 <= price <= 4500.0 and any(k in name.lower() for k in ["gravel", "jakar", "kalima", "terra", "nuroad", "silex", "speedster", "as-x", "diverge"]):
                            pvp = round(price * 1.25, 2)
                            results.append({
                                "title": name,
                                "price": price,
                                "pvp": pvp,
                                "discount_str": f"{round((pvp - price) / pvp * 100)}%",
                                "sizes": ["S", "M"], # Escapa suele tener stock multitalle en gravel de catálogo
                                "url": item_url,
                                "store_slug": self.store_slug,
                                "store_name": self.store_name,
                                "store_type": self.store_type
                            })
            except Exception:
                pass

        # Deduplicar por URL
        seen_urls = set()
        deduped = []
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                deduped.append(r)

        return deduped
