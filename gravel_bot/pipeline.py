"""
gravel_bot.pipeline - Motor de Automatización, Ingesta, Valoración y Alertas
"""

import time
from typing import Dict, Any, List
from gravel_bot.config import ALERT_CRITERIA
from gravel_bot.db import (
    init_db, get_or_create_store, upsert_bike,
    record_price_if_changed, was_alert_sent, mark_alert_sent
)
from gravel_bot.evaluator import detect_bike_specs
from gravel_bot.scrapers import get_all_scrapers
from gravel_bot.notifier import send_telegram_alert

def run_pipeline(send_alerts: bool = True, verbose: bool = True) -> Dict[str, Any]:
    """
    Ejecuta el pipeline completo de rastreo:
    1. Descarga ofertas de todas las tiendas configuradas (sin usar LLMs).
    2. Parsea componentes y calcula la rúbrica matemática 50/50 para 1,69m.
    3. Almacena o actualiza en SQLite (gravel_madrid.db).
    4. Dispara alerta automática en Telegram si encuentra una ganga en Tier S+ o Tier S.
    """
    init_db()

    scrapers = get_all_scrapers()
    total_scraped = 0
    saved_count = 0
    alerts_triggered = 0
    top_findings: List[Dict[str, Any]] = []

    if verbose:
        print("🚀 [PIPELINE] Iniciando escaneo automático de tiendas...")

    for scraper in scrapers:
        if verbose:
            print(f"📡 [SCAN] Consultando {scraper.store_name} ({scraper.base_url})...")
        try:
            items = scraper.scrape()
            if verbose:
                print(f"   ↳ {len(items)} productos extraídos de {scraper.store_name}")
            total_scraped += len(items)

            # Asegurar tienda en base de datos
            store_id = get_or_create_store(
                slug=scraper.store_slug,
                nombre=scraper.store_name,
                tipo=scraper.store_type,
                url=scraper.base_url
            )

            for item in items:
                # 1. Extracción y Rúbrica
                specs = detect_bike_specs(
                    title=item["title"],
                    price=item["price"],
                    sizes=item.get("sizes", [])
                )
                specs["tienda_id"] = store_id
                specs["tienda_nombre"] = scraper.store_name
                specs["url_oferta"] = item["url"]
                specs["precio_pvp"] = item.get("pvp", item["price"])
                specs["precio_oferta"] = item["price"]

                # 2. Persistencia en SQLite
                bike_id = upsert_bike(specs)
                saved_count += 1

                # 3. Registro en Historial de Precios (guarda cada cambio de precio y fecha)
                record_price_if_changed(
                    bike_id=bike_id,
                    store_id=store_id,
                    price=item["price"],
                    size=", ".join(item.get("sizes", [])) or specs["talla_recomendada_169"],
                    in_stock=1,
                    url=item["url"],
                    note=f"Rastreo automático {scraper.store_name}"
                )
                # 4. Evaluación de Criterio de Alerta (Tier S+ o Tier S con nota >= umbral y precio accesible)
                is_top_tier = specs["tier"] in ALERT_CRITERIA["tiers_permitidos"]
                is_good_score = specs["nota"] >= ALERT_CRITERIA["nota_minima"]
                is_affordable = specs["precio_oferta"] <= ALERT_CRITERIA["max_precio"]
                is_valid_size = specs["talla_recomendada_169"] != "No compatible"

                if is_top_tier and is_good_score and is_affordable and is_valid_size:
                    top_findings.append(specs)
                    if send_alerts and not was_alert_sent(bike_id, specs["precio_oferta"]):
                        if verbose:
                            print(f"\n🚨 [ALERTA DISPARADA] {specs['marca']} {specs['modelo']} -> {specs['tier']} ({specs['nota']}/10) - {specs['precio_oferta']} €")
                        sent = send_telegram_alert(specs)
                        if sent:
                            mark_alert_sent(bike_id, specs["precio_oferta"], specs["tier"], specs["nota"])
                            alerts_triggered += 1

        except Exception as e:
            print(f"❌ [ERROR] Fallo en scraper {scraper.name}: {e}")

    summary = {
        "scraped_count": total_scraped,
        "saved_count": saved_count,
        "alerts_triggered": alerts_triggered,
        "top_findings": top_findings
    }

    if verbose:
        print("\n" + "="*70)
        print("📊 [RESUMEN DE ESCANEO AUTOMÁTICO]")
        print(f" • Total productos rastreados: {total_scraped}")
        print(f" • Bicicletas indexadas/actualizadas: {saved_count}")
        print(f" • Nuevas gangas Tier S+/S encontradas: {len(top_findings)}")
        print(f" • Alertas enviadas a Telegram: {alerts_triggered}")
        print("="*70)

    return summary
