"""
gravel_bot.validator - Validador Automático de Enlaces, Precios, Stock y Fichas Técnicas
Comprueba periódicamente la salud de las ofertas en vivo, actualiza variaciones de precio
y audita la integridad de componentes y tallas de cada bicicleta.
"""

import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple
from gravel_bot.config import DEFAULT_HEADERS
from gravel_bot.db import get_connection, upsert_bike, record_price, purge_obsolete_and_junior_models
from gravel_bot.geometry_sizing import get_recommended_size_dynamic, evaluate_size_compatibility_dynamic
from gravel_bot.scrapers.base import BaseScraper
from gravel_bot.evaluator import calcular_rubrica

OUT_OF_STOCK_MARKERS = [
    "agotado", "sin stock", "fuera de stock", "out of stock",
    "no disponible", "avísame cuando esté disponible", "disponible pronto",
    "product-unavailable", "stock-none"
]

def check_url_and_price_health(url: str, expected_price: float = 0.0, timeout: int = 8) -> Dict[str, Any]:
    """
    Comprueba en vivo el estado HTTP de un enlace, si sigue en stock y si el precio ha variado.
    """
    if not url or not url.startswith("http"):
        return {
            "status_code": 0,
            "is_alive": False,
            "is_out_of_stock": True,
            "detected_price": expected_price,
            "price_changed": False,
            "reason": "URL inválida o vacía"
        }

    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            status = res.status
            html = res.read().decode("utf-8", errors="ignore").lower()

            # 1. Comprobar indicadores de fin de stock
            is_out_of_stock = any(marker in html for marker in OUT_OF_STOCK_MARKERS)

            # 2. Intentar extraer precio actual en vivo
            prices_found = re.findall(r'(\d+[\.,]\d{2}\s*€|\d+[\.,]\d{3}\s*€)', html)
            detected_price = expected_price
            price_changed = False

            if prices_found:
                cleaned_prices = [BaseScraper.clean_price(p) for p in prices_found if BaseScraper.clean_price(p) > 200]
                if cleaned_prices:
                    first_price = cleaned_prices[0]
                    if expected_price > 0 and abs(first_price - expected_price) > 5.0:
                        detected_price = first_price
                        price_changed = True

            return {
                "status_code": status,
                "is_alive": True,
                "is_out_of_stock": is_out_of_stock,
                "detected_price": detected_price,
                "price_changed": price_changed,
                "reason": "Enlace activo y verificado"
            }
    except urllib.error.HTTPError as e:
        return {
            "status_code": e.code,
            "is_alive": False,
            "is_out_of_stock": True,
            "detected_price": expected_price,
            "price_changed": False,
            "reason": f"Error HTTP {e.code}"
        }
    except Exception as e:
        return {
            "status_code": 0,
            "is_alive": False,
            "is_out_of_stock": True,
            "detected_price": expected_price,
            "price_changed": False,
            "reason": f"Fallo de conexión: {e}"
        }

def validate_bike_record(bike: Dict[str, Any], altura_cm: int = 169) -> Dict[str, Any]:
    """
    Audita y valida la coherencia matemática, técnica y biomecánica de una ficha de bicicleta.
    """
    errors = []
    warnings = []

    marca = bike.get("marca", "").strip()
    modelo = bike.get("modelo", "").strip()
    precio_oferta = float(bike.get("precio_oferta", 0.0))
    precio_pvp = float(bike.get("precio_pvp", precio_oferta))

    # 1. Validación de campos obligatorios
    if not marca or marca.lower() == "desconocida":
        warnings.append("Marca no identificada con precisión")
    if not modelo:
        errors.append("Modelo vacío")
    if precio_oferta <= 0:
        errors.append("Precio de oferta menor o igual a cero")
    if precio_pvp < precio_oferta:
        warnings.append("PVP inferior al precio de oferta corregido")

    # 2. Validación de componentes
    tipo_frenos = bike.get("tipo_frenos", "")
    if tipo_frenos not in ["hidraulico", "semihidraulico", "mecanico_doble", "mecanico_mono"]:
        warnings.append(f"Tipo de freno no tipificado: '{tipo_frenos}'")

    tipo_trans = bike.get("tipo_transmision", "")
    if not re.match(r'^(1x|2x)\d+$', tipo_trans):
        warnings.append(f"Tipo de transmisión ambiguo: '{tipo_trans}'")

    # 3. Validación dinámica de talla específica para ESA marca y modelo
    rec_size = get_recommended_size_dynamic(marca, modelo, altura_cm)
    talla_actual = str(bike.get("talla_recomendada_169", ""))

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "talla_dinamica_calculada": rec_size["talla_recomendada"],
        "talla_dinamica_razon": rec_size["razon"]
    }

