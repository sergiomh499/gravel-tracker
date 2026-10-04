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
        elif cmd in ["--pure-deals", "pure-deals", "--chollos"]:
            from gravel_bot.deal_detector import format_pure_deals_message
            print(format_pure_deals_message())
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
        elif cmd in ["--add", "add"]:
            agregar_modelo_cli()
        elif cmd in ["--bot", "bot"]:
            from gravel_bot.bot_service import run_bot_polling
            run_bot_polling()
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
