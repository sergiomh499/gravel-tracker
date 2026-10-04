"""
test_intensive.py - Suite Completa y Exhaustiva de Tests de Todos los Módulos
Valida la integridad de Base de Datos, Base de Conocimiento, Biomecánica, Tallaje Dinámico,
Validador de Enlaces, Rúbrica Ponderada y Servicio de Telegram.
"""

import unittest
import os
import sqlite3
import json
from unittest.mock import patch, MagicMock

# Importaciones de los módulos a auditar
from gravel_bot.db import (
    init_db, get_connection, upsert_bike, get_all_bikes, get_deals,
    get_or_create_store, record_price, was_alert_sent, mark_alert_sent,
    get_or_create_user, get_user_profile, update_user_profile,
    get_all_active_profiles, was_alert_sent_to_user, mark_alert_sent_to_user
)
from gravel_bot.knowledge_base import KnowledgeBase
from gravel_bot.biomechanics import (
    calculate_climbing_ratio, calculate_gear_inches, evaluate_drivetrain_biomechanics,
    classify_geometry_aggressiveness, calculate_speed_at_cadence
)
from gravel_bot.geometry_sizing import (
    get_recommended_size_dynamic, evaluate_size_compatibility_dynamic,
    get_brand_geometry_rule
)
from gravel_bot.evaluator import (
    detect_bike_specs, calcular_rubrica, calcular_rubrica_personalizada,
    calcular_talla_desde_estatura
)
from gravel_bot.validator import (
    validate_bike_record, check_url_and_price_health, run_full_catalog_validation
)
from gravel_bot.scrapers.base import BaseScraper
from gravel_bot.scrapers.wallapop import WallapopMadridScraper
from gravel_bot.notifier import format_alert_message
from gravel_bot.bot_service import (
    format_profile_message, format_tier_list_message, format_deals_message,
    get_profile_for_chat
)

class TestDatabaseLayer(unittest.TestCase):
    """Pruebas intensivas sobre SQLite, integridad de esquema y operaciones CRUD."""

    def setUp(self):
        init_db()

    def test_schema_tables_exist(self):
        """Verifica que todas las tablas requeridas existan en la base de datos."""
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in c.fetchall()]
        conn.close()

        expected = [
            "tiendas", "bicicletas", "historial_precios", "alertas_notificadas",
            "usuarios", "perfiles_ciclista", "alertas_por_usuario"
        ]
        for t in expected:
            self.assertIn(t, tables, f"La tabla {t} no existe en la base de datos.")

    def test_store_creation_and_retrieval(self):
        """Verifica la inserción idempotente de tiendas físicas y online."""
        store_id = get_or_create_store(
            slug="test_store_madrid",
            nombre="Tienda Test Madrid",
            tipo="fisica",
            url="https://test.madrid.bike",
            direccion="Calle Retama 5, Méndez Álvaro"
        )
        self.assertGreater(store_id, 0)
        # Segunda llamada debe retornar el mismo ID
        store_id_again = get_or_create_store("test_store_madrid", "Tienda Test Madrid")
        self.assertEqual(store_id, store_id_again)

    def test_upsert_bike_and_price_history(self):
        """Verifica la inserción y actualización de bicicletas con registro de historial de precio."""
        bike = {
            "slug": "test_gravel_special_1000",
            "marca": "TestBrand",
            "modelo": "Gravel Expert 2025",
            "ano": 2025,
            "disciplina": "gravel",
            "transmision": "Shimano GRX 2x10",
            "tipo_transmision": "2x10",
            "frenos": "Shimano Hidráulicos",
            "tipo_frenos": "hidraulico",
            "cuadro": "Aluminio 6061",
            "horquilla": "Carbono",
            "ejes": "Pasantes 12mm",
            "patilla_udh": 1,
            "talla_recomendada_169": "S (52 cm)",
            "precio_pvp": 1500.0,
            "precio_oferta": 999.0,
            "tienda_id": 1,
            "url_oferta": "https://test.com/bike",
            "en_stock": 1,
            "c1_frenos": 25.0,
            "c2_transmision": 24.0,
            "c3_cuadro": 18.0,
            "c4_precio": 20.0,
            "c5_talla": 10.0,
            "puntuacion_total": 97.0,
            "nota": 9.7,
            "tier": "Tier S+",
            "notas_veredicto": "Modelo de test"
        }
        bike_id = upsert_bike(bike)
        self.assertGreater(bike_id, 0)

        # Grabar historial de precio
        record_price(bike_id, 1, 999.0, "S", "https://test.com/bike", "Oferta inicial")

        # Comprobar que get_deals la encuentra
        deals = get_deals(min_discount_pct=25.0)
        test_deal = [d for d in deals if d["slug"] == "test_gravel_special_1000"]
        self.assertEqual(len(test_deal), 1)
        self.assertGreaterEqual(test_deal[0]["descuento_pct"], 30.0)

        # Limpieza inmediata de datos de test
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM historial_precios WHERE bicicleta_id = ?", (bike_id,))
        c.execute("DELETE FROM bicicletas WHERE id = ?", (bike_id,))
        conn.commit()
        conn.close()

    def test_user_profile_lifecycle(self):
        """Verifica la gestión del perfil de ciclista y cálculo dinámico de talla base."""
        chat_id = 123456789
        user_id = get_or_create_user(chat_id, "sergio_test")
        self.assertGreater(user_id, 0)

        # Actualizar estatura a 176 cm -> debe calcular talla M
        update_user_profile(chat_id, estatura_cm=176, presupuesto_max=1200.0, holgura_max_pct=20.0)
        prof = get_user_profile(chat_id)
        self.assertEqual(prof["estatura_cm"], 176)
        self.assertEqual(prof["talla_calculada"], "M")
        self.assertEqual(prof["presupuesto_max"], 1200.0)
        self.assertEqual(prof["holgura_max_pct"], 20.0)

    def test_alert_deduplication_per_user(self):
        """Verifica que una alerta no se duplique al mismo usuario a un precio igual o superior."""
        user_id = get_or_create_user(777888999, "cyclist_dedup")
        bike_id = 99999
        conn = get_connection()
        conn.cursor().execute("DELETE FROM alertas_por_usuario WHERE usuario_id = ?", (user_id,))
        conn.commit()
        conn.close()

        self.assertFalse(was_alert_sent_to_user(user_id, bike_id, 1050.0))
        mark_alert_sent_to_user(user_id, bike_id, 1050.0)
        # Ya fue notificado a 1050 -> a 1050 o más no se envía
        self.assertTrue(was_alert_sent_to_user(user_id, bike_id, 1050.0))
        self.assertTrue(was_alert_sent_to_user(user_id, bike_id, 1100.0))
        # Pero si baja a 950 €, sí debe permitir re-notificar
        self.assertFalse(was_alert_sent_to_user(user_id, bike_id, 950.0))

