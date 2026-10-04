"""
gravel_bot.cli - Interfaz de Línea de Comandos para el Bot de Gravel
"""

import sys
import time
import argparse
from gravel_bot.config import SCAN_INTERVAL_SECONDS
from gravel_bot.db import init_db, get_all_bikes, get_deals, get_or_create_store, upsert_bike, record_price
from gravel_bot.evaluator import detect_bike_specs, calcular_rubrica
from gravel_bot.notifier import test_telegram_connection
from gravel_bot.pipeline import run_pipeline

def cmd_list(args):
    init_db()
    tier_filter = args.tier if hasattr(args, "tier") and args.tier else None
    bikes = get_all_bikes(tier_filter)

    print("\n" + "="*110)
    print(f"RANKING DE BICICLETAS GRAVEL (Madrid 50/50 - 1,69m - Presupuesto Flexible)")
    if tier_filter:
        print(f"Filtro aplicado: {tier_filter}")
    print("="*110)
    header = f"{'ID':<4} {'Marca y Modelo':<32} {'Tier':<8} {'Nota':<5} {'Precio':<8} {'PVP':<8} {'Talla 1,69m':<16} {'Tienda'}"
    print(header)
    print("-" * 110)

    for b in bikes:
        nombre = f"{b['marca']} {b['modelo']}"[:31]
        t_nombre = (b['tienda_nombre'] or 'Online')[:24]
        pvp_str = f"{int(b['precio_pvp'])} €" if b['precio_pvp'] else "-"
        oferta_str = f"{int(b['precio_oferta'])} €"
        print(f"{b['id']:<4} {nombre:<32} {b['tier']:<8} {b['nota']:<5} {oferta_str:<8} {pvp_str:<8} {b['talla_recomendada_169']:<16} {t_nombre}")
    print("="*110 + "\n")

def cmd_deals(args):
    init_db()
    deals = get_deals(min_discount_pct=args.min_discount if hasattr(args, "min_discount") else 15.0)

    print("\n" + "="*105)
    print("🎯 OPORTUNIDADES Y GANGAS DETECTADAS (Mayor descuento sobre PVP original)")
    print("="*105)
    header = f"{'ID':<4} {'Marca y Modelo':<32} {'Tier':<8} {'Oferta':<8} {'PVP':<8} {'Descuento':<10} {'Ahorro':<10} {'Tienda'}"
    print(header)
    print("-" * 105)

    for d in deals:
        nombre = f"{d['marca']} {d['modelo']}"[:31]
        t_nombre = (d['tienda_nombre'] or 'Online')[:22]
        desc_str = f"-{d['descuento_pct']:.1f}%"
        ahorro_str = f"-{int(d['ahorro_eur'])} €"
        print(f"{d['id']:<4} {nombre:<32} {d['tier']:<8} {int(d['precio_oferta']):<4} €   {int(d['precio_pvp']):<4} €   {desc_str:<10} {ahorro_str:<10} {t_nombre}")
    print("="*105 + "\n")

def cmd_scan(args):
    send_alerts = not args.no_alert if hasattr(args, "no_alert") else True
    run_pipeline(send_alerts=send_alerts, verbose=True)

def cmd_test_telegram(args):
    print("📡 Probando conexión con Telegram Bot...")
    success = test_telegram_connection()
    if success:
        print("✅ ¡Test completado con éxito! El bot tiene acceso y permisos.")
    else:
        print("⚠️ El test de Telegram no se completó. Revisa las variables de entorno.")

def cmd_daemon(args):
    interval = args.interval if hasattr(args, "interval") and args.interval else SCAN_INTERVAL_SECONDS
    print(f"🤖 [DAEMON] Iniciando monitor en segundo plano. Intervalo: {interval} segundos.")
    print("Presiona Ctrl+C para detener.")
    try:
        while True:
            print(f"\n⏰ [{time.strftime('%Y-%m-%d %H:%M:%S')}] Ejecutando ronda de escaneo...")
            run_pipeline(send_alerts=True, verbose=True)
            print(f"💤 Esperando {interval} segundos hasta el próximo escaneo...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 Monitor en segundo plano detenido por el usuario.")

def main():
    parser = argparse.ArgumentParser(description="Gravel Bot - Rastreador y Notificador de Chollos")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # scan
    parser_scan = subparsers.add_parser("scan", help="Ejecutar rastreo en tiendas web y notificar gangas")
    parser_scan.add_argument("--no-alert", action="store_true", help="No enviar alertas a Telegram")

    # list
    parser_list = subparsers.add_parser("list", help="Listar ranking de bicicletas en la base de datos")
    parser_list.add_argument("tier", nargs="?", default=None, help="Filtrar por Tier (ej: 'Tier S+')")

    # deals
    parser_deals = subparsers.add_parser("deals", help="Mostrar mayores descuentos y oportunidades")
    parser_deals.add_argument("--min-discount", type=float, default=15.0, help="Descuento mínimo en % (default 15)")

    # test-telegram
    subparsers.add_parser("test-telegram", help="Comprobar credenciales de Telegram Bot")

    # daemon
    parser_daemon = subparsers.add_parser("daemon", help="Ejecutar escaneo continuo en bucle")
    parser_daemon.add_argument("--interval", type=int, default=SCAN_INTERVAL_SECONDS, help="Segundos entre escaneos")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "deals":
        cmd_deals(args)
    elif args.command == "test-telegram":
        cmd_test_telegram(args)
    elif args.command == "daemon":
        cmd_daemon(args)
    else:
        # Default: mostrar listado
        cmd_list(args)

if __name__ == "__main__":
    main()
