"""
test_bot.py - Verificación y Pruebas Unitarias del Sistema Modular Gravel Bot
"""

import unittest
import os
import sqlite3
from gravel_bot.config import RIDER_PROFILE, ALERT_CRITERIA
from gravel_bot.db import init_db, get_connection, get_all_bikes, upsert_bike, was_alert_sent, mark_alert_sent
from gravel_bot.evaluator import detect_bike_specs, calcular_rubrica
from gravel_bot.scrapers.base import BaseScraper
from gravel_bot.notifier import format_alert_message, send_telegram_alert

class TestGravelBot(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_rubric_tier_s_plus(self):
        """Verifica que una gravel de 1.099 € con GRX 2x10 y frenos hidráulicos en talla S sea Tier S+."""
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
        self.assertEqual(BaseScraper.clean_price("1.299,00 €"), 1299.0)
        self.assertEqual(BaseScraper.clean_price("1349.10 €"), 1349.1)
        self.assertEqual(BaseScraper.clean_price("999 €"), 999.0)
        self.assertEqual(BaseScraper.clean_price("4.549,35 €"), 4549.35)

    def test_spec_detection(self):
        """Verifica que el extractor heurístico identifique GRX, hidráulicos y talla S."""
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
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM bicicletas LIMIT 1")
        row = c.fetchone()
        conn.close()

        if row:
            bike_id = row["id"]
            # Marcar alerta
            mark_alert_sent(bike_id, 1100.0, "Tier S+", 9.5, "telegram_test")
            # Comprobar que detecta que ya se envió
            self.assertTrue(was_alert_sent(bike_id, 1100.0))
            self.assertTrue(was_alert_sent(bike_id, 1200.0)) # a precio mayor no debe re-alertar

    def test_telegram_message_formatting(self):
        """Verifica que el mensaje generado para Telegram sea rico y contenga enlaces y badges."""
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

if __name__ == "__main__":
    unittest.main()
