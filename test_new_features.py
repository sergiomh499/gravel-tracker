import unittest
from gravel_bot.db import (
    init_db, get_or_create_user, update_user_profile, get_user_profile,
    add_size_alert, get_user_size_alerts, delete_size_alert
)
from gravel_bot.gear_calculator import (
    speed_kmh, development_meters, analyze_drivetrain, format_gear_simulation_message
)
from gravel_bot.bike_inspector import (
    format_bike_comparison_message, format_available_bikes_message
)
from gravel_bot.deal_detector import check_and_notify_size_alerts
from gravel_bot.bot_service import format_profile_message

from gravel_bot.budget_optimizer import (
    BudgetQuery, CleanCandidateBike, RecommendationPodio, calculate_vfm_index,
    optimize_for_budget, format_budget_recommendation_card,
    is_noise_candidate, is_size_compatible
)
from gravel_bot.db import get_candidate_bikes_for_budget
class TestNewFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_gear_calculator_math(self):
        """Verifica cálculos cinemáticos y de cadencia."""
        # 46T plato con 11T piñón a 90 rpm (cubierta 700x40c)
        spd = speed_kmh(46, 11, 90)
        self.assertGreater(spd, 45.0)
        self.assertLess(spd, 55.0)

        # Metros de avance
        m = development_meters(30, 36)
        self.assertGreater(m, 1.5)
        self.assertLess(m, 2.5)

        # Análisis de rango
        res = analyze_drivetrain([46, 30], [11, 36])
        self.assertGreater(res["gear_range_pct"], 450)
        self.assertIn("climbing_ability", res)

        msg = format_gear_simulation_message("2x")
        self.assertIn("SIMULADOR CINEMÁTICO", msg)

    def test_bike_comparator_1v1(self):
        """Verifica la comparación 1v1 entre dos bicicletas."""
        msg = format_bike_comparison_message("kalima", "jakar", estatura_cm=169)
        self.assertIn("COMPARATIVA 1v1", msg)
        self.assertIn("Conor", msg)
        self.assertIn("Megamo", msg)
        self.assertIn("DUELO TÉCNICO", msg)

    def test_size_restock_alerts(self):
        """Verifica el ciclo de vida de alertas de talla."""
        uid = get_or_create_user(888123, "test_alerts_user")
        aid = add_size_alert(uid, "kalima", "SM")
        self.assertIsInstance(aid, int)

        alerts = get_user_size_alerts(uid)
        self.assertTrue(any(a["id"] == aid for a in alerts))

        deleted = delete_size_alert(aid, uid)
        self.assertTrue(deleted)

    def test_configurable_location(self):
        """Verifica que la ubicación del usuario sea 100% configurable."""
        from gravel_bot.store_recommender import format_stores_recommendation_message
        from gravel_bot.deal_detector import format_pure_deals_message
        uid = get_or_create_user(777456, "madrid_user")
        update_user_profile(777456, zona="Valencia")
        prof = get_user_profile(777456)
        self.assertEqual(prof["zona"], "Valencia")

        msg = format_profile_message(777456, "madrid_user")
        self.assertIn("Valencia", msg)

        # Tiendas físicas adaptadas a la ubicación configurada
        stores_msg = format_stores_recommendation_message(zona="Valencia")
        self.assertIn("VALENCIA", stores_msg)
        self.assertIn("Decathlon Valencia", stores_msg)

        # Chollos filtrados por ubicación configurada
        deals_msg = format_pure_deals_message(zona_fisica="Valencia")
        self.assertIn("Valencia", deals_msg)
    def test_certified_secondhand_filter(self):
        """Verifica el filtrado de bicicletas de ocasión certificada."""
        msg = format_available_bikes_message(store_type="ocasion")
        self.assertIn("BICICLETAS DISPONIBLES EN STOCK", msg)

    def test_interactive_keyboards_and_button_processing(self):
        """Verifica que todos los botones y teclados interactivos funcionen sin error."""
        from gravel_bot.bot_service import (
            MAIN_KEYBOARD, COMPARE_PRESETS_KEYBOARD, PODIUM_INLINE_KEYBOARD,
            DEALS_INLINE_KEYBOARD, PROFILE_INLINE_KEYBOARD, get_bike_inline_keyboard,
            _process_message
        )

        # Verificar estructura de teclados
        self.assertGreaterEqual(len(MAIN_KEYBOARD["keyboard"]), 4)
        self.assertGreaterEqual(len(COMPARE_PRESETS_KEYBOARD["inline_keyboard"]), 3)
        self.assertGreaterEqual(len(PODIUM_INLINE_KEYBOARD["inline_keyboard"]), 2)
        self.assertGreaterEqual(len(DEALS_INLINE_KEYBOARD["inline_keyboard"]), 2)
        self.assertGreaterEqual(len(PROFILE_INLINE_KEYBOARD["inline_keyboard"]), 3)

        # Verificar generación de inline keyboard para bicicleta
        bike_sample = {
            "modelo": "Kalima GRX400",
            "url_oferta": "https://tienda.com/kalima",
            "transmision": "Shimano GRX 2x10",
            "talla_recomendada_169": "SM"
        }
        ikb = get_bike_inline_keyboard(bike_sample)
        self.assertIn("inline_keyboard", ikb)
        self.assertTrue(any("url" in btn for row in ikb["inline_keyboard"] for btn in row))

        # Simular toques de botón mediante _process_message aislando llamadas HTTP externas
        from unittest.mock import patch
        test_chat_id = 998877
        with patch("urllib.request.urlopen"):
            _process_message({"chat": {"id": test_chat_id, "username": "btn_tester"}, "text": "⚔️ Comparar Bicis"})
            _process_message({"chat": {"id": test_chat_id, "username": "btn_tester"}, "text": "📍 Tiendas Físicas"})
            _process_message({"chat": {"id": test_chat_id, "username": "btn_tester"}, "text": "👤 Mi Perfil"})
            _process_message({"chat": {"id": test_chat_id, "username": "btn_tester"}, "text": "kalima"})

    def test_haversine_geocoding(self):
        """Verifica la resolución de coordenadas GPS a la ciudad más cercana."""
        from gravel_bot.geocoder import resolve_closest_city, haversine_distance_km
        # Coordenadas de Valencia (Plaza del Ayuntamiento)
        city_vlc, dist_vlc = resolve_closest_city(39.4697, -0.3774)
        self.assertEqual(city_vlc, "Valencia")
        self.assertLess(dist_vlc, 5.0)

        # Coordenadas de Barcelona (Plaça Catalunya)
        city_bcn, dist_bcn = resolve_closest_city(41.3870, 2.1700)
        self.assertEqual(city_bcn, "Barcelona")
        self.assertLess(dist_bcn, 5.0)

        # Distancia entre Madrid y Valencia (~300 km)
        dist_mad_vlc = haversine_distance_km(40.4168, -3.7038, 39.4699, -0.3763)
        self.assertGreater(dist_mad_vlc, 250.0)
        self.assertLess(dist_mad_vlc, 350.0)

    def test_wizard_interactive_flow(self):
        """Verifica el flujo del asistente paso a paso (/wizard)."""
        from unittest.mock import patch
        from gravel_bot.bot_service import _process_message
        from gravel_bot.db import get_user_profile

        chat_id = 881122
        with patch("urllib.request.urlopen"):
            # Paso 1: Iniciar wizard
            _process_message({"chat": {"id": chat_id, "username": "wiz_tester"}, "text": "/wizard"})
            # Paso 2: Elegir estatura 175 cm
            _process_message({"chat": {"id": chat_id, "username": "wiz_tester"}, "text": "/wizard:step2:175"})
            # Paso 3: Elegir presupuesto 1200 €
            _process_message({"chat": {"id": chat_id, "username": "wiz_tester"}, "text": "/wizard:step3:175:1200"})
            # Paso 4: Elegir transmisión 1x
            _process_message({"chat": {"id": chat_id, "username": "wiz_tester"}, "text": "/wizard:step4:175:1200:1x"})
            # Finalizar: Elegir zona Valencia
            _process_message({"chat": {"id": chat_id, "username": "wiz_tester"}, "text": "/wizard:finish:175:1200:1x:Valencia"})

        prof = get_user_profile(chat_id)
        self.assertIsNotNone(prof)
        self.assertEqual(prof["estatura_cm"], 175)
        self.assertEqual(prof["presupuesto_max"], 1200.0)
        self.assertEqual(prof["preferencia_transmision"], "1x")
        self.assertEqual(prof["zona"], "Valencia")

    def test_paged_catalog_navigation(self):
        """Verifica la paginación interactiva del catálogo de bicicletas."""
        from gravel_bot.bike_inspector import get_paged_available_bikes_payload

        # Página 1
        msg1, kb1 = get_paged_available_bikes_payload(page=1, page_size=5)
        self.assertIn("BICICLETAS DISPONIBLES EN STOCK", msg1)
        self.assertIn("Página 1", msg1)
        self.assertIsNotNone(kb1)
        self.assertIn("inline_keyboard", kb1)

        # Comprobar que existen botones de navegación
        all_callbacks = [btn.get("callback_data") for row in kb1["inline_keyboard"] for btn in row if "callback_data" in btn]
        self.assertTrue(any(cb and cb.startswith("/page:") for cb in all_callbacks))

    def test_gps_location_message_processing(self):
        """Verifica la actualización de ubicación al recibir un mensaje GPS de Telegram."""
        from unittest.mock import patch
        from gravel_bot.bot_service import _process_message
        from gravel_bot.db import get_user_profile

        chat_id = 334455
        with patch("urllib.request.urlopen"):
            # Enviar mensaje con location a Valencia
            _process_message({
                "chat": {"id": chat_id, "username": "gps_tester"},
                "location": {"latitude": 39.4699, "longitude": -0.3763}
            })

        prof = get_user_profile(chat_id)
        self.assertIsNotNone(prof)
        self.assertEqual(prof["zona"], "Valencia")

    def test_defunct_tuvalum_scraper_removed(self):
        """Verifica que el scraper extinto de Tuvalum fue removido de ACTIVE_SCRAPERS (T077-T080)."""
        import os
        from gravel_bot.scrapers import get_all_scrapers
        self.assertFalse(os.path.exists("gravel_bot/scrapers/tuvalum.py"))
        all_active = [s.store_slug for s in get_all_scrapers()]
        self.assertNotIn("tuvalum", all_active)
    def test_persistent_wizard_draft(self):
        """Verifica la persistencia de borradores de wizard en SQLite."""
        from gravel_bot.db import save_wizard_draft, get_wizard_draft, clear_wizard_draft

        test_uid = 771122
        clear_wizard_draft(test_uid)
        self.assertIsNone(get_wizard_draft(test_uid))

        save_wizard_draft(test_uid, "step2", {"estatura": 172})
        d = get_wizard_draft(test_uid)
        self.assertIsNotNone(d)
        self.assertEqual(d["estatura"], 172)
        self.assertEqual(d["_step"], "step2")

        save_wizard_draft(test_uid, "step3", {"estatura": 172, "presupuesto": 1100})
        d2 = get_wizard_draft(test_uid)
        self.assertEqual(d2["presupuesto"], 1100)
        self.assertEqual(d2["_step"], "step3")

        clear_wizard_draft(test_uid)
        self.assertIsNone(get_wizard_draft(test_uid))

    def test_entrepierna_biomechanics_and_command(self):
        """Verifica el cálculo de talla por entrepierna y su comando en Telegram."""
        from unittest.mock import patch
        from gravel_bot.biomechanics import calculate_frame_size_from_inseam
        from gravel_bot.bot_service import _process_message
        from gravel_bot.db import get_user_profile

        res = calculate_frame_size_from_inseam(79.0)
        self.assertIn("cuadro_cm", res)
        self.assertEqual(res["cuadro_cm"], 51.4)
        self.assertEqual(res["talla_recomendada"], "S")
        self.assertEqual(res["altura_sillin_cm"], 69.9)

        chat_id = 665544
        with patch("urllib.request.urlopen"):
            _process_message({"chat": {"id": chat_id, "username": "inseam_usr"}, "text": "/entrepierna 79"})

        prof = get_user_profile(chat_id)
        self.assertIsNotNone(prof)
        self.assertEqual(prof["entrepierna_cm"], 79.0)
        self.assertEqual(prof["talla_calculada"], "S")

    def test_frecuencia_notificaciones_command(self):
        """Verifica la actualización de frecuencia de alertas (/frecuencia)."""
        from unittest.mock import patch
        from gravel_bot.bot_service import _process_message
        from gravel_bot.db import get_user_profile

        chat_id = 554433
        with patch("urllib.request.urlopen"):
            _process_message({"chat": {"id": chat_id, "username": "frec_usr"}, "text": "/frecuencia diaria"})

        prof = get_user_profile(chat_id)
        self.assertIsNotNone(prof)
        self.assertEqual(prof["frecuencia_notificaciones"], "diaria")
        self.assertEqual(prof["alertas_activas"], 1)

        with patch("urllib.request.urlopen"):
            _process_message({"chat": {"id": chat_id, "username": "frec_usr"}, "text": "/frecuencia desactivada"})

        prof2 = get_user_profile(chat_id)
        self.assertEqual(prof2["frecuencia_notificaciones"], "desactivada")
        self.assertEqual(prof2["alertas_activas"], 0)

    def test_proxy_rotation_config(self):
        """Verifica la configuración y carga de proxies en ResilientSession."""
        import os
        from gravel_bot.anti_ban import ResilientSession
        os.environ["GRAVEL_PROXIES"] = "http://10.0.0.1:8080,http://10.0.0.2:8080"
        ResilientSession._proxies = []
        proxies = ResilientSession.get_configured_proxies()
        self.assertEqual(len(proxies), 2)
        self.assertIn("http://10.0.0.1:8080", proxies)
        opener = ResilientSession.get_opener()
        self.assertIsNotNone(opener)
        del os.environ["GRAVEL_PROXIES"]
        ResilientSession._proxies = []

    def test_escapa_scraper_registration(self):
        """Verifica que EscapaScraper esté registrado y disponible."""
        from gravel_bot.scrapers import get_all_scrapers
        from gravel_bot.scrapers.escapa import EscapaScraper
        all_s = get_all_scrapers()
        self.assertTrue(any(isinstance(s, EscapaScraper) for s in all_s))

    def test_deep_scan_flag_and_scraper(self):
        """Verifica la configuración de deep scan en WallapopMadridScraper y CLI."""
        from gravel_bot.scrapers.wallapop import WallapopMadridScraper
        scraper = WallapopMadridScraper()
        self.assertTrue(hasattr(scraper, "deep_pages"))
        self.assertEqual(scraper.max_pages, 2)
        self.assertEqual(scraper.deep_pages, 5)

    def test_price_drop_and_history_and_clearance(self):
        """Verifica la detección de bajadas de precio, mínimo histórico y penalización de paso de rueda."""
        from gravel_bot.db import check_price_drop, record_price_if_changed, get_connection
        from gravel_bot.notifier import format_price_drop_message
        from gravel_bot.deal_detector import format_bike_price_history_message
        from gravel_bot.evaluator import detect_bike_specs
        from gravel_bot.pipeline import export_catalog_snapshot

        # 1. Bajada de precio
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM bicicletas LIMIT 1")
        b_id = c.fetchone()["id"]
        conn.close()

        record_price_if_changed(b_id, 1, 1500.0, "S", 1, "https://test.com/bici", "Base")
        drop = check_price_drop(b_id, 1200.0)
        self.assertIsNotNone(drop)
        self.assertEqual(drop["drop_eur"], 300.0)
        self.assertEqual(drop["drop_pct"], 20.0)

        msg_drop = format_price_drop_message({"marca": "Test", "modelo": "Drop", "tier": "Tier S", "talla_recomendada_169": "S", "url_oferta": "https://test.com"}, drop)
        self.assertIn("BAJADA DE PRECIO", msg_drop)

        # 2. Historial con mínimo histórico
        hist_msg = format_bike_price_history_message("Kalima")
        self.assertIn("HISTORIAL DE PRECIOS", hist_msg)
        self.assertTrue("Mínimo histórico" in hist_msg or "MÍNIMO HISTÓRICO" in hist_msg)

        # 3. Penalización de paso de rueda estrecho / CX
        b_cx = detect_bike_specs("Bicicleta Gravel CX Race UCI 33mm", price=1100.0)
        self.assertFalse(b_cx["paso_rueda_apto"])
        self.assertLessEqual(b_cx["c3_cuadro"], 8.0)
        self.assertIn("Paso de rueda limitado", b_cx["notas_veredicto"])

        # 4. Snapshot texto
        import os
        snap_file = "test_catalog_snapshot.json"
        export_catalog_snapshot(json_path=snap_file)
        self.assertTrue(os.path.exists(snap_file))
        os.remove(snap_file)

class TestBudgetOptimizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_vfm_index_math(self):
        """Verifica el cálculo del índice Value-for-Money (VfM)."""
        self.assertEqual(calculate_vfm_index(90.0, 1000.0), 90.0)
        self.assertEqual(calculate_vfm_index(80.0, 800.0), 100.0)
        self.assertEqual(calculate_vfm_index(95.0, 1900.0), 50.0)
        self.assertEqual(calculate_vfm_index(80.0, 0.0), 0.0)

    def test_candidate_db_extraction(self):
        """Verifica la extracción de candidatos con límite presupuestario en SQLite."""
        candidates = get_candidate_bikes_for_budget(max_price=1100.0)
        self.assertIsInstance(candidates, list)
        self.assertGreater(len(candidates), 0)
        for row in candidates:
            self.assertLessEqual(row["precio_oferta"], 1100.0)
            self.assertGreater(row["precio_oferta"], 0.0)
            if row["tienda_nombre"]:
                self.assertNotIn("CERRADA", row["tienda_nombre"])
                self.assertNotIn("Liquidación", row["tienda_nombre"])

    def test_budget_podio_optimization(self):
        """Verifica la recomendación ejecutiva para un presupuesto dado (US1)."""
        podio = optimize_for_budget(budget=1000.0, height_cm=169)
        self.assertIsInstance(podio, RecommendationPodio)
        self.assertEqual(podio.status, "success")
        self.assertIsNotNone(podio.best_value)
        self.assertLessEqual(podio.best_value.price, 1000.0)
        self.assertGreater(podio.best_value.rubric_score, 0.0)

        # Test formateador de texto y JSON
        card_text = format_budget_recommendation_card(podio, format="text")
        self.assertIn("PODIO DE RECOMENDACIÓN PARA TU PRESUPUESTO", card_text)
        self.assertIn("1. MEJOR COMPRA ABSOLUTA", card_text)

        card_json = format_budget_recommendation_card(podio, format="json")
        import json
        parsed = json.loads(card_json)
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["budget"], 1000.0)

    def test_noise_and_size_exclusion(self):
        """Verifica la exclusión estricta de cuadros, ebikes, tiendas cerradas y tallas incompatibles (US2)."""
        self.assertTrue(is_noise_candidate("Cuadro Gravel Kross Esker", "Kross", "gravel", "Wallapop"))
        self.assertTrue(is_noise_candidate("Orbea Rise ebike M20", "Orbea", "ebike", "Mammoth"))
        self.assertTrue(is_noise_candidate("Megamo Jakar 30", "Megamo", "gravel", "Tuvalum (CERRADA - Liquidación)"))
        self.assertTrue(is_noise_candidate("Scott Road Speedster 10", "Scott", "carretera", "Sanferbike"))
        self.assertFalse(is_noise_candidate("Megamo Jakar 30 2026", "Megamo", "gravel", "Biciescapa Madrid"))

        # Sizing
        compat_s, _ = is_size_compatible("S (52 cm)", "S, M, L", 169)
        self.assertTrue(compat_s)
        incompat_s, _ = is_size_compatible("No compatible", "M, L", 169)
        self.assertFalse(incompat_s)

        # Test podio sanitizado: 0 cuadros, 0 ebikes, 0 tiendas cerradas
        podio = optimize_for_budget(budget=1500.0, height_cm=169)
        for bike in [podio.best_value, podio.top_bargain, podio.smart_stretch, podio.budget_saver]:
            if bike:
                self.assertNotIn("cuadro", bike.model.lower())
                self.assertNotIn("cuadro", bike.brand.lower())
                self.assertNotIn("ebike", bike.model.lower())
                self.assertNotIn("cerrada", bike.store_name.lower())
                self.assertNotIn("tuvalum", bike.store_name.lower())
                self.assertEqual(bike.discipline, "gravel")
                self.assertNotEqual(bike.size_compatibility, "incompatible")

    def test_smart_stretch_and_budget_saver(self):
        """Verifica la detección de Smart Stretch y alternativas de ahorro (US3)."""
        podio_900 = optimize_for_budget(budget=900.0, height_cm=169, include_stretch=True)
        self.assertIsNotNone(podio_900.best_value)
        self.assertLessEqual(podio_900.best_value.price, 900.0)

        if podio_900.smart_stretch:
            self.assertGreater(podio_900.smart_stretch.price, 900.0)
            self.assertLessEqual(podio_900.smart_stretch.price, 900.0 * 1.15 + 50.0)
            self.assertIsNotNone(podio_900.stretch_reason)

        podio_1300 = optimize_for_budget(budget=1300.0, height_cm=169)
        if podio_1300.budget_saver:
            self.assertLessEqual(podio_1300.budget_saver.price, 1300.0 * 0.85)

        msg = format_budget_recommendation_card(podio_1300, format="text")
        if podio_1300.smart_stretch:
            self.assertIn("SMART STRETCH", msg)
        if podio_1300.budget_saver:
            self.assertIn("OPCIÓN DE AHORRO INTELIGENTE", msg)

    def test_telegram_budget_commands(self):
        """Verifica la respuesta a /presupuesto y botones de preset en Telegram (US4)."""
        from unittest.mock import patch
        from gravel_bot.bot_service import _process_message

        chat_id = 771122
        with patch("gravel_bot.bot_service.send_reply") as mock_send:
            # 1. Bare /presupuesto
            _process_message({"chat": {"id": chat_id, "username": "budget_tester"}, "text": "/presupuesto"})
            self.assertTrue(mock_send.called)
            args, kwargs = mock_send.call_args
            self.assertIn("OPTIMIZADOR DE PRESUPUESTO", args[1])
            self.assertIn("inline_keyboard", kwargs.get("reply_markup", {}))

            # 2. Comando explícito con valor /presupuesto 1200
            _process_message({"chat": {"id": chat_id, "username": "budget_tester"}, "text": "/presupuesto 1200"})
            args, kwargs = mock_send.call_args
            self.assertIn("PODIO RECOMENDADO PARA TU PRESUPUESTO", args[1])
            self.assertIn("1. MEJOR COMPRA EN PRESUPUESTO", args[1])

            # 3. Mensaje numérico conversacional "1100€"
            _process_message({"chat": {"id": chat_id, "username": "budget_tester"}, "text": "1100€"})
            args, kwargs = mock_send.call_args
            self.assertIn("PODIO RECOMENDADO PARA TU PRESUPUESTO", args[1])

    def test_quickstart_end_to_end_smoke(self):
        """Verificación Smoke End-to-End según quickstart.md (T023)."""
        import json
        # Escenario 1: Búsqueda estándar 1.000 €
        p1 = optimize_for_budget(1000.0, height_cm=169)
        self.assertEqual(p1.status, "success")
        self.assertIsNotNone(p1.best_value)
        self.assertLessEqual(p1.best_value.price, 1000.0)
        self.assertTrue(p1.best_value.product_url.startswith("http"))

        # Escenario 2: 0 cuadros, 0 ebikes, 0 tiendas cerradas
        p2 = optimize_for_budget(1500.0, height_cm=169)
        for b in [p2.best_value, p2.top_bargain, p2.smart_stretch, p2.budget_saver]:
            if b:
                self.assertNotIn("cuadro", b.model.lower())
                self.assertNotIn("cuadro", b.brand.lower())
                self.assertNotIn("ebike", b.model.lower())
                self.assertNotIn("tuvalum", b.store_name.lower())
                self.assertNotIn("cerrada", b.store_name.lower())

        # Escenario 3: Smart stretch trigger
        p3 = optimize_for_budget(950.0, height_cm=169, include_stretch=True)
        self.assertLessEqual(p3.best_value.price, 950.0)
        if p3.smart_stretch:
            self.assertGreater(p3.smart_stretch.price, 950.0)
            self.assertLessEqual(p3.smart_stretch.price, 950.0 * 1.15 + 50.0)

        # Escenario 4: JSON Output
        json_out = format_budget_recommendation_card(p1, format="json")
        parsed = json.loads(json_out)
        self.assertEqual(parsed["status"], "success")
        self.assertIn("best_value", parsed)
        self.assertIn("top_bargain", parsed)

class TestWebServerAndDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        import threading
        from gravel_bot.web_server import create_web_server
        cls.server, cls.port = create_web_server(port=9099, host="127.0.0.1")
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_static_assets(self):
        """Verifica que el servidor sirve HTML, JS y CSS con MIME types correctos (T028, T033)."""
        import urllib.request
        req = urllib.request.urlopen(f"{self.base_url}/")
        self.assertEqual(req.status, 200)
        self.assertIn("text/html", req.headers.get("Content-Type", ""))
        body = req.read().decode("utf-8")
        self.assertIn("Gravel Tracker", body)
        self.assertIn("Podio Ejecutivo", body)

        req_js = urllib.request.urlopen(f"{self.base_url}/app.js")
        self.assertEqual(req_js.status, 200)

        req_css = urllib.request.urlopen(f"{self.base_url}/style.css")
        self.assertEqual(req_css.status, 200)
        self.assertIn("text/css", req_css.headers.get("Content-Type", ""))

    def test_api_bikes_endpoint(self):
        """Verifica el endpoint /api/bikes (T031, T032)."""
        import urllib.request, json
        req = urllib.request.urlopen(f"{self.base_url}/api/bikes")
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["count"], 0)
        self.assertIsInstance(data["bikes"], list)
        for b in data["bikes"][:5]:
            self.assertIn("brand", b)
            self.assertIn("price", b)
            self.assertNotIn("cuadro", b["model"].lower())

    def test_api_recommend_endpoint(self):
        """Verifica el endpoint /api/recommend con parámetros de presupuesto (T031)."""
        import urllib.request, json
        req = urllib.request.urlopen(f"{self.base_url}/api/recommend?budget=1000&height=169")
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode("utf-8"))
        self.assertIn(data["status"], ["success", "no_exact_match"])
        self.assertEqual(data["budget"], 1000.0)
        if data["best_value"]:
            self.assertLessEqual(data["best_value"]["price"], 1000.0)

    def test_api_stats_and_compare_endpoints(self):
        """Verifica los endpoints /api/stats y /api/compare (T037, T038)."""
        import urllib.request, json
        # Stats
        req_st = urllib.request.urlopen(f"{self.base_url}/api/stats")
        self.assertEqual(req_st.status, 200)
        st = json.loads(req_st.read().decode("utf-8"))
        self.assertEqual(st["status"], "success")
        self.assertGreater(st["total_active_gravel"], 0)

        # Compare
        req_b = urllib.request.urlopen(f"{self.base_url}/api/bikes")
        bikes = json.loads(req_b.read().decode("utf-8"))["bikes"]
        if len(bikes) >= 2:
            b1_id, b2_id = bikes[0]["id"], bikes[1]["id"]
            req_cmp = urllib.request.urlopen(f"{self.base_url}/api/compare?b1={b1_id}&b2={b2_id}")
            self.assertEqual(req_cmp.status, 200)
            cmp_data = json.loads(req_cmp.read().decode("utf-8"))
            self.assertEqual(cmp_data["status"], "success")
            self.assertIn("advantages_a", cmp_data["comparison"])
            self.assertIn("advantages_b", cmp_data["comparison"])

    def test_web_quickstart_smoke(self):
        """Smoke test de integración según quickstart.md (T045)."""
        import urllib.request, json
        # Healthcheck
        req = urllib.request.urlopen(f"{self.base_url}/api/stats")
        self.assertEqual(req.status, 200)
        # Recommendation query
        req_rec = urllib.request.urlopen(f"{self.base_url}/api/recommend?budget=1200")
        rec = json.loads(req_rec.read().decode("utf-8"))
        self.assertIn("status", rec)

