"""
gravel_bot.anti_ban - Motor de Resiliencia, Evasión de Bloqueos y Gestión Anti-Bot
Implementa perfiles de navegación coherentes, rate limiting adaptativo con jitter humano,
gestión persistente de cookies de sesión, backoff exponencial y detección de retos/CAPTCHAs.
"""

import time
import random
import re
import urllib.request
import urllib.error
import urllib.parse
import http.cookiejar
from typing import Dict, Any, Optional, Tuple

# Perfiles de navegador coherentes (User-Agent + Client Hints alineados)
BROWSER_PROFILES = [
    {
        "name": "Chrome_Windows",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
    },
    {
        "name": "Chrome_macOS",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
    },
    {
        "name": "Firefox_Windows",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
    },
    {
        "name": "Safari_macOS",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none"
        }
    }
]

# Firmas de retos anti-bot y páginas de verificación CAPTCHA
CHALLENGE_SIGNATURES = [
    "cf-chl-", "challenges.cloudflare.com", "ray id:", "attention required! | cloudflare",
    "turnstile", "recaptcha", "g-recaptcha", "hcaptcha", "datadome",
    "perimeterx", "press & hold", "verificación de seguridad", "bot detection"
]

class AdaptiveRateLimiter:
    """Gestiona pausas inteligentes y espaciado por dominio para simular navegación humana."""
    _last_request_time: Dict[str, float] = {}

    @classmethod
    def wait(cls, domain: str, min_delay: float = 1.2, max_delay: float = 3.0):
        now = time.time()
        last_time = cls._last_request_time.get(domain, 0.0)
        target_delay = random.uniform(min_delay, max_delay)
        elapsed = now - last_time

        if elapsed < target_delay:
            sleep_time = target_delay - elapsed
            time.sleep(sleep_time)

        cls._last_request_time[domain] = time.time()

class ResilientSession:
    """
    Sesión HTTP con persistencia de cookies, rotación de perfiles,
    gestión de backoff exponencial y detección de CAPTCHAs.
    """
    _cookie_jar = http.cookiejar.CookieJar()
    _opener = None
    _cooldown_domains: Dict[str, float] = {}

    @classmethod
    def get_opener(cls):
        if cls._opener is None:
            cookie_handler = urllib.request.HTTPCookieProcessor(cls._cookie_jar)
            cls._opener = urllib.request.build_opener(cookie_handler)
        return cls._opener

    @classmethod
    def is_in_cooldown(cls, domain: str) -> bool:
        """Comprueba si un dominio está en pausa preventiva por reto anti-bot detectado."""
        cooldown_until = cls._cooldown_domains.get(domain, 0.0)
        return time.time() < cooldown_until

    @classmethod
    def set_cooldown(cls, domain: str, seconds: float = 300.0):
        cls._cooldown_domains[domain] = time.time() + seconds

    @classmethod
    def detect_anti_bot_challenge(cls, html: str, status_code: int) -> bool:
        """Determina si la respuesta contiene un CAPTCHA o reto Cloudflare/WAF."""
        if status_code in [403, 503, 429]:
            h_lower = html.lower()
            return any(sig in h_lower for sig in CHALLENGE_SIGNATURES)
        return False

    @classmethod
    def get_random_profile(cls) -> Dict[str, Any]:
        """Selecciona un perfil de navegador aleatorio coherente."""
        return random.choice(BROWSER_PROFILES)

    @classmethod
    def fetch(cls, url: str, timeout: int = 12, max_retries: int = 2) -> Tuple[Optional[str], int, Dict[str, Any]]:
        """
        Descarga una URL ejecutando rate limiting, rotación de headers y backoff en caso de 429/503.
        Retorna: (html_text, status_code, metadata_dict)
        """
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()

        if cls.is_in_cooldown(domain):
            return None, 429, {"error": "domain_in_cooldown", "reason": "Dominio en enfriamiento preventivo por CAPTCHA previo"}

        # 1. Rate limiting con jitter humano
        AdaptiveRateLimiter.wait(domain)

        opener = cls.get_opener()
        profile = cls.get_random_profile()
        headers = dict(profile["headers"])

        # Referer natural si es página interna
        if parsed.path and parsed.path != "/":
            headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"

        for attempt in range(max_retries + 1):
            req = urllib.request.Request(url, headers=headers)
            try:
                with opener.open(req, timeout=timeout) as res:
                    status = res.status
                    raw_data = res.read()
                    text = raw_data.decode("utf-8", errors="ignore")

                    # Verificar si nos entregaron un reto 200 OK falso
                    if cls.detect_anti_bot_challenge(text, status):
                        cls.set_cooldown(domain, seconds=180.0)
                        return None, 403, {"error": "captcha_detected", "reason": "Reto Cloudflare / CAPTCHA detectado en página 200 OK"}

                    return text, status, {"profile": profile["name"], "attempts": attempt + 1}

            except urllib.error.HTTPError as e:
                status = e.code
                error_body = ""
                try:
                    error_body = e.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass
                # Resolución de retos JavaScript automáticos basados en cookie (ej. PrestaShop / DDoS Shield)
                token_m = re.search(r'var\s+t\s*=\s*["\']([a-f0-9]{32,64})["\']', error_body)
                cookie_m = re.search(r'document\.cookie\s*=\s*["\']([^"\'=]+)=', error_body)
                if token_m and attempt < max_retries:
                    c_token = token_m.group(1)
                    c_name = cookie_m.group(1) if cookie_m else "en_ad_challenge"
                    headers["Cookie"] = f"{c_name}={c_token}"
                    time.sleep(0.5)
                    continue

                # Detectar CAPTCHA o reto insuperable
                if cls.detect_anti_bot_challenge(error_body, status):
                    cls.set_cooldown(domain, seconds=300.0)
                    return None, status, {
                        "error": "captcha_or_waf_challenge",
                        "status": status,
                        "reason": f"WAF / CAPTCHA activado en {domain}. Enfriamiento aplicado para proteger la IP."
                    }
                # Backoff exponencial si es 429 Too Many Requests o 503
                if status in [429, 503] and attempt < max_retries:
                    retry_after = e.headers.get("Retry-After")
                    delay = float(retry_after) if (retry_after and retry_after.isdigit()) else (2.0 * (2 ** attempt) + random.uniform(0.5, 1.5))
                    time.sleep(delay)
                    continue

                return None, status, {"error": "http_error", "status": status}

            except Exception as e:
                if attempt < max_retries:
                    time.sleep(1.0 + random.uniform(0.5, 1.0))
                    continue
                return None, 0, {"error": "network_exception", "exception": str(e)}

        return None, 0, {"error": "max_retries_exceeded"}
