"""
gravel_bot.pipeline - Motor de Automatización, Ingesta, Valoración y Alertas
"""

import time
import sqlite3
import re
import json
from typing import Dict, Any, List
from gravel_bot.config import ALERT_CRITERIA, DB_PATH
from gravel_bot.db import (
    init_db, get_or_create_store, upsert_bike,
    record_price_if_changed, check_price_drop, was_alert_sent, mark_alert_sent,
    purge_obsolete_and_junior_models
)
from gravel_bot.evaluator import detect_bike_specs
from gravel_bot.scrapers import get_all_scrapers
from gravel_bot.notifier import send_telegram_alert, format_price_drop_message, is_valid_purchase_url

def sync_directorio_markdown(db_path: str = DB_PATH, md_path: str = "directorio_bicicletas.md"):
    """
    Sincroniza y actualiza automáticamente el documento directorio_bicicletas.md
    con el ranking en tiempo real de modelos en stock procedentes de la base de datos.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("""
            SELECT b.marca, b.modelo, b.precio_oferta, b.precio_pvp, b.puntuacion_total, b.tier, b.nota,
                   b.talla_recomendada_169, t.nombre as tienda, b.en_stock, b.url_oferta
            FROM bicicletas b
            LEFT JOIN tiendas t ON b.tienda_id = t.id
            WHERE b.precio_oferta <= 1350 
              AND b.talla_recomendada_169 NOT IN ('No compatible', 'Incompatible (No gravel)')
              AND (b.disciplina IS NULL OR b.disciplina = 'gravel')
              AND b.marca NOT IN ('Desconocida')
              AND b.modelo NOT LIKE '%junior%'
              AND b.modelo NOT LIKE '%niño%'
              AND b.modelo NOT LIKE '%infantil%'
              AND b.tier != 'Tier C'
            ORDER BY b.en_stock DESC, b.puntuacion_total DESC
            LIMIT 15
        """)
        rows = c.fetchall()
        conn.close()

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        table = "### 📡 Monitor de Stock en Tiempo Real (Actualizado Automáticamente)\n"
        table += f"*Última sincronización robótica:* `{timestamp}` | *Filtro:* $\\le 1.350$ € · Talla S/XS · 50% Asfalto / 50% Tierra\n\n"
        table += "| # | Modelo | Precio Oferta (PVP) | Tier | Nota | Talla | Tienda | Estado Stock |\n"
        table += "| :-: | :--- | :---: | :---: | :---: | :---: | :--- | :---: |\n"

        for i, r in enumerate(rows, 1):
            stock_badge = "🟢 En Stock" if r["en_stock"] else "🔴 Agotada"
            pvp_str = f"({r['precio_pvp']} €)" if r["precio_pvp"] and r["precio_pvp"] != r["precio_oferta"] else ""
            link = f"[{r['marca']} {r['modelo']}]({r['url_oferta']})" if r["url_oferta"] else f"{r['marca']} {r['modelo']}"
            table += f"| {i} | {link} | **{r['precio_oferta']} €** *{pvp_str}* | **{r['tier']}** | {r['nota']}/10 | {r['talla_recomendada_169']} | {r['tienda']} | {stock_badge} |\n"

        # Leer archivo existente
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Reemplazar o insertar bloque de monitor de stock
        marker_start = "### 📡 Monitor de Stock en Tiempo Real"
        marker_end = "## Tier S+: Las Compras Maestras"

        if marker_start in content:
            idx_start = content.find(marker_start)
            idx_end = content.find(marker_end)
            new_content = content[:idx_start] + table + "\n---\n\n" + content[idx_end:]
        else:
            idx_tier = content.find(marker_end)
            if idx_tier != -1:
                new_content = content[:idx_tier] + table + "\n---\n\n" + content[idx_tier:]
            else:
                new_content = content + "\n\n" + table

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"📄 [AUTO-DOC] {md_path} sincronizado con {len(rows)} modelos líderes en stock.")
    except Exception as e:
        print(f"⚠️ [AUTO-DOC] Error sincronizando {md_path}: {e}")
def export_catalog_snapshot(db_path: str = DB_PATH, json_path: str = "catalog_snapshot.json"):
    """
    Exporta un snapshot en formato JSON plano y determinista de todas las bicicletas activas
    para control de versiones limpio, diffs legibles en Git y respaldo frente a corrupciones de BD.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT b.id, b.marca, b.modelo, b.tier, b.nota, b.precio_oferta, b.precio_pvp,
                   b.talla_recomendada_169, b.tallas_disponibles, b.transmision, b.frenos,
                   t.nombre as tienda, b.url_oferta
            FROM bicicletas b
            LEFT JOIN tiendas t ON b.tienda_id = t.id
            WHERE b.en_stock = 1
            ORDER BY b.tier ASC, b.nota DESC, b.precio_oferta ASC
        """)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
        print(f"📦 [SNAPSHOT] {json_path} generado con {len(rows)} bicicletas activas en formato texto.")
    except Exception as e:
        print(f"⚠️ [SNAPSHOT] Error exportando {json_path}: {e}")



def run_pipeline(send_alerts: bool = True, verbose: bool = True, deep_scan: bool = False) -> Dict[str, Any]:
    """
    Ejecuta el pipeline completo de rastreo y actualización automática:
    1. Descarga ofertas de todas las tiendas configuradas (sin usar LLMs).
    2. Parsea componentes y calcula la rúbrica matemática 50/50 para 1,69m.
    3. Almacena o actualiza en SQLite (gravel_madrid.db).
    4. Sincroniza automáticamente directorio_bicicletas.md.
    5. Dispara alerta automática en Telegram si encuentra una ganga en Tier S+ o Tier S.
    """
    init_db()
    # FR-02: barrido de ruido (junior/infantil/test/marca 'Desconocida') en el propio rastreo,
    # no solo en auditorías — evita ventanas donde las superficies de cliente muestran resebrados.
    purged = purge_obsolete_and_junior_models()
    if purged.get("purged_bikes") or purged.get("purged_prices"):
        print(f"🧹 [PURGA] {purged.get('purged_bikes', 0)} modelos y {purged.get('purged_prices', 0)} registros de precios fuera de catálogo eliminados.")
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
            if deep_scan and hasattr(scraper, "deep_pages"):
                items = scraper.scrape(deep=True)
            else:
                items = scraper.scrape()
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
                item_sizes = item.get("sizes", [])
                specs = detect_bike_specs(
                    title=item["title"],
                    description=item.get("description", ""),
                    price=item["price"],
                    sizes=item_sizes
                )
                if specs.get("disciplina") in ["no_bicicleta", "test_artifact"]:
                    continue
                specs["tienda_id"] = store_id
                specs["url_oferta"] = item["url"]
                pvp_val = item.get("pvp")
                specs["precio_pvp"] = pvp_val if (pvp_val and pvp_val > item["price"]) else specs.get("precio_pvp", item["price"])
                specs["precio_oferta"] = item["price"]
                if item_sizes:
                    specs["tallas_disponibles"] = ", ".join([str(s) for s in item_sizes])
                # 2. Persistencia en SQLite
                bike_id = upsert_bike(specs)
                saved_count += 1

                # 3. Comprobación y Registro en Historial de Precios
                price_drop = check_price_drop(bike_id, item["price"])
                record_price_if_changed(
                    bike_id=bike_id,
                    store_id=store_id,
                    price=item["price"],
                    size=", ".join(item.get("sizes", [])) or specs["talla_recomendada_169"],
                    in_stock=1,
                    url=item["url"],
                    note=f"Rastreo automático {scraper.store_name}"
                )

                # Notificación prioritaria de bajada de precio detectada
                if price_drop and send_alerts:
                    specs_with_store = dict(specs)
                    specs_with_store["tienda_nombre"] = scraper.store_name
                    drop_msg = format_price_drop_message(specs_with_store, price_drop)
                    if verbose:
                        print(f"\n📉 [BAJADA DE PRECIO] {specs['marca']} {specs['modelo']} -> -{price_drop['drop_eur']}€ (-{price_drop['drop_pct']}%) a {item['price']}€")
                    send_telegram_alert(drop_msg)
                    alerts_triggered += 1
                # 4. Evaluación de Criterio de Alerta
                is_top_tier = specs["tier"] in ALERT_CRITERIA["tiers_permitidos"]
                is_good_score = specs["nota"] >= ALERT_CRITERIA["nota_minima"]
                is_affordable = specs["precio_oferta"] <= ALERT_CRITERIA["max_precio"]
                is_valid_size = specs["talla_recomendada_169"] != "No compatible"
                has_valid_link = is_valid_purchase_url(specs.get("url_oferta"))

                if is_top_tier and is_good_score and is_affordable and is_valid_size and has_valid_link:
                    if send_alerts and not was_alert_sent(bike_id, specs["precio_oferta"]):
                        if verbose:
                            print(f"\n🚨 [ALERTA DISPARADA] {specs['marca']} {specs['modelo']} -> {specs['tier']} ({specs['nota']}/10) - {specs['precio_oferta']} €")
                        sent = send_telegram_alert(specs)
                        if sent:
                            mark_alert_sent(bike_id, specs["precio_oferta"], specs["tier"], specs["nota"])
                            alerts_triggered += 1

        except Exception as e:
            print(f"❌ [ERROR] Fallo en scraper {scraper.name}: {e}")

    # FR-02: purga adicional tras el rastreo — el loop de scrapers puede resembrar
    # 'Desconocida'; hay que limpiar ANTES de regenerar snapshot y directorio (SC-02).
    purged_end = purge_obsolete_and_junior_models()
    if purged_end.get("purged_bikes") or purged_end.get("purged_prices"):
        print(f"🧹 [PURGA] {purged_end.get('purged_bikes', 0)} modelos y {purged_end.get('purged_prices', 0)} registros de precios fuera de catálogo eliminados (post-rastreo).")

    # 5. Sincronizar directorio markdown y snapshot JSON automáticamente
    sync_directorio_markdown()
    export_catalog_snapshot()

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
