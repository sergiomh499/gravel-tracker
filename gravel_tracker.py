#!/usr/bin/env python3
"""
gravel_tracker.py - Interfaz Unificada y Retrocompatible para el Sistema Gravel Bot
Base territorial: Méndez Álvaro, Madrid | Perfil: 50% Asfalto / 50% Tierra | 1,69 m (Talla S)
"""

import sys
from gravel_bot.config import DB_PATH
from gravel_bot.db import get_connection, init_db, get_all_bikes, get_deals, upsert_bike, record_price
from gravel_bot.evaluator import calcular_rubrica, detect_bike_specs
from gravel_bot.pipeline import run_pipeline
from gravel_bot.notifier import test_telegram_connection, send_telegram_alert

def listar_ranking(filtro_tier=None):
    from gravel_bot.cli import cmd_list
    class DummyArgs:
        tier = filtro_tier
    cmd_list(DummyArgs())

def buscar_gangas(min_descuento=15.0):
    from gravel_bot.cli import cmd_deals
    class DummyArgs:
        min_discount = min_descuento
    cmd_deals(DummyArgs())

def agregar_modelo_cli():
    """Permite añadir o actualizar interactivamente un modelo con recalculo de rúbrica."""
    print("\n--- AÑADIR NUEVA BICICLETA / OFERTA ---")
    marca = input("Marca (ej. Orbea, Megamo, Conor): ")
    modelo = input("Modelo (ej. Terra H40): ")
    ano = int(input("Año (ej. 2024): ") or "2025")
    disc = input("Disciplina (gravel / carretera / fitness): ") or "gravel"
    trans = input("Transmisión (ej. Shimano GRX 2x10v): ")
    tipo_trans = input("Tipo Transmisión (2x10, 2x11, 2x12, 1x11, 1x12, 1x10): ")
    frenos = input("Frenos (ej. Shimano GRX Hidráulico): ")
    tipo_frenos = input("Tipo Frenos (hidraulico / semihidraulico / mecanico_doble): ")
    cuadro = input("Material Cuadro (ej. Aluminio Triple Conificado): ")
    horquilla = input("Material Horquilla (ej. Carbono): ")
    ejes = input("Ejes (ej. Pasantes 12mm): ") or "Pasantes 12 mm"
    udh = int(input("Tiene patilla UDH? (1=Si, 0=No): ") or "0")
    talla = input("Talla recomendada: ")
    pvp = float(input("Precio PVP (€): ") or "0")
    oferta = float(input("Precio Oferta (€): ") or str(pvp))
    url = input("URL de la oferta: ")
    talla_ok = input("Es talla adecuada para 1,69m? (s/n): ").lower() == 's'
    notas = input("Notas / Veredicto: ")

    c1, c2, c3, c4, c5, total, nota, tier = calcular_rubrica(disc, tipo_frenos, tipo_trans, cuadro, horquilla, udh, oferta, talla_ok)

    clean_slug = f"{marca.lower()}_{modelo.lower()}_{ano}".replace(" ", "_")
    bike_data = {
        "slug": clean_slug,
        "marca": marca,
        "modelo": modelo,
        "ano": ano,
        "disciplina": disc,
        "transmision": trans,
        "tipo_transmision": tipo_trans,
        "frenos": frenos,
        "tipo_frenos": tipo_frenos,
        "cuadro": cuadro,
        "horquilla": horquilla,
        "ejes": ejes,
        "patilla_udh": udh,
        "talla_recomendada_169": talla,
        "precio_pvp": pvp,
        "precio_oferta": oferta,
        "tienda_id": 1,
        "url_oferta": url,
        "en_stock": 1,
        "c1_frenos": c1,
        "c2_transmision": c2,
        "c3_cuadro": c3,
        "c4_precio": c4,
        "c5_talla": c5,
        "puntuacion_total": total,
        "nota": nota,
        "tier": tier,
        "notas_veredicto": notas
    }
    upsert_bike(bike_data)
    print(f"\n✅ Modelo registrado con éxito! Puntuación: {total}/100 | Nota: {nota}/10 | Clasificación: {tier}\n")