class TestKnowledgeBase(unittest.TestCase):
    """Pruebas sobre el motor desacoplado de componentes técnicos."""

    def setUp(self):
        self.kb = KnowledgeBase.get_instance()

    def test_drivetrain_matching(self):
        """Verifica la identificación correcta de grupos 1x y 2x."""
        rx400 = self.kb.match_drivetrain("Bicicleta Gravel con Shimano GRX RX400 2x10 velocidades")
        self.assertIsNotNone(rx400)
        self.assertEqual(rx400["tipo"], "2x10")
        self.assertEqual(rx400["climbing_ratio"], 0.83)

        cues = self.kb.match_drivetrain("Montaje monoplato Shimano CUES U6000 1x10v")
        self.assertIsNotNone(cues)
        self.assertEqual(cues["tipo"], "1x10")

        apex_axs = self.kb.match_drivetrain("SRAM Apex XPLR AXS electrónico 12 velocidades")
        self.assertIsNotNone(apex_axs)
        self.assertEqual(apex_axs["accionamiento"], "electronico")

    def test_brakes_matching(self):
        """Verifica la clasificación precisa de frenos hidráulicos vs mecánicos."""
        grx_brakes = self.kb.match_brakes("Frenos de disco hidráulicos Shimano GRX BR-RX400")
        self.assertEqual(grx_brakes["tipo"], "hidraulico")
        self.assertEqual(grx_brakes["puntos"], 25.0)

        hyrd_brakes = self.kb.match_brakes("Frenos TRP HY/RD semi-hidráulicos")
        self.assertEqual(hyrd_brakes["tipo"], "semihidraulico")
        self.assertEqual(hyrd_brakes["puntos"], 16.0)

        mech_brakes = self.kb.match_brakes("Frenos mecánicos por cable Tektro Mira")
        self.assertEqual(mech_brakes["tipo"], "mecanico_doble")

    def test_score_components_weighting(self):
        """Verifica que el terreno 50/50 pondere adecuadamente el asfalto y la tierra."""
        res = self.kb.score_components("Shimano GRX RX400 2x10v disco hidraulico", terreno_asfalto_pct=50)
        self.assertGreaterEqual(res["score_transmision"], 23.0)
        self.assertEqual(res["score_frenos"], 25.0)

