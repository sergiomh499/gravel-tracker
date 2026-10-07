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
        elif cmd in ["--pure-deals", "pure-deals", "--chollos", "--chollos-talla"]:
            from gravel_bot.deal_detector import format_pure_deals_message
            max_p = None
            min_pct = 20.0
            solo_talla = (cmd == "--chollos-talla" or any(a in sys.argv for a in ["--talla", "-t", "--size"]))
            for arg in sys.argv[2:]:
                if arg in ["--talla", "-t", "--size"]:
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
            print(format_pure_deals_message(max_price=max_p, min_discount_pct=min_pct, solo_talla_compatible=solo_talla))
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
            print(format_stores_recommendation_message())
        elif cmd in ["--scan", "scan"]:
            run_pipeline(send_alerts=True, verbose=True)
        elif cmd in ["--test-telegram", "test-telegram"]:
            test_telegram_connection()
        elif cmd in ["--validate", "validate"]:
            from gravel_bot.validator import run_full_catalog_validation
            run_full_catalog_validation(auto_repair=True, verbose=True)
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
            dur = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
            run_bot_polling(duration_seconds=dur)
        elif cmd in ["--daemon", "daemon"]:
            from gravel_bot.cli import cmd_daemon
            cmd_daemon(None)
        elif cmd == "--init":
            print(f"Base de datos {DB_PATH} inicializada con éxito.")
        else:
            listar_ranking()
    else:
        listar_ranking()
        buscar_gangas()
