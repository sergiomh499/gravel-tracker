"""
gravel_bot.scrapers.base - Clase Base para Scrapers de Tiendas de Ciclismo
"""

import re
import html
from typing import List, Dict, Any, Optional
from gravel_bot.anti_ban import ResilientSession

class BaseScraper:
    name: str = "base"
    store_slug: str = "base"
    store_name: str = "Base Store"
    store_type: str = "online"
    base_url: str = ""

    def fetch_html(self, url: str, timeout: int = 12) -> Optional[str]:
        """
        Descarga el contenido HTML utilizando el motor resiliente anti-ban:
        rotación de perfiles de navegador, rate limiting adaptativo y persistencia de cookies.
        """
        html_text, status, meta = ResilientSession.fetch(url, timeout=timeout)
        if not html_text:
            err = meta.get("error", "desconocido")
            reason = meta.get("reason", "")
            if err not in ["network_exception", "http_error", "domain_in_cooldown"] and status not in [403, 404]:
                print(f"⚠️ [{self.name}] Petición no completada a {url} (Status {status}, Motivo: {err} {reason})")
        return html_text

    @staticmethod
    def clean_price(text: str) -> float:
        """Convierte cadenas como '1.299,00 €', '1,299.00', '1.299' o '1349.1' a un float numérico limpio."""
        if not text:
            return 0.0
        # Eliminar símbolos, espacios y letras
        cleaned = re.sub(r'[^\d,\.]', '', str(text)).strip()
        if not cleaned:
            return 0.0

        # Si tiene tanto coma como punto, determinar cuál es el separador decimal
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                # Formato europeo: 1.299,00 -> 1299.00
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # Formato anglosajón / JSON: 1,299.00 -> 1299.00
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            # Caso europeo con coma única: 1299,00 o 1,299
            parts = cleaned.split(",")
            if len(parts) == 2 and len(parts[1]) == 3 and int(parts[0]) > 0:
                # Miles: 1,299
                cleaned = parts[0] + parts[1]
            else:
                cleaned = cleaned.replace(",", ".")
        elif "." in cleaned:
            # Caso con punto único: 1.299 (miles) vs 1299.50 (decimales)
            parts = cleaned.split(".")
            if len(parts) == 2 and len(parts[1]) == 3:
                cleaned = parts[0] + parts[1]
            elif len(parts) > 2:
                # Varios puntos de miles: 1.299.000
                cleaned = "".join(parts[:-1]) + ("." + parts[-1] if len(parts[-1]) <= 2 else parts[-1])

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
