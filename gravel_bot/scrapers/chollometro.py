"""
gravel_bot.scrapers.chollometro - Scraper de Ofertas Comunitarias de Chollometro
Rastrea ofertas de bicicletas gravel compartidas y votadas por la comunidad.
"""

import json
import html
import re
from typing import List, Dict, Any, Optional
from gravel_bot.scrapers.base import BaseScraper
from gravel_bot.anti_ban import ResilientSession

class ChollometroScraper(BaseScraper):
    def __init__(self):
        self.name = "Chollometro"
        self.store_slug = "chollometro"
        self.store_name = "Chollometro"
        self.store_type = "comunidad"
        self.base_url = "https://www.chollometro.com"
        self.search_queries = [
            "bicicleta+gravel",
            "gravel"
        ]
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Rastrea las búsquedas en Chollometro y extrae ofertas activas de gravel.
        """
        items: List[Dict[str, Any]] = []
        seen_threads = set()

        for q in self.search_queries:
            url = f"{self.base_url}/search?q={q}"
            page_html = self.fetch_html(url)
            if not page_html:
                continue

            matches = re.findall(r'data-vue3=[\'\"]({.*?threadId.*?})[\'\"]', page_html)
            for m in matches:
                try:
                    clean_json = html.unescape(m)
                    data = json.loads(clean_json)
                    thread = data.get("props", {}).get("thread", {})
                    
                    tid = thread.get("threadId")
                    if not tid or tid in seen_threads:
                        continue
                    
                    # Descartar ofertas expiradas
                    if thread.get("isExpired", False):
                        continue

                    title = thread.get("title") or ""
                    price = thread.get("price")
                    if not title or price is None:
                        continue

                    # Filtrar que realmente sea una bicicleta de gravel y no un accesorio o producto promocionado
                    title_lower = title.lower()
                    if not any(k in title_lower for k in ["gravel", "jakar", "kalima", "esker", "terra", "nuroad", "silex", "speedster", "diverge"]):
                        continue
                    non_bike_keywords = ["casco", "zapatilla", "rueda", "cubierta", "manillar", "bolsa", "luz", "guante", "potencia", "sillin", "pedal", "tv", "oled"]
                    if any(nb in title_lower for nb in non_bike_keywords) and "bicicleta" not in title_lower and "bici" not in title_lower:
                        continue

                    # PVP y descuento
                    pvp = thread.get("nextBestPrice") or price
                    try:
                        price_float = float(price)
                        pvp_float = float(pvp)
                    except (ValueError, TypeError):
                        continue

                    if price_float < 400.0 or price_float > 4500.0:
                        continue
                    slug = thread.get("titleSlug") or str(tid)
                    deal_url = f"{self.base_url}/ofertas/{slug}-{tid}"
                    merchant = thread.get("merchant")
                    merchant_name = merchant.get("merchantName") if isinstance(merchant, dict) else (merchant or "Chollometro")
                    temp = thread.get("temperature", 0)
                    item = {
                        "title": title,
                        "price": price_float,
                        "pvp": pvp_float if pvp_float >= price_float else price_float,
                        "sizes": ["Consultar"],
                        "url": deal_url,
                        "discount_str": f"{round((pvp_float - price_float)/pvp_float * 100)}%" if pvp_float > price_float else "0%",
                        "store_slug": "chollometro",
                        "store_name": f"Chollometro ({merchant_name})",
                        "store_type": "comunidad",
                        "en_stock": 1,
                        "temperatura_comunidad": temp
                    }
                    seen_threads.add(tid)
                    items.append(item)
                except Exception as e:
                    continue

        return items