class TestBiomechanicsEngine(unittest.TestCase):
    """Pruebas sobre el motor biomecánico de desarrollos y geometrías."""

    def test_climbing_ratio_calculations(self):
        """Verifica el cálculo del ratio mínimo de subida."""
        # GRX 2x10: plato 30, corona 36 -> 30/36 = 0.83
        r_grx = calculate_climbing_ratio([46, 30], [11, 36])
        self.assertEqual(r_grx, 0.83)

        # CUES 1x10: plato 40, corona 48 -> 40/48 = 0.83
        r_cues = calculate_climbing_ratio([40], [11, 48])
        self.assertEqual(r_cues, 0.83)

        # Carretera tradicional: plato 34, corona 32 -> 34/32 = 1.06 (duro)
        r_road = calculate_climbing_ratio([50, 34], [11, 32])
        self.assertEqual(r_road, 1.06)

    def test_gear_inches_calculation(self):
        """Verifica los desarrollos mínimos y máximos en pulgadas de avance."""
        # 30/36 en rueda 700x40c (~27.64 pulgadas) -> 23.0 inches
        low_in = calculate_gear_inches(30, 36)
        self.assertAlmostEqual(low_in, 23.0, places=0)

        # 46/11 -> ~115.6 inches
        high_in = calculate_gear_inches(46, 11)
        self.assertAlmostEqual(high_in, 115.6, places=0)

    def test_speed_at_cadence(self):
        """Verifica la velocidad teórica calculada a 85 RPM en plato grande."""
        speed = calculate_speed_at_cadence(46, 11, cadencia_rpm=85)
        # 46/11 * 2.182 m * 85 * 60 / 1000 = ~46.5 km/h
        self.assertGreaterEqual(speed, 45.0)
        self.assertLessEqual(speed, 48.0)

    def test_stack_reach_aggressiveness(self):
        """Verifica la clasificación de geometrías según el ratio Stack/Reach."""
        # Endurance relajada: Stack 580, Reach 370 -> Ratio 1.57 (>1.55)
        endurance = classify_geometry_aggressiveness(580.0, 370.0)
        self.assertEqual(endurance["categoria"], "Gran Fondo / Resistencia")

        # Aero agresiva: Stack 540, Reach 385 -> Ratio 1.40 (<1.48)
        aero = classify_geometry_aggressiveness(540.0, 385.0)
        self.assertEqual(aero["categoria"], "Aero Competición")

class TestDynamicGeometrySizing(unittest.TestCase):
    """Pruebas del tallaje no global por marca, modelo y estatura."""

    def test_canyon_grizl_sizing_strict_169(self):
        """Canyon a 1,69m exige XS; S y M deben ser estrictamente rechazadas."""
        canyon_169 = get_recommended_size_dynamic("Canyon", "Grizl", 169)
        self.assertEqual(canyon_169["talla_recomendada"], "XS")

        # Anuncio con S y M -> no compatible
        compat, _, _ = evaluate_size_compatibility_dynamic("Canyon", "Grizl", 169, ["S", "M"])
        self.assertFalse(compat)

        # Anuncio con XS -> compatible
        compat_xs, _, _ = evaluate_size_compatibility_dynamic("Canyon", "Grizl", 169, ["XS"])
        self.assertTrue(compat_xs)

    def test_trek_checkpoint_sizing_cm(self):
        """Trek usa tallas numéricas; para 1,69m la talla es 52 cm."""
        trek_169 = get_recommended_size_dynamic("Trek", "Checkpoint", 169)
        self.assertEqual(trek_169["talla_recomendada"], "52 cm")

    def test_conor_kalima_sizing_sm(self):
        """Conor etiqueta como SM (51 cm) para 1,69m."""
        conor_169 = get_recommended_size_dynamic("Conor", "Kalima", 169)
        self.assertIn("SM", conor_169["talla_recomendada"])

    def test_sizing_for_different_rider_heights(self):
        """Comprueba que el motor calcule tallas diferentes para diferentes estaturas."""
        # 160 cm -> XS o 2XS
        size_160 = get_recommended_size_dynamic("Orbea", "Terra", 160)
        self.assertEqual(size_160["talla_recomendada"], "XS")

        # 175 cm -> M
        size_175 = get_recommended_size_dynamic("Orbea", "Terra", 175)
        self.assertIn("M", size_175["talla_recomendada"])

        # 185 cm -> L
        size_185 = get_recommended_size_dynamic("Orbea", "Terra", 185)
        self.assertIn("L", size_185["talla_recomendada"])

