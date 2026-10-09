"""
gravel_bot.web_server - Servidor Web Embebido Multi-hilo y API REST para Gravel Tracker
Sirve la SPA interactiva y expone endpoints JSON sin requerir librerías externas (solo Python stdlib).
"""

import os
import json
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from gravel_bot.budget_optimizer import (
    optimize_for_budget, clean_candidate_from_row, CleanCandidateBike
)
from gravel_bot.db import get_candidate_bikes_for_budget, get_connection

BASE_WEB_DIR = Path(__file__).resolve().parent / "web"


def get_sanitized_catalog_dict() -> List[Dict[str, Any]]:
    """Devuelve el catálogo completo sanitizado (sin cuadros, ebikes ni tiendas cerradas)."""
    rows = get_candidate_bikes_for_budget(max_price=None)
    bikes = []
    for r in rows:
        cand = clean_candidate_from_row(r, rider_height_cm=169, target_size=None)
        if cand:
            bikes.append(cand.__dict__)
    return bikes


def get_catalog_stats_dict() -> Dict[str, Any]:
    """Calcula estadísticas generales del catálogo de gravels activas con métricas de auditoría."""
    bikes = get_sanitized_catalog_dict()
    prices = [b["price"] for b in bikes if b["price"] > 0]
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT audit_status, COUNT(*) FROM bicicletas GROUP BY audit_status")
    audit_summary = {r[0] or "pendiente": r[1] for r in c.fetchall()}
    conn.close()
    return {
        "status": "success",
        "total_active_gravel": len(bikes),
        "min_price": min(prices) if prices else 0.0,
        "max_price": max(prices) if prices else 0.0,
        "avg_price": round(sum(prices) / len(prices), 1) if prices else 0.0,
        "audit_summary": audit_summary
    }


def calculate_1v1_comparison_diff(bike_a_id: int, bike_b_id: int) -> Optional[Dict[str, Any]]:
    """Calcula un enfrentamiento 1v1 resaltando las ventajas comparativas de cada modelo."""
    bikes = {b["id"]: b for b in get_sanitized_catalog_dict()}
    if bike_a_id not in bikes or bike_b_id not in bikes:
        return None

    a = bikes[bike_a_id]
    b = bikes[bike_b_id]

    adv_a = []
    adv_b = []

    # Frenos
    if a["has_hydraulic_brakes"] and not b["has_hydraulic_brakes"]:
        adv_a.append("Frenos hidráulicos frente a mecánicos")
    elif b["has_hydraulic_brakes"] and not a["has_hydraulic_brakes"]:
        adv_b.append("Frenos hidráulicos frente a mecánicos")

    # Horquilla
    if a["has_carbon_fork"] and not b["has_carbon_fork"]:
        adv_a.append("Horquilla de carbono para mejor absorción")
    elif b["has_carbon_fork"] and not a["has_carbon_fork"]:
        adv_b.append("Horquilla de carbono para mejor absorción")

    # Precio y descuento
    if a["price"] < b["price"]:
        adv_a.append(f"Más económica ({b['price'] - a['price']:.0f} € más barata)")
    elif b["price"] < a["price"]:
        adv_b.append(f"Más económica ({a['price'] - b['price']:.0f} € más barata)")

    if a["discount_pct"] > b["discount_pct"]:
        adv_a.append(f"Mayor descuento ({a['discount_pct']:.0f}% vs {b['discount_pct']:.0f}%)")
    elif b["discount_pct"] > a["discount_pct"]:
        adv_b.append(f"Mayor descuento ({b['discount_pct']:.0f}% vs {a['discount_pct']:.0f}%)")

    # Puntuación global
    if a["rubric_score"] > b["rubric_score"]:
        adv_a.append(f"Mejor nota global ({a['rubric_nota']:.1f}/10 vs {b['rubric_nota']:.1f}/10)")
    elif b["rubric_score"] > a["rubric_score"]:
        adv_b.append(f"Mejor nota global ({b['rubric_nota']:.1f}/10 vs {a['rubric_nota']:.1f}/10)")

    return {
        "bike_a": a,
        "bike_b": b,
        "advantages_a": adv_a,
        "advantages_b": adv_b,
        "price_difference": round(a["price"] - b["price"], 2)
    }


