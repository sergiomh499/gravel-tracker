"""
gravel_bot.pipeline - Motor de Automatización, Ingesta, Valoración y Alertas
"""

import time
import sqlite3
import re
from typing import Dict, Any, List
from gravel_bot.config import ALERT_CRITERIA, DB_PATH
from gravel_bot.db import (
    init_db, get_or_create_store, upsert_bike,
    record_price_if_changed, was_alert_sent, mark_alert_sent
)
from gravel_bot.evaluator import detect_bike_specs
from gravel_bot.scrapers import get_all_scrapers
from gravel_bot.notifier import send_telegram_alert


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


def run_pipeline(send_alerts: bool = True, verbose: bool = True) -> Dict[str, Any]:
    """
    Ejecuta el pipeline completo de rastreo y actualización automática:
    1. Descarga ofertas de todas las tiendas configuradas (sin usar LLMs).
    2. Parsea componentes y calcula la rúbrica matemática 50/50 para 1,69m.
    3. Almacena o actualiza en SQLite (gravel_madrid.db).
    4. Sincroniza automáticamente directorio_bicicletas.md.
    5. Dispara alerta automática en Telegram si encuentra una ganga en Tier S+ o Tier S.
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

                # 3. Registro en Historial de Precios
                record_price_if_changed(
                    bike_id=bike_id,
                    store_id=store_id,
                    price=item["price"],
                    size=", ".join(item.get("sizes", [])) or specs["talla_recomendada_169"],
                    in_stock=1,
                    url=item["url"],
                    note=f"Rastreo automático {scraper.store_name}"
                )

                # 4. Evaluación de Criterio de Alerta
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

    # 5. Sincronizar directorio markdown automáticamente
    sync_directorio_markdown()

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