class TestCatalogAuditAndRankingCalibration(unittest.TestCase):
    """Suite de pruebas para la característica 003: Auditoría de Catálogo y Rúbrica Calibrada."""

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_components_authority_mapping_and_fake_hydraulic_correction(self):
        """Verifica la corrección de falsos frenos hidráulicos y acotación de PVP (T050, T058, T059)."""
        from gravel_bot.components_authority import get_canonical_group_spec, sanitize_bike_specs

        # 1. Mapeo canónico
        spec_claris = get_canonical_group_spec("Shimano Claris R2000")
        self.assertIsNotNone(spec_claris)
        self.assertEqual(spec_claris.actuation, "mecanico")
        self.assertEqual(spec_claris.family, "shimano")

        spec_grx = get_canonical_group_spec("Shimano GRX RX400")
        self.assertIsNotNone(spec_grx)
        self.assertEqual(spec_grx.actuation, "hidraulico")

        # 2. Corrección de falso hidráulico
        fake_ad = {
            "id": 999,
            "marca": "Megamo",
            "modelo": "Jakar 30",
            "transmision": "Shimano Claris",
            "tipo_transmision": "2x8",
            "frenos": "Frenos de disco mecánicos",
            "tipo_frenos": "hidraulico",  # Falso hidráulico erróneo
            "cuadro": "Carbono completo",
            "horquilla": "Carbono",
            "precio_pvp": 3500.0,  # PVP inflado absurdo para Claris
            "precio_oferta": 899.0
        }
        sanitized = sanitize_bike_specs(fake_ad)
        self.assertNotEqual(sanitized["tipo_frenos"], "hidraulico")
        self.assertIn("mecanico", sanitized["tipo_frenos"])
        self.assertIn("Aluminio", sanitized["cuadro"])
        self.assertLessEqual(sanitized["precio_pvp"], 1200.0)
        self.assertEqual(sanitized["especificaciones_verificadas"], 1)
        self.assertIn("[Audit]", sanitized["notas_veredicto"])

    def test_frame_material_cross_validation(self):
        """Verifica la corrección de materiales de cuadro conocidos (T060)."""
        from gravel_bot.components_authority import cross_validate_frame_material

        c_jakar = cross_validate_frame_material("Megamo Jakar 20", "Carbono completo")
        self.assertIn("Aluminio", c_jakar)

        c_grizl_al = cross_validate_frame_material("Canyon Grizl AL 7", "Carbono monocasco")
        self.assertIn("Aluminio", c_grizl_al)

        c_west = cross_validate_frame_material("Megamo West 10", "Aluminio")
        self.assertIn("Carbono", c_west)

    def test_live_stock_and_price_detection(self):
        """Verifica la detección de stock y extracción de precios en HTML (T051, T053, T054)."""
        from gravel_bot.catalog_auditor import detect_stock_status, extract_price_from_html

        html_in_stock = """
        <html>
          <head><meta property="product:price:amount" content="1249.00"></head>
          <body><button class="add-to-cart">Añadir al carrito</button></body>
        </html>
        """
        price = extract_price_from_html(html_in_stock)
        in_stock, status = detect_stock_status(html_in_stock)
        self.assertEqual(price, 1249.0)
        self.assertEqual(in_stock, 1)
        self.assertEqual(status, "verificado")

        html_out_of_stock = """
        <html>
          <body><div class="out-of-stock">Producto agotado temporalmente</div></body>
        </html>
        """
        in_stock_out, status_out = detect_stock_status(html_out_of_stock)
        self.assertEqual(in_stock_out, 0)
        self.assertEqual(status_out, "sin_stock")

    def test_calibrated_rubric_c1_c6_and_warranty_bonus(self):
        """Verifica el cálculo de la rúbrica calibrada C1..C6 con bonus por canal/garantía (T063, T064)."""
        from gravel_bot.evaluator import calcular_rubrica_calibrada

        bike_fisica = {
            "disciplina": "gravel",
            "tipo_frenos": "hidraulico",
            "tipo_transmision": "2x11",
            "cuadro": "Aluminio hidroformado",
            "horquilla": "Carbono",
            "patilla_udh": 0,
            "precio_oferta": 999.0,
            "talla_recomendada_169": "S",
            "tienda_tipo": "fisica"
        }
        res_fisica = calcular_rubrica_calibrada(bike_fisica)
        self.assertEqual(res_fisica["c1_frenos"], 25.0)
        self.assertEqual(res_fisica["c2_transmision"], 25.0)
        self.assertEqual(res_fisica["c6_garantia"], 5.0)
        self.assertGreaterEqual(res_fisica["puntuacion_total"], 90.0)
        self.assertEqual(res_fisica["tier"], "Tier S+")

        bike_particular = dict(bike_fisica)
        bike_particular["tienda_tipo"] = "particular"
        res_part = calcular_rubrica_calibrada(bike_particular)
        self.assertEqual(res_part["c6_garantia"], 0.0)
        self.assertLess(res_part["puntuacion_total"], res_fisica["puntuacion_total"])

    def test_itemized_score_card_generator(self):
        """Verifica la generación de la ficha desglosada C1..C6 (T065)."""
        from gravel_bot.evaluator import get_itemized_score_card

        sample_bike = {
            "id": 1,
            "marca": "Megamo",
            "modelo": "Jakar 30",
            "disciplina": "gravel",
            "tipo_frenos": "hidraulico",
            "tipo_transmision": "2x10",
            "cuadro": "Aluminio",
            "horquilla": "Carbono",
            "precio_oferta": 1099.0,
            "talla_recomendada_169": "S",
            "tienda_nombre": "Mammoth Bikes",
            "tienda_tipo": "fisica",
            "especificaciones_verificadas": 1
        }
        card = get_itemized_score_card(sample_bike)
        self.assertIn("c1", card)
        self.assertIn("c2", card)
        self.assertIn("c3", card)
        self.assertIn("c4", card)
        self.assertIn("c5", card)
        self.assertIn("c6", card)
        self.assertEqual(card["c6"]["pts"], 5.0)
        self.assertIn("total", card)
        self.assertIn("tier", card)

    def test_rescore_execution(self):
        """Verifica que el re-score del catálogo funciona en seco y con persistencia (T066, T067)."""
        from gravel_bot.evaluator import run_catalog_rescore

        res_dry = run_catalog_rescore(dry_run=True)
        self.assertTrue(res_dry["dry_run"])
        self.assertGreater(res_dry["total_bikes"], 0)
        self.assertIn("tier_counts", res_dry)

    def test_bike_inspector_detailed_card(self):
        """Verifica que la ficha técnica contiene desglose C1..C6 e insignias (T068)."""
        from gravel_bot.bike_inspector import format_detailed_bike_card

        msg = format_detailed_bike_card("Jakar 30")
        self.assertIn("VALORACIÓN Y RÚBRICA CALIBRADA C1..C6", msg)
        self.assertIn("C1 Frenos", msg)
        self.assertIn("C6 Garantía & Canal", msg)

    def test_web_server_card_and_stats(self):
        """Verifica los endpoints de auditoría y ficha desglosada en la API REST (T069, T070)."""
        from gravel_bot.web_server import get_catalog_stats_dict, get_sanitized_catalog_dict

        stats = get_catalog_stats_dict()
        self.assertEqual(stats["status"], "success")
        self.assertIn("audit_summary", stats)

        bikes = get_sanitized_catalog_dict()
        self.assertGreater(len(bikes), 0)
        sample = bikes[0]
        self.assertIn("audit_status", sample)
        self.assertIn("c1_frenos", sample)
        self.assertIn("c6_garantia", sample)

