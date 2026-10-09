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

    def test_tuvalum_scraper_integration(self):
        """Verifica la extracción y fallback de bicicletas reacondicionadas en Tuvalum."""
        from gravel_bot.scrapers.tuvalum import TuvalumScraper
        from gravel_bot.scrapers import get_all_scrapers

        scraper = TuvalumScraper()
        items = scraper.scrape()
        self.assertGreater(len(items), 0)
        first = items[0]
        self.assertIn("title", first)
        self.assertIn("price", first)
        self.assertGreater(first["price"], 400)
        self.assertIn("url", first)
        self.assertEqual(first["tienda_slug"], "tuvalum")

        # Verificar que está en la lista de scrapers activos
        all_active = [s.name for s in get_all_scrapers()]
        self.assertIn("tuvalum", all_active)

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
if __name__ == "__main__":
    unittest.main()
