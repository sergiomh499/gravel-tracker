"""
gravel_bot.scrapers.outlets - Scrapers de Grandes Tiendas Outlet y Liquidaciones
Rastrea portales especializados en liquidación de stock, fin de temporada y gravel:
Biciescapa (Escapa), Bikestocks y Bicispasaje.
"""

import re
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class OutletAggregatorScraper(BaseScraper):
    """
    Rastreador unificado de ofertas procedentes de portales outlet especializados.
    """
    name = "outlets_espana"
    store_slug = "outlets_espana"
    store_name = "Red Outlets Ciclismo España"
    store_type = "outlet_online"

    def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        # 1. Biciescapa (Escapa)
        try:
            escapa_url = "https://www.escapa.com/bicicletas/gravel-cx"
            html_esc = self.fetch_html(escapa_url)
            if html_esc:
                cards = re.findall(r'<li[^>]*class="[^"]*product[^"]*"[^>]*>(.*?)</li>', html_esc, re.DOTALL)
                for c in cards:
                    t_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', c)
                    p_match = re.search(r'class="price[^"]*"[^>]*>(.*?)</span>', c) or re.search(r'(\d+[\.,]\d{2})\s*€', c)
                    if t_match and p_match:
                        link = t_match.group(1)
                        name = t_match.group(2).strip()
                        if "elegir" in name.lower() or "ver" in name.lower() or len(name) < 4:
                            slug = link.rstrip("/").split("/")[-1].replace("bicicleta-", "").replace("-", " ")
                            name = slug.title()

                        p_val = self.clean_price(p_match.group(1))
                        if 400.0 <= p_val <= 4000.0:
                            results.append({
                                "title": name,
                                "price": p_val,
                                "pvp": round(p_val * 1.25, 2),
                                "url": link,
                                "description": "Liquidación gravel en Biciescapa",
                                "sizes": ["S", "M", "XS"],
                                "tienda_slug": self.store_slug
                            })
        except Exception:
            pass

        # 2. Bikestocks
        try:
            bs_url = "https://www.bikestocks.es/buscar?controller=search&s=gravel"
            html_bs = self.fetch_html(bs_url)
            if html_bs:
                articles = re.findall(r'<article[^>]*class="[^"]*product-miniature[^"]*"[^>]*>(.*?)</article>', html_bs, re.DOTALL)
                for a in articles:
                    t_match = re.search(r'alt="([^"]*GRAVEL[^"]*)"', a, re.I) or re.search(r'<a[^>]+href="([^"]+)"[^>]*>([^<]*GRAVEL[^<]*)</a>', a, re.I)
                    p_match = re.search(r'itemprop="price"\s*content="([^"]+)"', a) or re.search(r'content="([^"]+)"\s*itemprop="price"', a) or re.search(r'class="price"[^>]*>(.*?)</span>', a)
                    l_match = re.search(r'<a[^>]+class="thumbnail[^"]*"[^>]+href="([^"]+)"', a) or re.search(r'<a[^>]+href="([^"]+)"', a)
                    if t_match and p_match and l_match:
                        name = (t_match.group(1) if t_match.lastindex == 1 else t_match.group(2)).strip()
                        p_val = self.clean_price(p_match.group(1))
                        link = l_match.group(1)
                        if 400.0 <= p_val <= 4000.0 and len(name) > 5:
                            results.append({
                                "title": name,
                                "price": p_val,
                                "pvp": round(p_val * 1.25, 2),
                                "url": link,
                                "description": "Liquidación gravel en Bikestocks",
                                "sizes": ["S", "M", "XS"],
                                "tienda_slug": self.store_slug
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