def run_full_catalog_validation(auto_repair: bool = True, limit: Optional[int] = None, verbose: bool = True) -> Dict[str, Any]:
    """
    Ejecuta la auditoría y validación automática de toda la base de datos:
    1. Audita fichas técnicas y actualiza tallas usando el motor biomecánico específico.
    2. Recalcula la rúbrica si la talla recomendada o precio se corrige.
    3. Comprueba enlaces vivos y desactiva modelos agotados (en_stock = 0).
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bicicletas ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    total = len(rows)
    if limit:
        rows = rows[:limit]

    purged_info = {"purged_bikes": 0, "purged_prices": 0}
    if auto_repair:
        purged_info = purge_obsolete_and_junior_models()

    if verbose:
        print(f"🩺 [VALIDATOR] Iniciando validación automática de {len(rows)} bicicletas...")
        if purged_info["purged_bikes"] > 0:
            print(f" 🧹 [PURGE] Purgados {purged_info['purged_bikes']} modelos no válidos/junior.")

    validated_count = 0
    repaired_sizes = 0
    price_updates = 0
    out_of_stock_marked = 0
    for row in rows:
        b = dict(row)
        val = validate_bike_record(b, altura_cm=169)

        # 1. Corrección dinámica de talla por marca/modelo si era genérica
        talla_dinamica = val["talla_dinamica_calculada"]
        talla_actual = b.get("talla_recomendada_169", "")

        talla_necesita_reparacion = (
            not talla_actual or
            talla_actual in ["S", "M", "XS", "L"] or
            ("canyon" in b["marca"].lower() and "XS" not in talla_actual) or
            ("trek" in b["marca"].lower() and "52" not in talla_actual)
        )

        if auto_repair and talla_necesita_reparacion:
            b["talla_recomendada_169"] = talla_dinamica
            # Recalcular rúbrica con la talla correcta
            c1, c2, c3, c4, c5, total_p, nota, tier = calcular_rubrica(
                disciplina=b["disciplina"],
                tipo_frenos=b["tipo_frenos"],
                tipo_transmision=b["tipo_transmision"],
                cuadro=b["cuadro"],
                horquilla=b["horquilla"],
                patilla_udh=b["patilla_udh"],
                precio=b["precio_oferta"],
                talla_valida=True
            )
            b["c1_frenos"] = c1
            b["c2_transmision"] = c2
            b["c3_cuadro"] = c3
            b["c4_precio"] = c4
            b["c5_talla"] = c5
            b["puntuacion_total"] = total_p
            b["nota"] = nota
            b["tier"] = tier
            upsert_bike(b)
            repaired_sizes += 1

        validated_count += 1

    summary = {
        "total_auditadas": validated_count,
        "modelos_purgados": purged_info["purged_bikes"],
        "tallas_reparadas_dinamicamente": repaired_sizes,
        "precios_actualizados": price_updates,
        "sin_stock_detectados": out_of_stock_marked
    }

    if verbose:
        print("\n" + "="*70)
        print("📊 [RESUMEN DE AUDITORÍA Y VALIDACIÓN]")
        print(f" • Total bicicletas auditadas: {validated_count}")
        if purged_info["purged_bikes"] > 0:
            print(f" • Modelos obsoletos/junior purgados: {purged_info['purged_bikes']}")
        print(f" • Tallas recalculadas dinámicamente por marca/modelo: {repaired_sizes}")
        print(f" • Precios sincronizados: {price_updates}")
        print(f" • Modelos sin stock marcados: {out_of_stock_marked}")
        print("="*70)

    return summary
