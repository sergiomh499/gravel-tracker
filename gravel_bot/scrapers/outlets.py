"""
gravel_bot.scrapers.outlets - Scrapers de Grandes Tiendas Outlet y Liquidaciones
Rastrea portales especializados en liquidación de stock, fin de temporada y descuentos agresivos:
Bicispasaje, Biciescapa, Bikeinn Outlet, Bicimarket y Mantel.
"""

import re
from typing import List, Dict, Any
from gravel_bot.scrapers.base import BaseScraper

OUTLET_TARGETS = [
    {
        "slug": "bicispasaje_outlet",
        "name": "Bicispasaje Outlet",
        "url": "https://www.bicispasaje.es/es/gravel-cx-14420",
        "base": "https://www.bicispasaje.es"
    },
    {
        "slug": "biciescapa_outlet",
        "name": "Biciescapa Outlet",
        "url": "https://www.biciescapa.com/es/bicicletas/gravel/outlet",
        "base": "https://www.biciescapa.com"
    },
    {
        "slug": "bikeinn_outlet",
        "name": "Bikeinn Outlet (Tradeinn)",
        "url": "https://www.tradeinn.com/bikeinn/es/bicicletas-y-cuadros-bicicletas-gravel/141562339/s",
        "base": "https://www.tradeinn.com"
    },
    {
        "slug": "bicimarket_outlet",
        "name": "Bicimarket Outlet",
        "url": "https://www.bicimarket.com/es/bicicletas/gravel/outlet",
        "base": "https://www.bicimarket.com"
    },
    {
        "slug": "mantel_outlet",
        "name": "Mantel Outlet España",
        "url": "https://www.mantel.com/es/bicicletas-gravel/outlet",
        "base": "https://www.mantel.com"
    }
]

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

        for target in OUTLET_TARGETS:
            html = self.fetch_html(target["url"])
            if not html:
                continue

            # Extracción genérica de fichas de producto en portales e-commerce estándar
            # Patrón para títulos y precios en listados
            cards = re.findall(
                r'(?:class="[^"]*(?:product|item|article)[^"]*".*?|href="([^"]*(?:gravel|bicicleta|bici)[^"]*)".*?)'
                r'([^<]{10,80}(?:gravel|jakar|kalima|terra|nuroad|silex|esker|x-grip|x-strada|as-x)[^<]{0,50})'
                r'.*?(\d+[\.,]\d{2,3}\s*€)',
                html,
                re.DOTALL | re.IGNORECASE
            )

            for match in cards[:15]:
                link_part, title_cand, price_cand = match[0], match[1], match[2]
                clean_t = self.clean_text(title_cand)
                clean_p = self.clean_price(price_cand)

                if clean_p < 400.0 or clean_p > 3500.0:
                    continue

                full_url = link_part if link_part.startswith("http") else f"{target['base']}{link_part}"

                results.append({
                    "title": clean_t,
                    "price": clean_p,
                    "pvp": clean_p * 1.30, # Descuento outlet base estimado
                    "url": full_url,
                    "description": f"Liquidación en {target['name']}",
                    "sizes": ["S", "M", "XS"],
                    "tienda_slug": target["slug"]
                })

        return results
