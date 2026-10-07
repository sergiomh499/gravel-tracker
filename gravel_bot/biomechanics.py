"""
gravel_bot.biomechanics - Motor Biomecánico y Simulador de Desarrollos
Calcula ratios de subida (Climbing Ratio), Gear Inches, cadencia a velocidad y
clasifica la agresividad postural según el ratio Stack/Reach.
"""

from typing import Dict, Any, List, Optional, Tuple

CIRCUNFERENCIA_700X40_M = 2.182 # Metros por vuelta de rueda estándar 700x40c
DIAMETRO_700X40_PULGADAS = 27.64

def calculate_climbing_ratio(platos: List[int], cassette: List[int]) -> float:
    """
    Calcula el ratio mínimo de subida (Climbing Gear Ratio).
    Fórmula: Dientes Plato Mínimo / Dientes Corona Máxima.
    Ratio <= 0.85: Excelente para subir rampas de tierra sin forzar rodillas.
    Ratio > 1.00: Desarrollo excesivamente duro de carretera tradicional.
    """
    if not platos or not cassette:
        return 0.90
    min_plato = min(platos)
    max_corona = max(cassette)
    if max_corona <= 0:
        return 0.90
    return round(min_plato / max_corona, 2)

def calculate_gear_inches(plato: int, corona: int, diametro_rueda_pulgadas: float = DIAMETRO_700X40_PULGADAS) -> float:
    """
    Calcula el desarrollo en Gear Inches (pulgadas de avance).
    Gear Inches = Diámetro rueda (pulgadas) * (Plato / Corona).
    """
    if corona <= 0:
        return 0.0
    return round(diametro_rueda_pulgadas * (plato / corona), 1)

def evaluate_drivetrain_biomechanics(platos: List[int], cassette: List[int]) -> Dict[str, Any]:
    """
    Analiza la idoneidad biomecánica del desarrollo completo para rutas de grava.
    """
    min_plato = min(platos) if platos else 30
    max_plato = max(platos) if platos else 46
    min_corona = min(cassette) if cassette else 11
    max_corona = max(cassette) if cassette else 34

    climb_ratio = calculate_climbing_ratio(platos, cassette)
    lowest_gear_inches = calculate_gear_inches(min_plato, max_corona)
    highest_gear_inches = calculate_gear_inches(max_plato, min_corona)

    if climb_ratio <= 0.80:
        climb_desc = "Desarrollo escalador ultra-ligero (ideal para puertos de tierra con piedras)"
        apto_tierra = True
    elif climb_ratio <= 0.86:
        climb_desc = "Desarrollo óptimo mixto 50/50 (sube cualquier rampa exigente sin desmontar)"
        apto_tierra = True
    elif climb_ratio <= 0.95:
        climb_desc = "Desarrollo estándar exigente en rampas >12%"
        apto_tierra = True
    else:
        climb_desc = "Desarrollo duro de carretera (requiere bajarse en cuestas empinadas de grava)"
        apto_tierra = False

    return {
        "climbing_ratio": climb_ratio,
        "lowest_gear_inches": lowest_gear_inches,
        "highest_gear_inches": highest_gear_inches,
        "apto_tierra": apto_tierra,
        "veredicto_subida": climb_desc
    }

def classify_geometry_aggressiveness(stack_mm: Optional[float], reach_mm: Optional[float]) -> Dict[str, Any]:
    """
    Clasifica la postura del ciclista según el ratio Stack/Reach.
    > 1.55: Gran Fondo / Resistencia (Erguida, relajada, ideal rutas largas).
    1.48 - 1.55: Equilibrada Gravel Mixto.
    < 1.48: Aero Competición (Agresiva, baja, mayor carga cervical).
    """
    if not stack_mm or not reach_mm or reach_mm <= 0:
        return {
            "ratio": 1.52,
            "categoria": "Equilibrada Gravel",
            "descripcion": "Geometría estándar mixta equilibrada."
        }

    ratio = round(stack_mm / reach_mm, 2)
    if ratio > 1.55:
        cat = "Gran Fondo / Resistencia"
        desc = "Postura relajada y erguida, perfecta para comodidad lumbar y largas jornadas."
    elif ratio >= 1.48:
        cat = "Equilibrada Mixta"
        desc = "Equilibrio ideal entre control ágil en tierra y eficiencia rodadora en asfalto."
    else:
        cat = "Aero Competición"
        desc = "Postura rasante y agresiva, mayor velocidad punta pero exige flexibilidad."

    return {
        "ratio": ratio,
        "categoria": cat,
        "descripcion": desc
    }

def calculate_speed_at_cadence(plato: int, corona: int, cadencia_rpm: int = 85) -> float:
    """Calcula la velocidad teórica rodando a una cadencia determinada en km/h."""
    if corona <= 0:
        return 0.0
    desarrollo_metros = (plato / corona) * CIRCUNFERENCIA_700X40_M
    velocidad_kmh = (desarrollo_metros * cadencia_rpm * 60) / 1000.0
    return round(velocidad_kmh, 1)
