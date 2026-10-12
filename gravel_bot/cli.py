"""
gravel_bot.cli - Interfaz de Línea de Comandos para el Bot de Gravel
"""

import sys
import time
import argparse
from typing import Optional, List
from gravel_bot.config import SCAN_INTERVAL_SECONDS
from gravel_bot.db import init_db, get_all_bikes, get_deals, get_or_create_store, upsert_bike, record_price
from gravel_bot.evaluator import detect_bike_specs, calcular_rubrica
from gravel_bot.notifier import test_telegram_connection
from gravel_bot.pipeline import run_pipeline

def cmd_list(args):
    init_db()
    tier_filter = args.tier if hasattr(args, "tier") and args.tier else None
    bikes = get_all_bikes(tier_filter)

    from gravel_bot.config import RIDER_PROFILE
    zona = RIDER_PROFILE.get("zona", "Tu Zona")
    est = RIDER_PROFILE.get("estatura_m", 1.69)
    print("\n" + "="*110)
    print(f"RANKING DE BICICLETAS GRAVEL ({zona} 50/50 - {est}m - Presupuesto Flexible)")
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

def cmd_budget(args):
    init_db()
    from gravel_bot.budget_optimizer import optimize_for_budget, format_budget_recommendation_card
    from gravel_bot.config import RIDER_PROFILE

    budget_val = getattr(args, "presupuesto", 1000.0) or 1000.0
    height_val = getattr(args, "altura", None) or RIDER_PROFILE.get("estatura_cm", 169)
    size_val = getattr(args, "talla", None)
    channel_val = "local_madrid" if getattr(args, "local", False) else (getattr(args, "canal", "all") or "all")
    json_mode = getattr(args, "json", False)

    podio = optimize_for_budget(
        budget=budget_val,
        height_cm=height_val,
        size=size_val,
        channel=channel_val,
        include_stretch=not getattr(args, "no_stretch", False)
    )
    print(format_budget_recommendation_card(podio, format="json" if json_mode else "text"))

def cmd_web(args):
    init_db()
    from gravel_bot.web_server import run_web_server
    port = getattr(args, "port", 8080) or 8080
    host = getattr(args, "host", "127.0.0.1") or "127.0.0.1"
    run_web_server(port=port, host=host)

def cmd_audit(args):
    init_db()
    from gravel_bot.catalog_auditor import run_catalog_audit
    limit_val = None if getattr(args, "all", False) else getattr(args, "limit", 20)
    store_val = getattr(args, "tienda", None)
    force_val = getattr(args, "force", False)

    print("\n" + "="*80)
    print("🔍 INICIANDO AUDITORÍA VIVA DEL CATÁLOGO (Stock & Enlaces)")
    print("="*80)
    if store_val:
        print(f"Tienda filtrada: {store_val}")
    if limit_val:
        print(f"Límite de comprobaciones: {limit_val}")
    print(f"Modo forzado (ignorar 24h previas): {'Sí' if force_val else 'No'}\n")

    def on_progress(cur, tot, res):
        tag = "✅" if res.audit_status == "verificado" else ("⚠️" if res.audit_status == "sin_stock" else "❌")
        price_str = f"{res.live_price:.0f}€" if res.live_price else "-"
        print(f"[{cur}/{tot}] {tag} ID {res.bike_id:<3} | {res.audit_status:<12} | {price_str:<6} | {res.url[:45]}")

    report = run_catalog_audit(limit=limit_val, store_filter=store_val, force=force_val, progress_callback=on_progress)
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

def cmd_rescore(args):
    init_db()
    from gravel_bot.evaluator import run_catalog_rescore
    dry_run = getattr(args, "dry_run", False)
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

def cmd_ficha(args):
    init_db()
    from gravel_bot.bike_inspector import format_detailed_bike_card
    modelo = getattr(args, "modelo", "Jakar 30") or "Jakar 30"
    print(format_detailed_bike_card(modelo))

