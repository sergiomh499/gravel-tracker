"""
gravel_bot/catalog_auditor.py
Motor de Auditoría en Vivo del Catálogo:
- Verificación de enlaces HTTP (200 OK vs 404/410 caídos)
- Detección de disponibilidad / stock por tienda y selectores universales
- Detección de fluctuaciones de precio (price drift) y sincronización con historial
- Actualización atómica en base de datos SQLite
"""

import re
import time
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List, Callable
from urllib.parse import urlparse

from gravel_bot.anti_ban import ResilientSession
from gravel_bot.db import (
    get_connection,
    update_bike_audit_status,
    record_price_if_changed,
)


@dataclass
class AuditResult:
    bike_id: int
    url: str
    status_code: int
    audit_status: str  # 'verificado', 'sin_stock', 'enlace_caido', 'pendiente'
    in_stock: int  # 1 o 0
    live_price: Optional[float] = None
    price_changed: bool = False
    old_price: Optional[float] = None
    notes: str = ""


# Indicadores de agotado por tienda y patrones universales de comercio electrónico
OUT_OF_STOCK_PATTERNS = [
    # Schema.org JSON-LD o Microdata
    r'https?://schema\.org/OutOfStock',
    r'"availability"\s*:\s*"[^"]*OutOfStock"',
    r'"itemAvailability"\s*:\s*"[^"]*OutOfStock"',
    r'"inStock"\s*:\s*false',
    # Selectores CSS / atributos HTML comunes
    r'class="[^"]*(?:out-of-stock|is-out-of-stock|agotado|sin-stock|no-disponible|stock-out|product-unavailable)[^"]*"',
    r'data-stock="0"',
    r'data-available="false"',
    # Textos explícitos de compra deshabilitada
    r'(?:producto\s+agotado|sin\s+existencias|temporalmente\s+sin\s+stock|no\s+disponible\s+en\s+tienda|artículo\s+agotado|fuera\s+de\s+stock)',
    r'(?:este\s+producto\s+ya\s+no\s+está\s+disponible|vendida|sold\s+out|bici\s+vendida)',
    r'<button[^>]+disabled[^>]*>(?:Agotado|Sin stock|No disponible|Avísame)</button>',
]

IN_STOCK_CONFIRMATION_PATTERNS = [
    r'https?://schema\.org/InStock',
    r'"availability"\s*:\s*"[^"]*InStock"',
    r'"inStock"\s*:\s*true',
    r'class="[^"]*(?:in-stock|en-stock|disponible)[^"]*"',
    r'<button[^>]+(?:submit|add-to-cart|btn-buy|btn-cart)[^>]*>(?:Añadir|Comprar|Agregar|Añadir a la cesta|Añadir al carrito)',
]


