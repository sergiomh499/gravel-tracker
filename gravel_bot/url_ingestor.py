"""
gravel_bot.url_ingestor - Ingestor Dinámico de Enlaces de Bicicletas y Tiendas
Permite incorporar automáticamente cualquier URL a la base de datos calculando componentes y rúbrica.
"""

import re
import json
import html
import urllib.parse
from typing import Dict, Any, Optional, Tuple
from gravel_bot.anti_ban import ResilientSession
from gravel_bot.db import get_or_create_store, upsert_bike, record_price_if_changed, get_connection
from gravel_bot.evaluator import detect_bike_specs
from gravel_bot.bike_inspector import format_detailed_bike_card

def extract_metadata_from_html(page_html: str, url: str) -> Dict[str, Any]:
    """
    Extrae título, precio de oferta, PVP y tallas a partir de meta tags, microdatos y HTML.
    """
    title = ""
    price = 0.0
    pvp = 0.0
    sizes = []

    # 1. Intentar JSON-LD (Schema.org Product)
    ld_json_matches = re.findall(r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', page_html, re.DOTALL)
    for block in ld_json_matches:
        try:
            data = json.loads(block.strip())
            # Si es lista o grafo
            items = data.get("@graph", [data]) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for it in items:
                if isinstance(it, dict) and it.get("@type") in ["Product", "IndividualProduct"]:
                    if not title and it.get("name"):
                        title = it["name"]
                    offers = it.get("offers")
                    if isinstance(offers, dict):
                        p = offers.get("price") or offers.get("lowPrice")
                        if p:
                            price = float(p)
                    elif isinstance(offers, list) and offers:
                        p = offers[0].get("price")
                        if p:
                            price = float(p)
        except Exception:
            pass

    # 2. Meta tags OpenGraph y Twitter
    if not title:
        og_title = re.search(r'<meta[^>]*property=[\'"]og:title[\'"][^>]*content=[\'"]([^\'"]+)[\'"]', page_html, re.IGNORECASE)
        if og_title:
            title = og_title.group(1)

    if not title:
        raw_title = re.search(r'<title[^>]*>(.*?)</title>', page_html, re.IGNORECASE | re.DOTALL)
        if raw_title:
            title = raw_title.group(1).split("|")[0].split("-")[0].strip()

    title = html.unescape(title).strip()

    # 3. Precio OpenGraph / itemprop
    if price <= 0.0:
        og_price = re.search(r'<meta[^>]*property=[\'"](?:og:price:amount|product:price:amount)[\'"][^>]*content=[\'"]([^\'"]+)[\'"]', page_html, re.IGNORECASE)
        if og_price:
            try:
                price = float(og_price.group(1).replace(",", "."))
            except ValueError:
                pass

    if price <= 0.0:
        itemprop_price = re.search(r'itemprop=[\'"]price[\'"][^>]*content=[\'"]([^\'"]+)[\'"]', page_html, re.IGNORECASE)
        if itemprop_price:
            try:
                price = float(itemprop_price.group(1).replace(",", "."))
            except ValueError:
                pass

    # 4. Fallback de precio con Regex en texto visible
    if price <= 0.0:
        price_matches = re.findall(r'(\d{1,2}[\.,]\d{3}|\d{3,4})[\s]*(?:€|EUR)', page_html)
        clean_prices = []
        for pm in price_matches:
            val_str = pm.replace(".", "").replace(",", ".")
            try:
                val = float(val_str)
                if 400.0 <= val <= 9000.0:
                    clean_prices.append(val)
            except ValueError:
                pass
        if clean_prices:
            # Tomamos el precio más bajo como oferta y el más alto como PVP
            price = min(clean_prices)
            if len(clean_prices) > 1:
                pvp = max(clean_prices)

    # 5. Detección de tallas en texto
    for sz in ["xs", "s", "sm", "m", "md", "l", "lg", "xl", "48", "50", "51", "52", "54"]:
        if re.search(rf'\b(?:talla|size|talle)[\s:]*{sz}\b', page_html, re.IGNORECASE):
            sizes.append(sz.upper())

    if pvp < price:
        pvp = price

    return {
        "title": title or "Bicicleta Gravel",
        "price": price or 1000.0,
        "pvp": pvp or price or 1200.0,
        "sizes": list(set(sizes))
    }

def ingest_bike_url(url: str, custom_store_name: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Descarga una página web de producto, detecta componentes y añade la bicicleta a la base de datos.
    Retorna: (éxito, mensaje, datos_bici)
    """
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False, "❌ La URL proporcionada no es válida. Debe incluir http:// o https://", None

    domain = parsed.netloc.lower()
    page_html, status, meta = ResilientSession.fetch(url)

    if not page_html:
        err = meta.get("error", "Error de red")
        return False, f"❌ No se pudo descargar la página (Status {status}: {err}).", None

    meta_extracted = extract_metadata_from_html(page_html, url)
    title = meta_extracted["title"]
    price = meta_extracted["price"]
    pvp = meta_extracted["pvp"]
    sizes = meta_extracted["sizes"]

    # Identificar o crear la tienda
    store_slug = re.sub(r'[^a-zA-Z0-9]+', '_', domain).strip('_')
    store_name = custom_store_name or domain.replace("www.", "").capitalize()
    store_id = get_or_create_store(
        slug=store_slug,
        nombre=store_name,
        tipo="online",
        url=f"{parsed.scheme}://{parsed.netloc}"
    )

    # Evaluar componentes y rúbrica biométrica
    specs = detect_bike_specs(title=title, description=page_html[:2000], price=price, sizes=sizes)
    specs["tienda_id"] = store_id
    specs["url_oferta"] = url
    specs["precio_pvp"] = pvp
    specs["precio_oferta"] = price
    specs["en_stock"] = 1

    # Insertar o actualizar en SQLite
    bike_id = upsert_bike(specs)

    # Registrar en historial de precios
    record_price_if_changed(
        bike_id=bike_id,
        store_id=store_id,
        price=price,
        size=", ".join(sizes) or specs.get("talla_recomendada_169", "S"),
        in_stock=1,
        url=url,
        note="Añadido manualmente mediante ingestor de enlaces"
    )

    card = format_detailed_bike_card(bike_id)
    return True, card, specs

def ingest_store(nombre: str, url: str, tipo: str = "online", direccion: str = "", marcas: str = "") -> Tuple[bool, str]:
    """
    Registra una nueva tienda en la base de datos de tiendas.
    """
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False, "❌ La URL de la tienda no es válida."

    slug = re.sub(r'[^a-zA-Z0-9]+', '_', nombre.lower()).strip('_')
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id FROM tiendas WHERE slug = ?", (slug,))
    exists = c.fetchone()
    if exists:
        c.execute("""
        UPDATE tiendas SET nombre = ?, tipo = ?, url = ?, direccion = ?, marcas = ?
        WHERE id = ?
        """, (nombre, tipo, url, direccion, marcas, exists["id"]))
        conn.commit()
        conn.close()
        return True, f"✅ Tienda <b>{nombre}</b> actualizada correctamente en la base de datos."
    else:
        c.execute("""
        INSERT INTO tiendas (slug, nombre, tipo, url, direccion, marcas)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (slug, nombre, tipo, url, direccion, marcas))
        conn.commit()
        conn.close()
        return True, f"✅ Nueva tienda <b>{nombre}</b> registrada con éxito en el catálogo."
