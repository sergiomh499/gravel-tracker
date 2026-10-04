"""
gravel_bot.scrapers.base - Clase Base para Scrapers de Tiendas de Ciclismo
"""

import re
import html
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from gravel_bot.config import DEFAULT_HEADERS

class BaseScraper:
    name: str = "base"
    store_slug: str = "base"
    store_name: str = "Base Store"
    store_type: str = "online"
    base_url: str = ""

    def fetch_html(self, url: str, timeout: int = 12) -> Optional[str]:
        """Descarga el contenido HTML de una página web con headers estándar."""
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return res.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            print(f"⚠️ [{self.name}] Error HTTP {e.code} en {url}")
            return None
        except Exception as e:
            print(f"⚠️ [{self.name}] Error de conexión en {url}: {e}")
            return None

    @staticmethod
    def clean_price(text: str) -> float:
        """Convierte cadenas como '1.299,00 €' o '1349.1' a un float numérico limpio."""
        if not text:
            return 0.0
        # Eliminar símbolos y espacios
        cleaned = re.sub(r'[^\d,\.]', '', text).strip()
        if not cleaned:
            return 0.0

        # Formato europeo: 1.299,00 -> 1299.00
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            # Caso 1299,00
            cleaned = cleaned.replace(",", ".")
        elif "." in cleaned:
            # Caso 1.299 (sin decimales) vs 1299.50
            parts = cleaned.split(".")
            if len(parts) == 2 and len(parts[1]) == 3: # Miles: 1.299
                cleaned = parts[0] + parts[1]

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def clean_text(text: str) -> str:
        """Limpia etiquetas HTML y entidades."""
        if not text:
            return ""
        no_html = re.sub(r'<[^>]+>', ' ', text)
        unescaped = html.unescape(no_html)
        return ' '.join(unescaped.split())

    def scrape(self) -> List[Dict[str, Any]]:
        """Método abstracto que deben implementar los scrapers específicos."""
        raise NotImplementedError
