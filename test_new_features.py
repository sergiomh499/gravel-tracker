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
        uid = get_or_create_user(777456, "madrid_user")
        update_user_profile(777456, zona="Valencia")
        prof = get_user_profile(777456)
        self.assertEqual(prof["zona"], "Valencia")

        msg = format_profile_message(777456, "madrid_user")
        self.assertIn("Valencia", msg)

    def test_certified_secondhand_filter(self):
        """Verifica el filtrado de bicicletas de ocasión certificada."""
        msg = format_available_bikes_message(store_type="ocasion")
        self.assertIn("BICICLETAS DISPONIBLES EN STOCK", msg)

if __name__ == "__main__":
    unittest.main()