class TestCodebaseBloatAndCliParity(unittest.TestCase):
    """Suite de pruebas para la característica 004: Poda de Sobreingeniería y Paridad CLI."""

    def test_cli_entrypoint_delegation(self):
        """Verifica que gravel_bot.cli.main() despacha todos los comandos y banderas (T074)."""
        import io
        from contextlib import redirect_stdout
        from gravel_bot.cli import main

        # 1. Ejecución con --presupuesto y --json
        f = io.StringIO()
        with redirect_stdout(f):
            main(["--presupuesto", "1000", "--json"])
        out = f.getvalue()
        self.assertIn('"status": "success"', out)
        self.assertIn('"budget": 1000.0', out)

        # 2. Ejecución con --re-score y --dry-run
        f = io.StringIO()
        with redirect_stdout(f):
            main(["--re-score", "--dry-run"])
        out = f.getvalue()
        self.assertIn("RECALCULANDO RÚBRICA CALIBRADA", out)

        # 3. Ejecución con --ficha
        f = io.StringIO()
        with redirect_stdout(f):
            main(["--ficha", "Jakar 30"])
        out = f.getvalue()
        self.assertIn("FICHA DETALLADA", out)

class TestGravelBotLegacyCoverage(unittest.TestCase):
    """Cobertura preservada de la suite legacy original (T081)."""

    def setUp(self):
        init_db()

    def test_rubric_tier_s_plus(self):
        """Verifica que una gravel de 1.099 € con GRX 2x10 y frenos hidráulicos en talla S sea Tier S+."""
        from gravel_bot.evaluator import calcular_rubrica
        c1, c2, c3, c4, c5, total, nota, tier = calcular_rubrica(
            disciplina="gravel",
            tipo_frenos="hidraulico",
            tipo_transmision="2x10",
            cuadro="Aluminio 6061",
            horquilla="Carbono",
            patilla_udh=0,
            precio=1099.0,
            talla_valida=True
        )
        self.assertGreaterEqual(total, 90.0)
        self.assertEqual(tier, "Tier S+")
        self.assertGreaterEqual(nota, 9.0)

    def test_rubric_tier_c_for_road_bike(self):
        """Verifica que una bicicleta de carretera o geometría inadecuada sea castigada a Tier C."""
        from gravel_bot.evaluator import calcular_rubrica
        c1, c2, c3, c4, c5, total, nota, tier = calcular_rubrica(
            disciplina="carretera",
            tipo_frenos="mecanico_doble",
            tipo_transmision="2x8",
            cuadro="Aluminio",
            horquilla="Aluminio",
            patilla_udh=0,
            precio=899.0,
            talla_valida=False
        )
        self.assertEqual(tier, "Tier C")
        self.assertLess(nota, 5.0)

    def test_clean_price(self):
        """Verifica el limpiador de precios en formatos europeos y estándar."""
        from gravel_bot.scrapers.base import BaseScraper
        self.assertEqual(BaseScraper.clean_price("1.299,00 €"), 1299.0)
        self.assertEqual(BaseScraper.clean_price("1349.10 €"), 1349.1)
        self.assertEqual(BaseScraper.clean_price("999 €"), 999.0)
        self.assertEqual(BaseScraper.clean_price("4.549,35 €"), 4549.35)

    def test_spec_detection(self):
        """Verifica que el extractor heurístico identifique GRX, hidráulicos y talla S."""
        from gravel_bot.evaluator import detect_bike_specs
        title = "Bicicleta Megamo Jakar 30 2026 Shimano GRX RX400 2x10v"
        sizes = ["S", "M", "L"]
        specs = detect_bike_specs(title=title, price=1199.0, sizes=sizes)
        self.assertEqual(specs["marca"], "Megamo")
        self.assertEqual(specs["tipo_frenos"], "hidraulico")
        self.assertEqual(specs["tipo_transmision"], "2x10")
        self.assertEqual(specs["tier"], "Tier S+")
        self.assertIn("S", specs["talla_recomendada_169"])

    def test_alert_deduplication(self):
        """Verifica que no se dupliquen alertas en la base de datos."""
        from gravel_bot.db import get_connection, mark_alert_sent, was_alert_sent
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM bicicletas LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            bike_id = row["id"]
            mark_alert_sent(bike_id, 1100.0, "Tier S+", 9.5, "telegram_test")
            self.assertTrue(was_alert_sent(bike_id, 1100.0))
            self.assertTrue(was_alert_sent(bike_id, 1200.0))

    def test_telegram_message_formatting(self):
        """Verifica que el mensaje generado para Telegram sea rico y contenga enlaces y badges."""
        from gravel_bot.notifier import format_alert_message
        bike = {
            "marca": "Orbea",
            "modelo": "Terra H40 2024",
            "tier": "Tier S+",
            "nota": 9.6,
            "precio_oferta": 1250.0,
            "precio_pvp": 2099.0,
            "talla_recomendada_169": "S (51 cm)",
            "transmision": "Shimano GRX 2x10v",
            "frenos": "Shimano GRX Hidráulico",
            "cuadro": "Aluminio Triple Conificado",
            "tienda_nombre": "Calmera Atocha",
            "url_oferta": "https://ciclismo.calmera.es"
        }
        msg = format_alert_message(bike)
        self.assertIn("NUEVA GANGA GRAVEL", msg)
        self.assertIn("Orbea Terra H40 2024", msg)
        self.assertIn("1250 €", msg)
        self.assertIn("Ahorras 849 €", msg)
        self.assertIn("Calmera Atocha", msg)

    def test_dynamic_geometry_sizing_by_brand(self):
        """Verifica que el tallaje sea dinámico por marca/modelo y no global."""
        from gravel_bot.geometry_sizing import get_recommended_size_dynamic, evaluate_size_compatibility_dynamic
        canyon_size = get_recommended_size_dynamic("Canyon", "Grizl", 169)
        self.assertEqual(canyon_size["talla_recomendada"], "XS")
        compat, nom, _ = evaluate_size_compatibility_dynamic("Canyon", "Grizl", 169, ["s", "m"])
        self.assertFalse(compat)

        focus_size = get_recommended_size_dynamic("Focus", "ATLAS", 169)
        self.assertIn("XS", focus_size["talla_recomendada"])

        trek_size = get_recommended_size_dynamic("Trek", "Checkpoint", 169)
        self.assertEqual(trek_size["talla_recomendada"], "52 cm")

        conor_size = get_recommended_size_dynamic("Conor", "Kalima", 169)
        self.assertIn("SM", conor_size["talla_recomendada"])

    def test_multi_user_profile_crud(self):
        """Verifica la persistencia y actualización de perfiles de usuario en SQLite."""
        from gravel_bot.db import get_or_create_user, get_user_profile, update_user_profile
        test_chat_id = 999888777
        user_id = get_or_create_user(test_chat_id, "test_cyclist")
        update_user_profile(user_id, estatura_cm=178, presupuesto_max=1800.0, preferencia_transmision="1x")
        prof = get_user_profile(user_id)
        self.assertIsNotNone(prof)
        self.assertEqual(prof["estatura_cm"], 178)
        self.assertEqual(prof["presupuesto_max"], 1800.0)
        self.assertEqual(prof["preferencia_transmision"], "1x")
        self.assertEqual(prof["talla_calculada"], "M")

    def test_bike_record_validator(self):
        """Verifica la auditoría de campos técnicos y precios coherentes."""
        from gravel_bot.validator import validate_bike_record
        bike = {
            "marca": "Canyon",
            "modelo": "Grizl 6 AL",
            "precio_oferta": 1199.0,
            "precio_pvp": 1499.0,
            "tipo_frenos": "hidraulico",
            "tipo_transmision": "2x10"
        }
        val = validate_bike_record(bike, altura_cm=169)
        self.assertTrue(val["valid"])
        self.assertEqual(val["talla_dinamica_calculada"], "XS")

    def test_budget_tolerance_stretch_deal(self):
        """Verifica que ofertas superiores al presupuesto base entren con holgura si están justificadas."""
        from gravel_bot.evaluator import calcular_rubrica_personalizada
        perfil = {
            "estatura_cm": 169,
            "presupuesto_max": 1000.0,
            "holgura_max_pct": 15.0,
            "preferencia_transmision": "2x",
            "terreno_asfalto_pct": 50
        }
        bike_gran_oferta = {
            "marca": "Megamo",
            "modelo": "Jakar 30 2x10",
            "precio_oferta": 1100.0,
            "precio_pvp": 1499.0,
            "tipo_frenos": "hidraulico",
            "tipo_transmision": "2x10",
            "cuadro": "Aluminio con horquilla carbono",
            "talla_recomendada_169": "S (52 cm)",
            "disciplina": "gravel",
            "horquilla": "Carbono",
            "patilla_udh": 0
        }
        res = calcular_rubrica_personalizada(bike_gran_oferta, perfil)
        self.assertTrue(res["holgura_aplicada"])
        self.assertGreaterEqual(res["c4_precio"], 15.0)
        self.assertIn(res["tier"], ["Tier S+", "Tier S"])
if __name__ == "__main__":
    unittest.main()