def extract_price_from_html(html: str) -> Optional[float]:
    """Extrae el precio de oferta actual desde metaetiquetas, microdatos o bloques de precio."""
    if not html:
        return None

    # 1. Metadatos directos de producto (muy precisos)
    meta_patterns = [
        r'<meta\s+property=["\']product:price:amount["\']\s+content=["\']([\d\.,]+)["\']',
        r'<meta\s+name=["\']twitter:data1["\']\s+value=["\']([\d\.,]+)\s*€?["\']',
        r'<meta\s+property=["\']og:price:amount["\']\s+content=["\']([\d\.,]+)["\']',
        r'<meta\s+itemprop=["\']price["\']\s+content=["\']([\d\.,]+)["\']',
    ]
    for p in meta_patterns:
        m = re.search(p, html, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(",", ".").strip()
            try:
                val = float(raw)
                if 200.0 <= val <= 15000.0:
                    return val
            except ValueError:
                pass

    # 2. JSON-LD estructurado
    json_ld_matches = re.findall(r'<script\s+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    for block in json_ld_matches:
        try:
            # Buscar fragmentos de precio dentro del JSON-LD
            p_match = re.search(r'"price"\s*:\s*["\']?([\d\.]+)["\']?', block)
            if p_match:
                val = float(p_match.group(1))
                if 200.0 <= val <= 15000.0:
                    return val
        except Exception:
            pass

    # 3. Clases HTML típicas de precio oferta
    price_span_matches = re.findall(r'class=["\'][^"\']*(?:current-price|price-current|precio-oferta|special-price|sales-price)[^"\']*["\'][^>]*>\s*([\d\.,\s]+)€?', html, re.IGNORECASE)
    for raw in price_span_matches:
        cleaned = raw.replace(".", "").replace(",", ".").replace("€", "").strip()
        try:
            val = float(cleaned)
            if 200.0 <= val <= 15000.0:
                return val
        except ValueError:
            pass

    return None


def detect_stock_status(html: str) -> Tuple[int, str]:
    """
    Analiza el HTML para discernir si el producto está en stock (1) o agotado/descatalogado (0).
    Retorna: (in_stock, audit_status_tag)
    """
    if not html:
        return 0, "enlace_caido"

    # Verificar señales de fuera de stock
    for pat in OUT_OF_STOCK_PATTERNS:
        if re.search(pat, html, re.IGNORECASE):
            return 0, "sin_stock"

    # Verificar señales positivas de stock
    for pat in IN_STOCK_CONFIRMATION_PATTERNS:
        if re.search(pat, html, re.IGNORECASE):
            return 1, "verificado"

    # Si no hay señal explícita de agotado, se considera disponible con reserva
    return 1, "verificado"


def audit_single_bike_url(bike: Dict[str, Any], timeout: int = 10) -> AuditResult:
    """Ejecuta la auditoría viva de un enlace individual de bicicleta."""
    bike_id = bike["id"]
    url = bike.get("url_oferta", "").strip()
    old_price = float(bike.get("precio_oferta", 0.0))

    if not url or not url.startswith("http"):
        return AuditResult(
            bike_id=bike_id,
            url=url,
            status_code=0,
            audit_status="enlace_caido",
            in_stock=0,
            old_price=old_price,
            notes="URL de oferta no configurada o inválida",
        )

    # Realizar petición resiliente con control anti-bot
    html, status_code, meta = ResilientSession.fetch(url, timeout=timeout, max_retries=1)

    # Enlaces caídos definitivos
    if status_code in (404, 410):
        res = AuditResult(
            bike_id=bike_id,
            url=url,
            status_code=status_code,
            audit_status="enlace_caido",
            in_stock=0,
            old_price=old_price,
            notes=f"Enlace roto o producto eliminado (HTTP {status_code})",
        )
        update_bike_audit_status(bike_id, "enlace_caido", in_stock=0, notes=res.notes)
        return res

    # Bloqueos preventivos o captchas (no marcar como muerto si sólo hubo reto temporal)
    if status_code in (403, 429) or (meta and "captcha" in str(meta.get("error", ""))):
        res = AuditResult(
            bike_id=bike_id,
            url=url,
            status_code=status_code,
            audit_status="pendiente",
            in_stock=int(bike.get("en_stock", 1)),
            old_price=old_price,
            notes="Protección anti-bot activa; se mantiene estado previo",
        )
        update_bike_audit_status(bike_id, "pendiente", in_stock=res.in_stock, notes=res.notes)
        return res

    # 200 OK: Evaluar contenido
    if status_code == 200 and html:
        in_stock, audit_status = detect_stock_status(html)
        live_price = extract_price_from_html(html)

        price_changed = False
        notes_parts = []

        if in_stock == 0:
            notes_parts.append("Producto marcado como agotado/sin stock en tienda")
        else:
            notes_parts.append("Enlace vivo y verificado en stock")

        # Verificar price drift
        if live_price is not None and abs(live_price - old_price) >= 1.0:
            price_changed = True
            diff = live_price - old_price
            sign = "+" if diff > 0 else ""
            notes_parts.append(f"Precio actualizado: {old_price:.0f}€ -> {live_price:.0f}€ ({sign}{diff:.0f}€)")
            # Registrar en el historial de precios
            record_price_if_changed(
                bike_id=bike_id,
                store_id=bike.get("tienda_id"),
                price=live_price,
                size=bike.get("talla_recomendada_169", ""),
                in_stock=in_stock,
                url=url,
                note=f"Audit live drift: {sign}{diff:.0f}€",
            )

        notes_str = " | ".join(notes_parts)
        effective_price = live_price if price_changed else None

        update_bike_audit_status(
            bike_id=bike_id,
            audit_status=audit_status,
            in_stock=in_stock,
            live_price=effective_price,
            notes=notes_str,
        )

        return AuditResult(
            bike_id=bike_id,
            url=url,
            status_code=status_code,
            audit_status=audit_status,
            in_stock=in_stock,
            live_price=live_price,
            price_changed=price_changed,
            old_price=old_price,
            notes=notes_str,
        )

    # Errores desconocidos de red o timeout
    res = AuditResult(
        bike_id=bike_id,
        url=url,
        status_code=status_code,
        audit_status="pendiente",
        in_stock=int(bike.get("en_stock", 1)),
        old_price=old_price,
        notes=f"Respuesta inesperada (HTTP {status_code})",
    )
    return res


def run_catalog_audit(
    limit: Optional[int] = None,
    store_filter: Optional[str] = None,
    force: bool = False,
    progress_callback: Optional[Callable[[int, int, AuditResult], None]] = None,
) -> Dict[str, Any]:
    """
    Coordina la auditoría de enlaces en lote:
    - Recupera bicicletas del catálogo
    - Aplica filtros opcionales de tienda o antigüedad de auditoría
    - Ejecuta comprobaciones con rate-limiting y reporte de resultados
    """
    t_start = time.time()
    conn = get_connection()
    c = conn.cursor()

    query = """
    SELECT b.*, t.nombre as tienda_nombre, t.slug as tienda_slug
    FROM bicicletas b
    LEFT JOIN tiendas t ON b.tienda_id = t.id
    WHERE b.url_oferta IS NOT NULL AND b.url_oferta != ''
    """
    params = []
    if store_filter:
        query += " AND (LOWER(t.nombre) LIKE ? OR LOWER(t.slug) LIKE ?)"
        params.extend([f"%{store_filter.lower()}%", f"%{store_filter.lower()}%"])

    if not force:
        # Priorizar enlaces que nunca se auditaron o cuya última auditoría fue hace más de 24h
        cutoff_date = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        query += " AND (b.fecha_auditoria IS NULL OR b.fecha_auditoria < ?)"
        params.append(cutoff_date)

    query += " ORDER BY b.fecha_auditoria ASC NULLS FIRST, b.puntuacion_total DESC"

    if limit and limit > 0:
        query += f" LIMIT {int(limit)}"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    total_candidates = len(rows)
    report = {
        "total_candidatos": total_candidates,
        "auditados": 0,
        "verificados_ok": 0,
        "sin_stock": 0,
        "enlaces_caidos": 0,
        "precios_actualizados": 0,
        "pendientes_antiban": 0,
        "duracion_segundos": 0.0,
        "detalles": [],
    }

    if total_candidates == 0:
        report["duracion_segundos"] = round(time.time() - t_start, 2)
        return report

    for idx, row in enumerate(rows, start=1):
        bike_dict = dict(row)
        res = audit_single_bike_url(bike_dict)

        report["auditados"] += 1
        if res.audit_status == "verificado":
            report["verificados_ok"] += 1
        elif res.audit_status == "sin_stock":
            report["sin_stock"] += 1
        elif res.audit_status == "enlace_caido":
            report["enlaces_caidos"] += 1
        else:
            report["pendientes_antiban"] += 1

        if res.price_changed:
            report["precios_actualizados"] += 1

        report["detalles"].append({
            "id": res.bike_id,
            "modelo": bike_dict.get("modelo"),
            "url": res.url,
            "status": res.audit_status,
            "in_stock": res.in_stock,
            "live_price": res.live_price,
            "old_price": res.old_price,
            "price_changed": res.price_changed,
            "notes": res.notes,
        })

        if progress_callback:
            progress_callback(idx, total_candidates, res)

    report["duracion_segundos"] = round(time.time() - t_start, 2)
    return report
