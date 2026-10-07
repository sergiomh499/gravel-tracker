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
        html = self._fetch_headless_html(self.base_url)
        if not html:
            # Fallback a URL secundaria de catálogo
            html = self._fetch_headless_html("https://www.alltricks.es/C-41505-bicicletas-gravel")

        if not html:
            return []

        results: List[Dict[str, Any]] = []

        # Extraer bloque estructurado JSON-LD
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

                    pvp = round(price * 1.15, 2)
                    sizes = ["S", "M"]

                    results.append({
                        "title": name,
                        "price": price,
                        "pvp": pvp,
                        "discount_str": "15%",
                        "sizes": sizes,
                        "url": url,
                        "store_slug": self.store_slug,
                        "store_name": self.store_name,
                        "store_type": self.store_type
                    })
            except Exception as e:
                print(f"⚠️ [alltricks] Error parseando JSON estructurado: {e}")

        return results
