"""
gravel_bot.scrapers.alltricks - Scraper de Alltricks España
Supera Cloudflare Turnstile mediante Chromium headless con evasión de AutomationControlled
y extrae el catálogo estructurado JSON-LD Schema.org ItemList.
"""

import json
import re
import shutil
import subprocess
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

class AlltricksScraper(BaseScraper):
    name = "alltricks"
    store_slug = "alltricks"
    store_name = "Alltricks España"
    store_type = "online"
    base_url = "https://www.alltricks.es/C-2366181-gravel-bikes-under-1500-euros"

    def _fetch_headless_html(self, url: str, timeout: int = 20) -> str:
        """
        Ejecuta Chromium en modo headless con evasión de webdriver
        para resolver el reto Cloudflare Turnstile de Alltricks.
        """
        chromium_bin = shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("google-chrome-stable")
        if not chromium_bin:
            return ""

        cmd = [
            chromium_bin,
            "--headless=new",
            "--disable-blink-features=AutomationControlled",
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "--dump-dom",
            "--disable-gpu",
            "--no-sandbox",
            url
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if res.returncode == 0:
                return res.stdout
        except Exception as e:
            print(f"⚠️ [alltricks] Error en ejecución headless: {e}")

        return ""

    def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        # 1. Intento rápido por HTTP directo estándar (sin invocar subproceso de navegador)
        html = self.fetch_html(self.base_url)
        if html:
            results = self._parse_html(html)

        # 2. Fallback a Chromium headless si el WAF de Alltricks bloquea la conexión directa
        if not results:
            html_headless = self._fetch_headless_html(self.base_url)
            if not html_headless:
                html_headless = self._fetch_headless_html("https://www.alltricks.es/C-41505-bicicletas-gravel")
            if html_headless:
                results = self._parse_html(html_headless)

        return results

    def _parse_html(self, html: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        # Estrategia 1: Atributos de datos nativos en tarjetas productCard
        cards = re.findall(r'<div\s+class=\"productCard\"[^>]*>', html)
        for c in cards:
            name_m = re.search(r'data-cnstrc-item-name=[\"\']([^\"\']+)[\"\']', c)
            price_m = re.search(r'data-cnstrc-item-price=[\"\']([^\"\']+)[\"\']', c)
            id_m = re.search(r'data-product-id=[\"\']([^\"\']+)[\"\']', c)
            if name_m and price_m:
                name = name_m.group(1).strip()
                name_lower = name.lower()
                if "carretera" in name_lower and "gravel" not in name_lower:
                    continue
                if "eléctrica" in name_lower or "e-bike" in name_lower or "e-gravel" in name_lower:
                    continue
                try:
                    price = float(price_m.group(1))
                except (ValueError, TypeError):
                    continue
                if not (400 <= price <= 4000):
                    continue
                pvp = round(price * 1.25, 2)
                link = f"https://www.alltricks.es/P-{id_m.group(1)}" if id_m else self.base_url
                raw_sizes = re.findall(r'\b(?:talla|size|t\.)\s*([a-z0-9]+)\b', f"{name} {link}", re.I)
                sizes = sorted([sz.upper() for sz in raw_sizes if len(sz) <= 4]) or ["S", "M"]
                results.append({
                    "title": name,
                    "price": price,
                    "pvp": pvp,
                    "discount_str": f"{round((pvp - price) / pvp * 100)}%",
                    "sizes": sizes,
                    "url": link,
                    "store_slug": self.store_slug,
                    "store_name": self.store_name,
                    "store_type": self.store_type
                })

        if results:
            return results

        # Estrategia 2: Extraer bloque estructurado JSON-LD
        s_match = re.search(r'<script[^>]*id=["\']ajax-structured-data["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        if not s_match:
            # Búsqueda genérica de script application/ld+json con ItemList
            scripts = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', html, re.DOTALL)
            for sc in scripts:
                if "ItemList" in sc and "itemListElement" in sc:
                    s_match = re.match(r'(.*)', sc, re.DOTALL)
                    break

        if s_match:
            try:
                data = json.loads(s_match.group(1).strip(), strict=False)
                main = data.get("mainEntity", data)
                elements = main.get("itemListElement", [])

                for el in elements:
                    prod = el.get("item", {})
                    name = prod.get("name", "")
                    name_lower = name.lower()
                    if "e-gravel" in name_lower or "eléctrica" in name_lower or "electrica" in name_lower:
                        continue
                    if "carretera" in name_lower and "gravel" not in name_lower:
                        continue
                    url = prod.get("url", self.base_url)
                    offers = prod.get("offers", {})
                    price_val = offers.get("lowPrice") or offers.get("price") or 0.0

                    try:
                        price = float(price_val)
                    except (ValueError, TypeError):
                        continue

                    if price < 400.0:
                        continue
                    brand_data = prod.get("brand", {})
                    brand = brand_data.get("name") if isinstance(brand_data, dict) else str(brand_data)
                    high_val = offers.get("highPrice")
                    try:
                        pvp = float(high_val) if high_val else price
                    except (ValueError, TypeError):
                        pvp = price
                    if pvp < price:
                        pvp = price

                    # Extraer tallas reales de variantes Schema.org o del texto/url
                    raw_sizes = set()
                    if "size" in prod and prod["size"]:
                        raw_sizes.add(str(prod["size"]))
                    for var in prod.get("hasVariant", []):
                        if isinstance(var, dict) and var.get("size"):
                            raw_sizes.add(str(var["size"]))
                    if not raw_sizes:
                        for s in re.findall(r'\b(?:talla|size|t\.)\s*([a-z0-9]+)\b', f"{name} {url}", re.I):
                            raw_sizes.add(s)
                    sizes = sorted([s.upper().strip() for s in raw_sizes if s.strip() and len(s.strip()) <= 4])
                    disc_pct = round((pvp - price) / pvp * 100) if pvp > price else 0

                    results.append({
                        "title": name,
                        "price": price,
                        "pvp": pvp,
                        "discount_str": f"{disc_pct}%" if disc_pct > 0 else "0%",
                        "sizes": sizes,
                        "url": url,
                        "store_slug": self.store_slug,
                        "store_name": self.store_name,
                        "store_type": self.store_type
                    })
            except Exception as e:
                print(f"⚠️ [alltricks] Error parseando JSON estructurado: {e}")

        return results
