"""
gravel_bot.scrapers.cicloscorredor - Scraper Avanzado de Ciclos Corredor (Vallecas / Madrid)
Tienda histórica a 2,2 km de Méndez Álvaro.
Rastrea el catálogo completo de gravel (páginas 1 y 2) y extrae tallas y stock
reales en tienda a través de la tabla estructurada 'data-references'.
"""

import re
import json
import html
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper
from gravel_bot.anti_ban import ResilientSession

class CiclosCorredorScraper(BaseScraper):
    name = "ciclos_corredor"
    store_slug = "ciclos_corredor"
    store_name = "Ciclos Corredor Vallecas"
    store_type = "fisica"
    base_category_url = "https://cicloscorredor.com/es/c/bicicletas-gravel"

    def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        product_urls: List[str] = []
        pages_to_crawl = [self.base_category_url]
        crawled_pages = set()

        # 1. Recorrer páginas de categoría y obtener URLs de producto candidatas
        while pages_to_crawl:
            cat_url = pages_to_crawl.pop(0)
            if cat_url in crawled_pages:
                continue
            crawled_pages.add(cat_url)

            page_html = self.fetch_html(cat_url)
            if not page_html:
                continue

            # Extraer enlaces a páginas siguientes con uid_pag dinámico
            for p_link in re.findall(r'href=[\'"](/es/c/bicicletas-gravel\?uid_pag=[^\'"]+page=\d+[^\'"]*)[\'"]', page_html):
                full_p = "https://cicloscorredor.com" + p_link
                if full_p not in crawled_pages and full_p not in pages_to_crawl:
                    pages_to_crawl.append(full_p)

            matches = re.finditer(
                r'<h3[^>]*>\s*<a[^>]+href=[\'"](/es/p/[^\'"]+)[\'"][^>]*>\s*([^<]+)\s*</a>\s*</h3>(.*?)</div>\s*</div>',
                page_html,
                re.DOTALL
            )
            for m in matches:
                url_path = m.group(1)
                item_title = m.group(2).strip()
                tail = m.group(3)
                title_lower = item_title.lower()
                if any(nb in title_lower for nb in ["ruedas", "gafas", "rodillo", "casco", "zapatilla", "maillot", "culotte", "cubierta"]):
                    continue

                sale_m = re.search(r'class="sale[^"]*"[^>]*>\s*([\d\.,]+)\s*€', tail)
                amount_m = re.search(r'class="amount[^"]*"[^>]*>\s*([\d\.,]+)\s*€', tail)
                p_m = re.search(r'([\d\.,]+)\s*€', tail)

                sale_str = sale_m.group(1) if sale_m else (p_m.group(1) if p_m else "0")
                sale_price = self.clean_price(sale_str)

                # Priorizar productos en rango accesible (400 - 1.800 €)
                if 400.0 <= sale_price <= 1800.0:
                    full_url = "https://cicloscorredor.com" + url_path
                    if full_url not in product_urls:
                        product_urls.append(full_url)

        # 2. Consultar fichas de producto para extraer tallas exactas con stock en tienda
        for p_url in product_urls:
            p_html = self.fetch_html(p_url)
            if not p_html:
                continue

            t_m = re.search(r'<h1[^>]*>([^<]+)</h1>', p_html)
            title = t_m.group(1).strip() if t_m else p_url.split('/')[-1]

            # Parsear data-references para obtener variantes de talla y stock
            m = re.search(r'data-references=[\'"](\[.*?\])[\'"]', p_html)
            available_sizes = []
            final_price = 0.0
            pvp_price = 0.0

            if m:
                try:
                    raw = html.unescape(m.group(1))
                    refs = json.loads(raw)
                    for r in refs:
                        talla = r.get("attribute_values_explained", "").strip()
                        stock_str = r.get("virtual_online_stock", "0")
                        avail = r.get("availability", "")
                        price_cand = float(r.get("final_price_taxes") or r.get("sales_price_taxes") or 0.0)
                        pvp_cand = float(r.get("sales_price_taxes") or price_cand)

                        try:
                            stock_int = int(float(stock_str))
                        except Exception:
                            stock_int = 1 if avail == "in_stock" else 0

                        if stock_int > 0 or avail == "in_stock":
                            if talla and talla not in available_sizes:
                                available_sizes.append(talla)
                            if final_price == 0.0 or price_cand < final_price:
                                final_price = price_cand
                                pvp_price = pvp_cand
                except Exception:
                    pass

            if final_price == 0.0:
                p_match = re.search(r'class="sale[^"]*"[^>]*>\s*([\d\.,]+)\s*€', p_html) or re.search(r'([\d\.,]+)\s*€', p_html)
                final_price = self.clean_price(p_match.group(1)) if p_match else 0.0
                pvp_price = final_price

            if final_price < 400.0:
                continue

            # Si no hay data-references, asignar por defecto
            if not available_sizes:
                available_sizes = ["Consultar"]

            discount_pct = round((pvp_price - final_price) / pvp_price * 100) if pvp_price > final_price else 0

            results.append({
                "title": title,
                "price": final_price,
                "pvp": pvp_price if pvp_price >= final_price else final_price,
                "discount_str": f"{discount_pct}%" if discount_pct > 0 else "0%",
                "sizes": available_sizes,
                "url": p_url,
                "store_slug": self.store_slug,
                "store_name": self.store_name,
                "store_type": self.store_type
            })

        return results
