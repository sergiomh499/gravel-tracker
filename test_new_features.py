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

if __name__ == "__main__":
    unittest.main()