def cmd_vs(args):
    init_db()
    from gravel_bot.bike_inspector import format_bike_comparison_message
    print(format_bike_comparison_message(args.b1, args.b2))

def cmd_gear(args):
    from gravel_bot.gear_calculator import format_gear_simulation_message
    sub = getattr(args, "tipo", "2x") or "2x"
    print(format_gear_simulation_message(sub))

def cmd_validate(args):
    """Valida e intenta auto-reparar la integridad del catálogo completo."""
    init_db()
    from gravel_bot.validator import run_full_catalog_validation
    limit = getattr(args, "limit", None)
    run_full_catalog_validation(auto_repair=True, limit=limit, verbose=True)


def cmd_sync_doc(args):
    """Sincroniza directorio_bicicletas.md y catalog_snapshot.json desde la BD."""
    from gravel_bot.pipeline import sync_directorio_markdown, export_catalog_snapshot
    sync_directorio_markdown()
    export_catalog_snapshot()


def cmd_bot(args):
    """Ejecuta el bot de Telegram en modo polling (usado por el workflow cloud cada 30 min)."""
    from gravel_bot.bot_service import run_bot_polling
    duration = getattr(args, "duration", None)
    run_bot_polling(duration_seconds=duration)


def cmd_cloud_sync(args):
    """Sincroniza los secretos de .env en GitHub Actions Secrets mediante gh CLI y verifica el worker."""
    import subprocess
    from gravel_bot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

    print("\n" + "="*80)
    print("☁️ SINCRONIZACIÓN DE SECRETOS Y CONFIGURACIÓN CLOUD (GitHub Actions)")
    print("="*80)

    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID

    if not token or not chat_id:
        print("❌ Error: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados en .env o entorno local.")
        return

    masked_token = token[:8] + "..." + token[-4:] if len(token) > 12 else "***"
    print(" * Leyendo credenciales locales:")
    print(f"   - TELEGRAM_BOT_TOKEN: {masked_token}")
    print(f"   - TELEGRAM_CHAT_ID:   {chat_id}")

    repo_name = "sergiomh499/gravel-tracker"
    print(f"\n * Sincronizando secretos en GitHub Secrets ({repo_name})...")

    cmd1 = ["env", "-u", "GITHUB_TOKEN", "gh", "secret", "set", "TELEGRAM_BOT_TOKEN", "--repo", repo_name, "--body", token]
    res1 = subprocess.run(cmd1, capture_output=True, text=True)
    if res1.returncode == 0:
        print("   ✅ Secret TELEGRAM_BOT_TOKEN sincronizado en GitHub.")
    else:
        print(f"   ❌ Error sincronizando TELEGRAM_BOT_TOKEN: {res1.stderr.strip()}")

    cmd2 = ["env", "-u", "GITHUB_TOKEN", "gh", "secret", "set", "TELEGRAM_CHAT_ID", "--repo", repo_name, "--body", str(chat_id)]
    res2 = subprocess.run(cmd2, capture_output=True, text=True)
    if res2.returncode == 0:
        print("   ✅ Secret TELEGRAM_CHAT_ID sincronizado en GitHub.")
    else:
        print(f"   ❌ Error sincronizando TELEGRAM_CHAT_ID: {res2.stderr.strip()}")

    if getattr(args, "trigger", False):
        print("\n * Disparando ejecución de prueba en GitHub Actions Cloud...")
        cmd_run = ["env", "-u", "GITHUB_TOKEN", "gh", "workflow", "run", "gravel_cloud_worker.yml", "--repo", repo_name]
        res_run = subprocess.run(cmd_run, capture_output=True, text=True)
        if res_run.returncode == 0:
            print("   🚀 Workflow disparado en GitHub Actions. Ejecutándose en la nube 24/7.")
        else:
            print(f"   ⚠️ Aviso al disparar: {res_run.stderr.strip()}")

    print("\n✅ Configuración cloud completada: el servidor gratuito de GitHub se encargará")
    print("   de rastrear y enviar alertas 24/7 sin que este ordenador deba estar encendido.")
    print("="*80 + "\n")