if __name__ == "__main__":
    init_db()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ["--list", "list"]:
            tier_arg = sys.argv[2] if len(sys.argv) > 2 else None
            listar_ranking(filtro_tier=tier_arg)
        elif cmd in ["--deals", "deals"]:
            buscar_gangas()
        elif cmd in ["--presupuesto", "presupuesto", "--recomendar", "recomendar", "--budget", "budget"]:
            from gravel_bot.budget_optimizer import optimize_for_budget, format_budget_recommendation_card
            from gravel_bot.config import RIDER_PROFILE

            budget_val = 1000.0
            height_val = RIDER_PROFILE.get("estatura_cm", 169)
            size_val = None
            channel_val = "all"
            json_mode = "--json" in sys.argv

            args = sys.argv[2:]
            idx = 0
            while idx < len(args):
                a = args[idx]
                if a in ["--altura", "-a"] and idx + 1 < len(args):
                    height_val = int(args[idx + 1])
                    idx += 2
                elif a in ["--talla", "-t", "--size"] and idx + 1 < len(args):
                    size_val = args[idx + 1]
                    idx += 2
                elif a in ["--local", "-l"]:
                    channel_val = "local_madrid"
                    idx += 1
                elif a in ["--canal", "-c"] and idx + 1 < len(args):
                    channel_val = args[idx + 1]
                    idx += 2
                elif a == "--json":
                    json_mode = True
                    idx += 1
                elif a.replace(".", "").isdigit():
                    budget_val = float(a)
                    idx += 1
                else:
                    idx += 1

            podio = optimize_for_budget(
                budget=budget_val,
                height_cm=height_val,
                size=size_val,
                channel=channel_val,
                include_stretch=True
            )
            print(format_budget_recommendation_card(podio, format="json" if json_mode else "text"))
        elif cmd in ["--web", "web", "--dashboard", "dashboard", "--ui", "ui"]:
            from gravel_bot.web_server import run_web_server
            port_val = 8080
            for idx, a in enumerate(sys.argv[2:], start=2):
                if a in ["--port", "-p"] and idx + 1 < len(sys.argv):
                    port_val = int(sys.argv[idx + 1])
                    break
                elif a.isdigit():
                    port_val = int(a)
                    break
            run_web_server(port=port_val)
        elif cmd in ["--pure-deals", "pure-deals", "--chollos", "--chollos-talla", "--chollos-zona"]:
            from gravel_bot.deal_detector import format_pure_deals_message
            from gravel_bot.config import RIDER_PROFILE
            max_p = None
            min_pct = 20.0
            solo_talla = (cmd in ["--chollos-talla", "--chollos-zona"] or any(a in sys.argv for a in ["--talla", "-t", "--size"]))
            zona_arg = None
            if any(a in sys.argv for a in ["--local", "-l", "--zona", "--chollos-zona"]):
                for idx, a in enumerate(sys.argv):
                    if a == "--zona" and idx + 1 < len(sys.argv):
                        zona_arg = sys.argv[idx + 1]
                        break
                if not zona_arg:
                    zona_arg = RIDER_PROFILE.get("zona", "Madrid")
            for arg in sys.argv[2:]:
                if arg in ["--talla", "-t", "--size", "--local", "-l", "--zona", "--chollos-zona", zona_arg]:
                    continue
                if arg.endswith("%"):
                    val = arg.rstrip("%")
                    if val.replace(".", "").isdigit():
                        min_pct = float(val)
                elif arg.replace(".", "").isdigit():
                    num = float(arg)
                    if num <= 70 and ("--pct" in sys.argv or "%" in "".join(sys.argv)):
                        min_pct = num
                    else:
                        max_p = num
            print(format_pure_deals_message(max_price=max_p, min_discount_pct=min_pct, solo_talla_compatible=solo_talla, zona_fisica=zona_arg))
        elif cmd in ["--historial", "historial", "--history"]:
            from gravel_bot.deal_detector import format_bike_price_history_message
            target = sys.argv[2] if len(sys.argv) > 2 else "Kalima"
            print(format_bike_price_history_message(target))
        elif cmd in ["--info", "info", "--ficha", "ficha", "--detalle"]:
            from gravel_bot.bike_inspector import format_detailed_bike_card
            query = sys.argv[2] if len(sys.argv) > 2 else "Conor Kalima"
            print(format_detailed_bike_card(query))
        elif cmd in ["--disponibles", "disponibles", "--catalogo", "catalogo"]:
            from gravel_bot.bike_inspector import format_available_bikes_message
            tier_f = sys.argv[2] if len(sys.argv) > 2 else None
            print(format_available_bikes_message(tier=tier_f))
        elif cmd in ["--stats", "stats"]:
            from gravel_bot.bike_inspector import format_database_stats_message
            print(format_database_stats_message())
        elif cmd in ["--add-url", "add-url", "--ingest"]:
            if len(sys.argv) > 2:
                from gravel_bot.url_ingestor import ingest_bike_url
                print(f"📥 Ingestando enlace de bicicleta: {sys.argv[2]}...")
                ok, res_msg, _ = ingest_bike_url(sys.argv[2])
                print(res_msg)
            else:
                print("⚠️ Uso: python3 gravel_tracker.py --add-url <URL_DEL_PRODUCTO>")
        elif cmd in ["--add-store", "add-store"]:
            if len(sys.argv) > 3:
                from gravel_bot.url_ingestor import ingest_store
                nombre = sys.argv[2]
                url = sys.argv[3]
                tipo = sys.argv[4] if len(sys.argv) > 4 else "online"
                ok, res_msg = ingest_store(nombre=nombre, url=url, tipo=tipo)
                print(res_msg)
            else:
                print("⚠️ Uso: python3 gravel_tracker.py --add-store <NOMBRE> <URL> [TIPO]")
        elif cmd in ["--tiendas", "tiendas", "--stores"]:
            from gravel_bot.store_recommender import format_stores_recommendation_message
            from gravel_bot.config import RIDER_PROFILE
            zona_param = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else RIDER_PROFILE.get("zona", "Madrid")
            print(format_stores_recommendation_message(zona=zona_param))
        elif cmd in ["--scan", "scan"]:
            run_pipeline(send_alerts=True, verbose=True)
        elif cmd in ["--test-telegram", "test-telegram"]:
            test_telegram_connection()
        elif cmd in ["--validate", "validate"]:
            from gravel_bot.validator import run_full_catalog_validation
            run_full_catalog_validation(auto_repair=True, verbose=True)
        elif cmd in ["--audit", "audit"]:
            from gravel_bot.catalog_auditor import run_catalog_audit
            limit_val = 20
            store_filter_val = None
            force_val = False
            args = sys.argv[2:]
            idx = 0
            while idx < len(args):
                a = args[idx]
                if a in ["--limit", "-l"] and idx + 1 < len(args):
                    limit_val = int(args[idx + 1])
                    idx += 2
                elif a in ["--all"]:
                    limit_val = None
                    idx += 1
                elif a in ["--tienda", "-t", "--store"] and idx + 1 < len(args):
                    store_filter_val = args[idx + 1]
                    idx += 2
                elif a in ["--force", "-f"]:
                    force_val = True
                    idx += 1
                elif a.isdigit():
                    limit_val = int(a)
                    idx += 1
                else:
                    idx += 1

            print("\n" + "="*80)
            print("🔍 INICIANDO AUDITORÍA VIVA DEL CATÁLOGO (Stock & Enlaces)")
            print("="*80)
            if store_filter_val:
                print(f"Tienda filtrada: {store_filter_val}")
            if limit_val:
                print(f"Límite de comprobaciones: {limit_val}")
            print(f"Modo forzado (ignorar 24h previas): {'Sí' if force_val else 'No'}\n")

            def on_progress(cur, tot, res):
                tag = "✅" if res.audit_status == "verificado" else ("⚠️" if res.audit_status == "sin_stock" else "❌")
                price_str = f"{res.live_price:.0f}€" if res.live_price else "-"
                print(f"[{cur}/{tot}] {tag} ID {res.bike_id:<3} | {res.audit_status:<12} | {price_str:<6} | {res.url[:45]}")

            report = run_catalog_audit(limit=limit_val, store_filter=store_filter_val, force=force_val, progress_callback=on_progress)
            print("\n" + "="*80)
            print("📊 RESUMEN DE AUDITORÍA DEL CATÁLOGO")
            print("="*80)
            print(f"Total analizados:       {report['auditados']}")
            print(f"Activos y en stock:     {report['verificados_ok']}")
            print(f"Agotados / Sin stock:   {report['sin_stock']}")
            print(f"Enlaces caídos:         {report['enlaces_caidos']}")
            print(f"Precios actualizados:   {report['precios_actualizados']}")
            print(f"Pendientes anti-bot:    {report['pendientes_antiban']}")
            print(f"Tiempo total:           {report['duracion_segundos']} s")
            print("="*80 + "\n")
        elif cmd in ["--re-score", "re-score", "--rescore", "rescore"]:
            from gravel_bot.evaluator import run_catalog_rescore
            dry_run = "--dry-run" in sys.argv
            print("\n" + "="*80)
            print(f"⚖️ RECALCULANDO RÚBRICA CALIBRADA C1..C6 {'(MODO DRY-RUN)' if dry_run else ''}")
            print("="*80)
            res = run_catalog_rescore(dry_run=dry_run)
            print(f"Total bicicletas procesadas: {res['total_bikes']}")
            print("\nDistribución de Tiers:")
            for tier_name, count in sorted(res['tier_counts'].items()):
                print(f" * {tier_name:<10}: {count} modelos")
            if not dry_run:
                print("\n✅ Base de datos actualizada con puntuaciones calibradas C1..C6 y factor garantía.")
            print("="*80 + "\n")
        elif cmd in ["--purge", "purge"]:
            from gravel_bot.db import purge_obsolete_and_junior_models
            res = purge_obsolete_and_junior_models()
            print(f"🧹 Purgado completado: {res['purged_bikes']} modelos no aptos/junior eliminados | {res['purged_prices']} entradas de historial.")
        elif cmd in ["--vs", "vs", "--compare"]:
            from gravel_bot.bike_inspector import format_bike_comparison_message
            b1 = sys.argv[2] if len(sys.argv) > 2 else "kalima"
            b2 = sys.argv[3] if len(sys.argv) > 3 else "jakar"
            print(format_bike_comparison_message(b1, b2))
        elif cmd in ["--desarrollo", "desarrollo", "--cadencia"]:
            from gravel_bot.gear_calculator import format_gear_simulation_message
            sub = sys.argv[2] if len(sys.argv) > 2 else "2x"
            print(format_gear_simulation_message(sub))
        elif cmd in ["--sync-doc", "sync-doc", "--sync"]:
            from gravel_bot.pipeline import sync_directorio_markdown
            sync_directorio_markdown()
        elif cmd in ["--add", "add"]:
            agregar_modelo_cli()
        elif cmd in ["--bot", "bot"]:
            from gravel_bot.bot_service import run_bot_polling
            dur = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
            run_bot_polling(duration_seconds=dur)
        elif cmd in ["--daemon", "daemon"]:
            from gravel_bot.cli import cmd_daemon
            cmd_daemon(None)
            print(f"Base de datos {DB_PATH} inicializada con éxito.")
        else:
            listar_ranking()
    else:
        listar_ranking()
        buscar_gangas()