class TestValidatorAndHealthEngine(unittest.TestCase):
    """Pruebas sobre el validador automático de enlaces, stock y fichas."""

    def test_validate_bike_record_coherence(self):
        """Verifica que detecte modelos incompletos o errores en precios."""
        bad_bike = {
            "marca": "",
            "modelo": "",
            "precio_oferta": -50.0,
            "tipo_frenos": "desconocido"
        }
        val = validate_bike_record(bad_bike, altura_cm=169)
        self.assertFalse(val["valid"])
        self.assertGreater(len(val["errors"]), 0)

    def test_check_url_empty_or_malformed(self):
        """Verifica que URLs vacías o sin protocolo sean marcadas como inválidas."""
        res = check_url_and_price_health("")
        self.assertFalse(res["is_alive"])
        self.assertTrue(res["is_out_of_stock"])

    def test_full_catalog_validation_run(self):
        """Verifica que run_full_catalog_validation se ejecute sin errores."""
        summary = run_full_catalog_validation(auto_repair=True, limit=10, verbose=False)
        self.assertGreaterEqual(summary["total_auditadas"], 1)

class TestPersonalizedRubricAndBudgetTolerance(unittest.TestCase):
    """Pruebas sobre la rúbrica personalizada y la holgura en chollos."""

    def test_budget_tolerance_activation(self):
        """Verifica que una bicicleta con gran oferta active la holgura de presupuesto."""
        perfil = {
            "estatura_cm": 169,
            "presupuesto_max": 1000.0,
            "holgura_max_pct": 15.0, # Límite: 1.150 €
            "preferencia_transmision": "2x",
            "terreno_asfalto_pct": 50
        }
        bike = {
            "marca": "Megamo",
            "modelo": "Jakar 30 2025",
            "precio_oferta": 1099.0,
            "precio_pvp": 1499.0, # 27% descuento
            "tipo_frenos": "hidraulico",
            "tipo_transmision": "2x10",
            "disciplina": "gravel",
            "cuadro": "Aluminio hidroformado",
            "horquilla": "Carbono",
            "patilla_udh": 0,
            "talla_recomendada_169": "S (52 cm)"
        }
        ev = calcular_rubrica_personalizada(bike, perfil)
        self.assertTrue(ev["holgura_aplicada"])
        self.assertGreaterEqual(ev["c4_precio"], 16.0)
        self.assertIn(ev["tier"], ["Tier S+", "Tier S"])

    def test_strict_penalty_exceeding_tolerance(self):
        """Verifica que bicis por encima de la holgura sean penalizadas en C4."""
        perfil = {
            "estatura_cm": 169,
            "presupuesto_max": 1000.0,
            "holgura_max_pct": 15.0 # Límite: 1.150 €
        }
        bike_cara = {
            "marca": "Canyon",
            "modelo": "Grizl CF SL",
            "precio_oferta": 2499.0, # Supera con creces el límite
            "precio_pvp": 2999.0,
            "tipo_frenos": "hidraulico",
            "tipo_transmision": "2x12",
            "disciplina": "gravel",
            "cuadro": "Carbono",
            "horquilla": "Carbono",
            "patilla_udh": 0,
            "talla_recomendada_169": "XS"
        }
        ev = calcular_rubrica_personalizada(bike_cara, perfil)
        self.assertFalse(ev["holgura_aplicada"])
        self.assertLessEqual(ev["c4_precio"], 2.0)

class TestScrapersAndCleaning(unittest.TestCase):
    """Pruebas sobre el formateo de precios y scrapers."""

    def test_clean_price_formats(self):
        """Verifica parseo de precios europeos y anglosajones."""
        self.assertEqual(BaseScraper.clean_price("1.399,00 €"), 1399.0)
        self.assertEqual(BaseScraper.clean_price("999 €"), 999.0)
        self.assertEqual(BaseScraper.clean_price("1049.95"), 1049.95)
        self.assertEqual(BaseScraper.clean_price(""), 0.0)

    def test_clean_text_html(self):
        """Verifica la eliminación de etiquetas HTML en descripciones."""
        cleaned = BaseScraper.clean_text("<p>Bicicleta con <b>frenos hidráulicos</b></p>")
        self.assertEqual(cleaned, "Bicicleta con frenos hidráulicos")