class GravelWebRequestHandler(SimpleHTTPRequestHandler):
    """Manejador HTTP para assets estáticos y endpoints de la API REST."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_WEB_DIR), **kwargs)

    def log_message(self, format, *args):
        # Desactivar spam de logs durante tests, registrar si es modo servidor
        pass

    def send_json_response(self, data: Any, status_code: int = 200):
        """Envía una respuesta JSON estructurada con cabeceras CORS."""
        encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API: Listado de bicicletas
        if path == "/api/bikes":
            bikes = get_sanitized_catalog_dict()
            self.send_json_response({
                "status": "success",
                "count": len(bikes),
                "bikes": bikes
            })
            return

        # 2. API: Recomendación para presupuesto
        if path == "/api/recommend":
            try:
                budget = float(query.get("budget", [1000.0])[0])
            except (ValueError, IndexError):
                budget = 1000.0

            height = int(query.get("height", [169])[0]) if "height" in query else 169
            size = query.get("size", [None])[0]
            channel = query.get("channel", ["all"])[0]
            stretch = query.get("stretch", ["true"])[0].lower() in ["true", "1", "yes"]

            podio = optimize_for_budget(
                budget=budget,
                height_cm=height,
                size=size,
                channel=channel,
                include_stretch=stretch
            )

            data = {
                "status": podio.status,
                "budget": podio.query.budget_ceiling,
                "rider": {
                    "height_cm": podio.query.rider_height_cm,
                    "target_size": podio.query.target_size
                },
                "total_candidates_scanned": podio.total_candidates_scanned,
                "valid_candidates_count": podio.valid_candidates_count,
                "best_value": podio.best_value.__dict__ if podio.best_value else None,
                "top_bargain": podio.top_bargain.__dict__ if podio.top_bargain else None,
                "smart_stretch": podio.smart_stretch.__dict__ if podio.smart_stretch else None,
                "stretch_reason": podio.stretch_reason,
                "budget_saver": podio.budget_saver.__dict__ if podio.budget_saver else None
            }
            self.send_json_response(data)
            return

        # 3. API: Estadísticas
        if path == "/api/stats":
            self.send_json_response(get_catalog_stats_dict())
            return

        # 4. API: Comparación 1v1
        if path == "/api/compare":
            try:
                b1 = int(query.get("b1", [0])[0])
                b2 = int(query.get("b2", [0])[0])
                diff = calculate_1v1_comparison_diff(b1, b2)
                if diff:
                    self.send_json_response({"status": "success", "comparison": diff})
                else:
                    self.send_json_response({"status": "error", "message": "Bicicletas no encontradas"}, 404)
            except Exception as e:
                self.send_json_response({"status": "error", "message": str(e)}, 400)
            return

        # 5. API: Ficha de inspección y desglose C1..C6
        if path in ["/api/card", "/api/itemized"]:
            from gravel_bot.evaluator import get_itemized_score_card
            from gravel_bot.bike_inspector import get_detailed_bike_info
            b_id = query.get("id", [None])[0]
            if b_id:
                info = get_detailed_bike_info(b_id)
                if info:
                    card = get_itemized_score_card(info)
                    self.send_json_response({"status": "success", "card": card})
                    return
            self.send_json_response({"status": "error", "message": "Bicicleta no encontrada"}, 404)
            return

        # 5. Archivos estáticos de frontend
        if path in ["/", "/index.html"]:
            self.path = "/index.html"
        return super().do_GET()


def create_web_server(port: int = 8080, host: str = "127.0.0.1") -> Tuple[ThreadingHTTPServer, int]:
    """Crea una instancia de ThreadingHTTPServer con fallback automático de puerto."""
    cur_port = port
    while cur_port < port + 20:
        try:
            server = ThreadingHTTPServer((host, cur_port), GravelWebRequestHandler)
            return server, cur_port
        except OSError:
            cur_port += 1
    raise RuntimeError(f"No se pudo enlazar ningún puerto entre {port} y {cur_port}")


def run_web_server(port: int = 8080, host: str = "127.0.0.1"):
    """Inicia el bucle de servicio web para uso interactivo."""
    server, active_port = create_web_server(port=port, host=host)
    print("\n" + "=" * 80)
    print(f"🚀 [GRAVEL TRACKER WEB] Servidor interactivo iniciado con éxito")
    print(f"🔗 Abre tu navegador en: http://{host}:{active_port}")
    print(f"💡 Pulsa Ctrl+C para detener el servidor.")
    print("=" * 80 + "\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor web detenido.")
    finally:
        server.server_close()
