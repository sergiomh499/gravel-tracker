"""
gravel_bot.scrapers.buhobike - Scraper de Buhobike Madrid (Delicias / Moratalaz)
Tienda local de referencia en Madrid con taller, modelos Megamo/Orbea y sección de 2ª mano certificada.
Supera automáticamente los retos anti-DDoS / JavaScript challenge mediante ResilientSession.
"""

import re
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class BuhobikeScraper(BaseScraper):
    name = "buhobike"
    store_slug = "buhobike_delicias"
    store_name = "Buhobike Delicias / Moratalaz"
    store_type = "fisica"
    base_url = "https://www.buhobike.com"

    CATEGORY_URLS = [
        "https://www.buhobike.com/3211-gravel-aluminio",
        "https://www.buhobike.com/3205-gravel-carbono"
    ]

    # Modelos clave monitoreados en el catálogo y sección de 2ª mano certificada
    TARGET_URLS = [
        "https://www.buhobike.com/gravel-aluminio/25036-megamo-jakar-30-2027-bicicleta-gravel-8424735025527.html",
        "https://www.buhobike.com/gravel-aluminio/23453-megamo-jakar-20-2026-bicicleta-gravel.html",
        "https://www.buhobike.com/gravel-aluminio/24223-orbea-terra-h40-2026-bicicleta-gravel-8434446099144.html",
        "https://www.buhobike.com/gravel-aluminio/24222-orbea-terra-h50-1x-2026-bicicleta-gravel-8434446098918.html",
        "https://www.buhobike.com/segunda-mano-gravel/24266-orbea-terra-m20i-team-t-m-2024-bicicleta-segunda-mano.html",
        "https://www.buhobike.com/segunda-mano-gravel/24301-megamo-jakar-30-t--l-2021-bicicleta-segunda-mano.html"
    ]

    def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        seen_urls = set()

        # 1. Rastreo general por categorías completas de gravel
        for cat_url in self.CATEGORY_URLS:
            try:
                html = self.fetch_html(cat_url)
                if not html:
                    continue
                articles = re.findall(r'<article[^>]*class=\"[^\"]*product-miniature[^>]*>(.*?)</article>', html, re.DOTALL)
                for a in articles:
                    title_m = re.search(r'class=\"[^\"]*product-title[^\"]*\"[^>]*>\s*<a[^>]+href=\"([^\"]+)\"[^>]*>([^<]+)</a>', a)
                    price_m = re.search(r'itemprop=\"price\"\s*content=\"([^\"]+)\"', a) or re.search(r'class=\"price[^\"]*\"[^>]*>([^<]+)', a)
                    old_m = re.search(r'class=\"regular-price[^\"]*\"[^>]*>([^<]+)', a)
                    if title_m and price_m:
                        link = title_m.group(1)
                        if link in seen_urls:
                            continue
                        seen_urls.add(link)
                        name = title_m.group(2).strip()
                        price = self.clean_price(price_m.group(1))
                        pvp = self.clean_price(old_m.group(1)) if old_m else price
                        if pvp < price:
                            pvp = price
                        sizes = set(re.findall(r'talla-([a-z0-9]+)', link + ' ' + a, re.I))
                        if not sizes:
                            sizes = set(re.findall(r'\b(?:talla|size|t\.)\s*([a-z0-9]+)\b', name + ' ' + link, re.I))
                        clean_sizes = sorted([s.upper() for s in sizes if len(s) <= 4])
                        if 400 <= price <= 12000 and any(k in name.lower() for k in ['gravel', 'jakar', 'terra', 'crosshill', 'speedster', 'overland', 'silk']):
                            results.append({
                                "title": name,
                                "price": price,
                                "pvp": pvp,
                                "discount_str": f"{round((pvp - price) / pvp * 100)}%" if pvp > price else "0%",
                                "sizes": clean_sizes,
                                "url": link,
                                "store_slug": self.store_slug,
                                "store_name": self.store_name,
                                "store_type": self.store_type
                            })
            except Exception:
                continue

        # 2. Rastreo suplementario de modelos clave / segunda mano puntual
        for url in self.TARGET_URLS:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                html, status, meta = self.fetch_html(url), 200, {}
                if not html:
                    continue

                # 1. Extraer nombre
                name_m = re.search(r'"item_name":\s*"([^"]+)"', html) or re.search(r'<h1[^>]*class="[^"]*h1[^"]*"[^>]*>([^<]+)</h1>', html)
                if not name_m:
                    continue
                name = name_m.group(1).strip()
                # Limpiar texto de stock / color
                name = re.sub(r'\s+[MSLXL]+\s+(DUST|BLACK|GREEN|RED|GREY|RAW|SAND).*$', '', name, flags=re.I).strip()

                # 2. Extraer precio
                price_m = re.search(r'"price":\s*([0-9\.]+)', html) or re.search(r'itemprop="price"\s*content="([^"]+)"', html)
                if not price_m:
                    continue
                price = float(price_m.group(1))

                if price < 400.0:
                    continue

                # 3. PVP si existe descuento
                old_m = re.search(r'class="regular-price[^"]*"[^>]*>([^<]+)</span>', html)
                pvp = self.clean_price(old_m.group(1)) if old_m else price
                if pvp < price:
                    pvp = price

                # Tallas reales desde selector PrestaShop o URL/título
                raw_sizes = set()
                url_size_m = re.search(r't-+-([smlx0-9]+)', url, re.I)
                if url_size_m:
                    raw_sizes.add(url_size_m.group(1))
                for s in re.findall(r'title="Talla\s+([^"]+)"', html, re.I) + re.findall(r'talla-([a-z0-9]+)', html, re.I) + re.findall(r'class="radio-label"[^>]*>([^<]+)<', html, re.I):
                    raw_sizes.add(s)
                if not raw_sizes:
                    for s in re.findall(r'\b(?:talla|size|t\.)\s*([a-z0-9]+)\b', f"{name} {url}", re.I):
                        raw_sizes.add(s)
                sizes = sorted([s.upper().strip() for s in raw_sizes if s.strip() and len(s.strip()) <= 4])
                results.append({
                    "title": name,
                    "price": price,
                    "pvp": pvp,
                    "discount_str": f"{round((pvp - price) / pvp * 100)}%" if pvp > price else "0%",
                    "sizes": sizes,
                    "url": url,
                    "store_slug": self.store_slug,
                    "store_name": self.store_name,
                    "store_type": self.store_type
                })
            except Exception:
                continue

        return results