class TestTelegramBotFormatting(unittest.TestCase):
    """Pruebas sobre la generación de mensajes y seguridad HTML."""

    def test_profile_message_generation(self):
        """Verifica que el mensaje del perfil incluya las marcas y la holgura."""
        msg = format_profile_message(4983947, "sergio")
        self.assertIn("TU PERFIL DE CICLISTA", msg)
        self.assertIn("Canyon", msg)
        self.assertIn("Focus", msg)
        self.assertIn("Trek", msg)
        self.assertIn("Holgura para Chollazos", msg)

    def test_tier_list_message_generation(self):
        """Verifica la generación del Tier list personalizado."""
        msg = format_tier_list_message(4983947)
        self.assertIn("TIER LIST PERSONALIZADO", msg)

    def test_deals_message_generation(self):
        """Verifica la generación del ranking de descuentos."""
        msg = format_deals_message()
        self.assertIn("MAYORES GANGAS", msg)


class TestAntiBanEngine(unittest.TestCase):
    """Pruebas sobre el motor de evasión de bloqueos, perfiles de navegador y retos CAPTCHA."""

    def test_browser_profiles_integrity(self):
        """Verifica que todos los perfiles de navegación tengan cabeceras válidas y coherentes."""
        from gravel_bot.anti_ban import BROWSER_PROFILES
        self.assertGreaterEqual(len(BROWSER_PROFILES), 3)
        for prof in BROWSER_PROFILES:
            headers = prof["headers"]
            self.assertIn("User-Agent", headers)
            self.assertIn("Accept", headers)
            self.assertTrue(headers["User-Agent"].startswith("Mozilla/5.0"))

    def test_challenge_detection(self):
        """Verifica la detección de retos Cloudflare Turnstile y CAPTCHA."""
        from gravel_bot.anti_ban import ResilientSession
        cf_html = "<html><head><title>Just a moment...</title></head><body><div id='cf-chl-widget'>Ray ID: 88923a</div></body></html>"
        self.assertTrue(ResilientSession.detect_anti_bot_challenge(cf_html, 403))
        self.assertTrue(ResilientSession.detect_anti_bot_challenge("Please complete the recaptcha to continue", 503))
        # HTML limpio no debe ser detectado
        self.assertFalse(ResilientSession.detect_anti_bot_challenge("<html><body><h1>Megamo Jakar</h1></body></html>", 200))

    def test_domain_cooldown_activation(self):
        """Verifica que la activación de enfriamiento impida peticiones repetidas al mismo dominio."""
        from gravel_bot.anti_ban import ResilientSession
        domain = "test-protected-shop.com"
        self.assertFalse(ResilientSession.is_in_cooldown(domain))
        ResilientSession.set_cooldown(domain, seconds=60.0)
        self.assertTrue(ResilientSession.is_in_cooldown(domain))

class TestStoreRecommender(unittest.TestCase):
    """Pruebas del recomendador de tiendas físicas en Madrid."""

    def test_proximity_ranking(self):
        """Verifica que Sanferbike M-30 sea la tienda #1 en proximidad (< 1 km)."""
        from gravel_bot.store_recommender import get_recommended_physical_stores, format_stores_recommendation_message
        stores = get_recommended_physical_stores()
        self.assertGreaterEqual(len(stores), 3)
        self.assertEqual(stores[0]["nombre"], "Sanferbike M-30")
        self.assertLess(stores[0]["distancia_km"], 1.0)

        # Verificar mensaje formateado
        msg = format_stores_recommendation_message()
        self.assertIn("TIENDAS FÍSICAS RECOMENDADAS", msg)
        self.assertIn("Sanferbike M-30", msg)
        self.assertIn("Calmera Ciclismo", msg)

class TestPureDealDetector(unittest.TestCase):
    """Pruebas sobre el detector puro de gangas por diferencia de precio."""

    def test_pure_deals_sorting(self):
        """Verifica que las ofertas se ordenen por ahorro económico real."""
        from gravel_bot.deal_detector import get_pure_deals, format_pure_deals_message
        deals = get_pure_deals(sort_by="ahorro_eur", limit=5)
        if deals:
            for d in deals:
                self.assertGreater(d["ahorro_eur"], 0.0)
                self.assertGreater(d["descuento_pct"], 0.0)

        msg = format_pure_deals_message()
        self.assertIn("DETECTOR DE GANGAS", msg)
if __name__ == "__main__":
    unittest.main()