def cmd_scan(args):
    send_alerts = not args.no_alert if hasattr(args, "no_alert") else True
    deep_scan = getattr(args, "deep", False)
    run_pipeline(send_alerts=send_alerts, verbose=True, deep_scan=deep_scan)
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
def main(args_list: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Gravel Bot - Rastreador y Notificador de Chollos")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # scan
    parser_scan = subparsers.add_parser("scan", help="Ejecutar rastreo en tiendas web y notificar gangas")
    parser_scan.add_argument("--no-alert", action="store_true", help="No enviar alertas a Telegram")
    parser_scan.add_argument("--deep", action="store_true", help="Escaneo profundo con mayor paginación en portales compatibles (Wallapop, etc.)")
    # list
    parser_list = subparsers.add_parser("list", help="Listar ranking de bicicletas en la base de datos")
    parser_list.add_argument("tier", nargs="?", default=None, help="Filtrar por Tier (ej: 'Tier S+')")

    # deals
    parser_deals = subparsers.add_parser("deals", help="Mostrar mayores descuentos y oportunidades")
    parser_deals.add_argument("--min-discount", type=float, default=15.0, help="Descuento mínimo en %% (default 15)")
    # test-telegram
    subparsers.add_parser("test-telegram", help="Comprobar credenciales de Telegram Bot")

    # daemon
    parser_daemon = subparsers.add_parser("daemon", help="Ejecutar escaneo continuo en bucle")
    parser_daemon.add_argument("--interval", type=int, default=SCAN_INTERVAL_SECONDS, help="Segundos entre escaneos")

    # presupuesto / budget
    parser_budget = subparsers.add_parser("presupuesto", aliases=["budget", "recomendar"], help="Recomendar la mejor bicicleta para tu presupuesto (Podio Ejecutivo)")
    parser_budget.add_argument("presupuesto", type=float, nargs="?", default=1000.0, help="Presupuesto máximo en € (default 1000)")
    parser_budget.add_argument("--altura", "-a", type=int, default=None, help="Estatura en cm (default 169)")
    parser_budget.add_argument("--talla", "-t", type=str, default=None, help="Talla nominal (ej: S, M, 52)")
    parser_budget.add_argument("--local", "-l", action="store_true", help="Filtrar solo tiendas físicas locales")
    parser_budget.add_argument("--canal", "-c", type=str, default="all", help="Canal de compra: all, tienda_fisica, ocasion, online")
    parser_budget.add_argument("--no-stretch", action="store_true", help="No calcular alternativa Smart Stretch")
    parser_budget.add_argument("--json", action="store_true", help="Salida en formato JSON estructurado")

    # web / dashboard
    parser_web = subparsers.add_parser("web", aliases=["dashboard", "ui"], help="Iniciar el servidor web interactivo local")
    parser_web.add_argument("--port", "-p", type=int, default=8080, help="Puerto del servidor (default 8080)")
    parser_web.add_argument("--host", type=str, default="127.0.0.1", help="Host del servidor (default 127.0.0.1)")


    # audit
    parser_audit = subparsers.add_parser("audit", help="Auditar enlaces en vivo y disponibilidad de stock")
    parser_audit.add_argument("--limit", "-l", type=int, default=20, help="Límite de comprobaciones (default 20)")
    parser_audit.add_argument("--all", action="store_true", help="Auditar todos los enlaces del catálogo")
    parser_audit.add_argument("--tienda", "-t", "--store", type=str, default=None, help="Filtrar por tienda específica")
    parser_audit.add_argument("--force", "-f", action="store_true", help="Forzar auditoría ignorando últimas 24h")

    # re-score
    parser_rescore = subparsers.add_parser("re-score", aliases=["rescore"], help="Recalcular rúbrica calibrada C1..C6 con factor garantía")
    parser_rescore.add_argument("--dry-run", action="store_true", help="Simular sin escribir en la base de datos")

    # ficha / info / inspect
    parser_ficha = subparsers.add_parser("ficha", aliases=["info", "detalle"], help="Mostrar ficha técnica detallada")
    parser_ficha.add_argument("modelo", type=str, nargs="?", default="Jakar 30", help="Modelo de bicicleta")

    # vs / compare
    parser_vs = subparsers.add_parser("vs", aliases=["compare"], help="Comparar dos bicicletas 1v1")
    parser_vs.add_argument("b1", type=str, help="Primera bicicleta")
    parser_vs.add_argument("b2", type=str, help="Segunda bicicleta")

    # desarrollo / cadencia
    parser_gear = subparsers.add_parser("desarrollo", aliases=["cadencia"], help="Simular cinemática de desarrollo")
    parser_gear.add_argument("tipo", type=str, nargs="?", default="2x", help="Tipo de transmisión: 1x o 2x")

    # cloud-sync
    parser_cloud = subparsers.add_parser("cloud-sync", aliases=["sync-cloud", "cloud"], help="Sincronizar secretos en GitHub Actions para ejecución 24/7 en la nube")
    parser_cloud.add_argument("--trigger", "-t", action="store_true", help="Disparar ejecución de prueba inmediata en GitHub Cloud")

    # validate / sync-doc / bot
    parser_validate = subparsers.add_parser("validate", help="Validar y auto-reparar la integridad del catálogo")
    parser_validate.add_argument("--limit", "-l", type=int, default=None, help="Limitar número de bicicletas validadas")
    subparsers.add_parser("sync-doc", help="Regenerar directorio_bicicletas.md y catalog_snapshot.json")
    parser_bot = subparsers.add_parser("bot", help="Ejecutar el bot de Telegram en modo polling")
    parser_bot.add_argument("duration", type=int, nargs="?", default=None, help="Duración en segundos (ej. 1500 en GitHub Actions)")
    raw_args = list(sys.argv[1:] if args_list is None else args_list)
    if not raw_args:
        cmd_list(argparse.Namespace(tier=None))
        cmd_deals(argparse.Namespace(min_discount=15.0))
        return

    cmd_map = {
        "--scan": "scan",
        "--list": "list",
        "--deals": "deals",
        "--presupuesto": "presupuesto",
        "--budget": "budget",
        "--recomendar": "recomendar",
        "--web": "web",
        "--dashboard": "dashboard",
        "--ui": "ui",
        "--audit": "audit",
        "--re-score": "re-score",
        "--rescore": "rescore",
        "--ficha": "ficha",
        "--info": "info",
        "--detalle": "detalle",
        "--vs": "vs",
        "--compare": "compare",
        "--desarrollo": "desarrollo",
        "--cadencia": "cadencia",
        "--daemon": "daemon",
        "--test-telegram": "test-telegram",
        "--cloud-sync": "cloud-sync",
        "--sync-cloud": "cloud-sync",
        "--cloud": "cloud-sync",
        "--validate": "validate",
        "--sync-doc": "sync-doc",
        "--bot": "bot",
    }
    if raw_args and raw_args[0] in cmd_map:
        raw_args[0] = cmd_map[raw_args[0]]

    args = parser.parse_args(raw_args)

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
    elif args.command in ["presupuesto", "budget", "recomendar"]:
        cmd_budget(args)
    elif args.command in ["web", "dashboard", "ui"]:
        cmd_web(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command in ["re-score", "rescore"]:
        cmd_rescore(args)
    elif args.command in ["ficha", "info", "detalle"]:
        cmd_ficha(args)
    elif args.command in ["vs", "compare"]:
        cmd_vs(args)
    elif args.command in ["desarrollo", "cadencia"]:
        cmd_gear(args)
    elif args.command in ["cloud-sync", "sync-cloud", "cloud"]:
        cmd_cloud_sync(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "sync-doc":
        cmd_sync_doc(args)
    elif args.command == "bot":
        cmd_bot(args)
    else:
        cmd_list(args)
if __name__ == "__main__":
    main()
