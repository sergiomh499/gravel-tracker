"""
gravel_bot.scrapers.multi_store - Rastreador Concurrente Multi-Tienda (Red Nacional y Europea)
Ejecuta consultas concurrentes con ThreadPoolExecutor sobre las tiendas del directorio
aplicando parsers estándar de comercio electrónico (PrestaShop, WooCommerce, JSON-LD).
"""

import re
import json
import concurrent.futures
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper
from gravel_bot.scrapers.store_directory import STORE_DIRECTORY

class MultiStoreAggregatorScraper(BaseScraper):
    """
    Rastreador concurrente que consulta tiendas del directorio que no disponen
    de scraper dedicado exclusivo, usando patrones estándar de comercio electrónico.
    """
    name = "red_tiendas_ciclismo"
    store_slug = "red_tiendas_ciclismo"
    store_name = "Red Nacional y Europea de Tiendas de Ciclismo"
    store_type = "online"
    base_url = "https://www.sanferbike.com"

    # Tiendas que ya tienen scrapers dedicados (para no duplicar llamadas)
    EXCLUDED_SLUGS = {
        "decathlon_usera",
        "bike_discount",
        "bicimarket_online",
        "canyon_espana",
        "bicispasaje_online",
        "ciclos_corredor",
        "bikestocks_online",
        "buhobike_delicias",
        "alltricks",
        "sanferbike_m30",
        "fabregues_online",
        "mammoth_madrid",
        "wallapop_madrid",
        "chollometro"
    }

    def _parse_store_html(self, store: Dict[str, Any], html: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not html or len(html) < 1000:
            return results

        slug = store["slug"]
        s_name = store["nombre"]

        # 1. Estrategia JSON-LD universal
        json_products = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        for jp in json_products:
            if '"Product"' in jp or '"offers"' in jp:
                try:
                    data = json.loads(jp, strict=False)
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    if data.get("@type") == "Product":
                        name = data.get("name", "")
                        offers = data.get("offers", {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        price = float(offers.get("price", 0))
                        url = offers.get("url") or store["url"]
                        if 400.0 <= price <= 4000.0 and any(k in name.lower() for k in ["gravel", "jakar", "kalima", "esker", "terra", "nuroad", "silex"]):
                            results.append({
                                "title": name.strip(),
                                "price": price,
                                "pvp": round(price * 1.2, 2),
                                "url": url,
                                "sizes": ["S", "M"],
                                "store_slug": slug,
                                "store_name": s_name
                            })
                except Exception:
                    pass

        # 2. Estrategia PrestaShop (product-miniature)
        articles = re.findall(r'<article[^>]*class="[^"]*product-miniature[^"]*"[^>]*>(.*?)</article>', html, re.DOTALL)
        for a in articles:
            t = re.search(r'class="[^"]*product-title[^"]*"[^>]*><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>', a)
            p = re.search(r'itemprop="price"\s*class="price">([^<]+)</span>', a) or re.search(r'class="price[^"]*"[^>]*>([^<]+)</span>', a)
            if t and p:
                name = t.group(2).strip()
                price = self.clean_price(p.group(1))
                link = t.group(1)
                if 400.0 <= price <= 4000.0 and any(k in name.lower() for k in ["gravel", "bici", "jakar", "kalima", "esker", "terra", "nuroad", "silex", "x-grip"]):
                    results.append({
                        "title": name,
                        "price": price,
                        "pvp": round(price * 1.2, 2),
                        "url": link,
                        "sizes": ["S", "M"],
                        "store_slug": slug,
                        "store_name": s_name
                    })

        # 3. Estrategia WooCommerce (product class)
        wc_items = re.findall(r'<li[^>]*class="[^"]*product[^"]*"[^>]*>(.*?)</li>', html, re.DOTALL)
        for w in wc_items:
            t = re.search(r'<h2[^>]*class="[^"]*woocommerce-loop-product__title[^"]*"[^>]*>([^<]+)</h2>', w)
            l = re.search(r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*woocommerce-LoopProduct-link', w) or re.search(r'<a[^>]+href="([^"]+)"', w)
            p = re.search(r'class="woocommerce-Price-amount[^"]*"[^>]*><bdi>([^<]+)', w) or re.search(r'class="price"[^>]*>([^<]+)</span>', w)
            if t and l and p:
                name = t.group(1).strip()
                price = self.clean_price(p.group(1))
                link = l.group(1)
                if 400.0 <= price <= 4000.0 and any(k in name.lower() for k in ["gravel", "bici", "jakar", "kalima", "esker", "terra", "nuroad"]):
                    results.append({
                        "title": name,
                        "price": price,
                        "pvp": round(price * 1.2, 2),
                        "url": link,
                        "sizes": ["S", "M"],
                        "store_slug": slug,
                        "store_name": s_name
                    })

        # Deduplicar por URL
        seen = set()
        deduped = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                deduped.append(r)

        return deduped

    def scrape(self) -> List[Dict[str, Any]]:
        # Tiendas elegibles con URLs que responden
        eligible_stores = [s for s in STORE_DIRECTORY if s["slug"] not in self.EXCLUDED_SLUGS and s.get("scrape_url")]
        all_results: List[Dict[str, Any]] = []

        def _fetch_and_parse(store: Dict[str, Any]):
            url = store.get("scrape_url", store["url"])
            try:
                html = self.fetch_html(url, timeout=4)
                if html:
                    return self._parse_store_html(store, html)
            except Exception:
                pass
            return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_store = {executor.submit(_fetch_and_parse, store): store for store in eligible_stores}
            for future in concurrent.futures.as_completed(future_to_store):
                try:
                    store_results = future.result()
                    if store_results:
                        all_results.extend(store_results)
                except Exception:
                    pass

        return all_results
