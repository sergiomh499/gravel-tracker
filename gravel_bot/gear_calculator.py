"""
Calculadora cinemática de transmisiones y cadencia para gravel (rueda 700x40c estándar ~2185 mm).
Calcula ratio de subida (climbing ratio), velocidad en llano a 80-100 rpm y metros de desarrollo.
"""
from typing import Dict, Any, List, Optional

WHEEL_CIRCUMFERENCE_MM = 2185  # 700x40c estándar ETRTO 622-40

PRESET_CONFIGS = {
    "2x": {
        "nombre": "Shimano GRX 2x10v (46/30 x 11-36)",
        "chainrings": [46, 30],
        "cogs": [11, 13, 15, 17, 19, 21, 24, 28, 32, 36],
        "desc": "El rey polivalente para 50/50: saltos cerrados en asfalto y rampa suave en tierra."
    },
    "1x": {
        "nombre": "Shimano CUES / SRAM 1x (40T x 11-48)",
        "chainrings": [40],
        "cogs": [11, 13, 15, 18, 21, 24, 28, 32, 37, 42, 48],
        "desc": "Simplicidad monoplato: un solo mando, sin roces de desviador, pero saltos más abiertos."
    },
    "2x11": {
        "nombre": "Shimano GRX 2x11v / 2x12v (48/31 x 11-34)",
        "chainrings": [48, 31],
        "cogs": [11, 12, 13, 14, 15, 17, 19, 21, 24, 27, 30, 34],
        "desc": "Configuración rodadora: más punta en bajada de asfalto y cadencia quirúrgica."
    },
    "1x12": {
        "nombre": "SRAM Apex Eagle 1x12v (40T x 11-50)",
        "chainrings": [40],
        "cogs": [11, 13, 15, 17, 19, 22, 25, 28, 32, 36, 42, 50],
        "desc": "Gama ultra amplia para montaña extrema con saltos escalonados."
    }
}

def speed_kmh(chainring: int, cog: int, rpm: int, circ_mm: int = WHEEL_CIRCUMFERENCE_MM) -> float:
    """Calcula velocidad en km/h dados plato, piñón, cadencia (rpm) y circunferencia."""
    gear_ratio = chainring / cog
    meters_per_stroke = (gear_ratio * circ_mm) / 1000.0
    return round((meters_per_stroke * rpm * 60) / 1000.0, 1)

def development_meters(chainring: int, cog: int, circ_mm: int = WHEEL_CIRCUMFERENCE_MM) -> float:
    """Metros avanzados por pedalada completa."""
    return round((chainring / cog) * (circ_mm / 1000.0), 2)

def analyze_drivetrain(chainrings: List[int], cogs: List[int]) -> Dict[str, Any]:
    """Analiza rango porcentual, ratio mínimo de escalada y velocidades máximas/mínimas."""
    chainrings_sorted = sorted(chainrings)
    cogs_sorted = sorted(cogs)

    big_ring = chainrings_sorted[-1]
    small_ring = chainrings_sorted[0]
    small_cog = cogs_sorted[0]
    big_cog = cogs_sorted[-1]

    highest_ratio = big_ring / small_cog
    lowest_ratio = small_ring / big_cog
    gear_range_pct = round((highest_ratio / lowest_ratio) * 100, 1)

    return {
        "highest_ratio": round(highest_ratio, 2),
        "lowest_ratio": round(lowest_ratio, 2),
        "gear_range_pct": gear_range_pct,
        "speed_max_90rpm": speed_kmh(big_ring, small_cog, 90),
        "speed_max_105rpm": speed_kmh(big_ring, small_cog, 105),
        "speed_min_75rpm": speed_kmh(small_ring, big_cog, 75),
        "meters_max": development_meters(big_ring, small_cog),
        "meters_min": development_meters(small_ring, big_cog),
        "climbing_ability": "Sobresaliente (< 0.90)" if lowest_ratio < 0.90 else (
            "Bueno (0.90 - 1.00)" if lowest_ratio <= 1.00 else "Exigente (> 1.00)"
        )
    }

def format_gear_simulation_message(preset_or_query: str = "2x") -> str:
    """Genera mensaje formatado en HTML para Telegram comparando desarrollos o calculando a medida."""
    query = preset_or_query.lower().strip()
    config = PRESET_CONFIGS.get(query)

    if not config:
        if "1x" in query or "mono" in query:
            config = PRESET_CONFIGS["1x"]
        else:
            config = PRESET_CONFIGS["2x"]

    res = analyze_drivetrain(config["chainrings"], config["cogs"])
    platos_str = "/".join(str(c) for c in config["chainrings"])
    pinones_str = f"{config['cogs'][0]}-{config['cogs'][-1]}"

    msg = f"⚙️ <b>SIMULADOR CINEMÁTICO: {config['nombre']}</b> ⚙️\n\n"
    msg += f"• <b>Plato(s):</b> <code>{platos_str}T</code> | <b>Cassette:</b> <code>{pinones_str}T</code>\n"
    msg += f"• <b>Rango Total de Transmisión:</b> <b>{res['gear_range_pct']}%</b>\n"
    msg += f"• <b>Capacidad de Escalada (Rampa > 12%):</b> {res['climbing_ability']} (Ratio: <code>{res['lowest_ratio']}</code>)\n\n"

    msg += "🚴‍♂️ <b>Velocidades Teóricas (Cubierta 700x40c):</b>\n"
    msg += f" • 🟢 <b>Subida dura (75 rpm):</b> <code>{res['speed_min_75rpm']} km/h</code> ({res['meters_min']} m/pedalada)\n"
    msg += f" • 🟡 <b>Crucero llano (90 rpm):</b> <code>{res['speed_max_90rpm']} km/h</code> ({res['meters_max']} m/pedalada)\n"
    msg += f" • 🔴 <b>Sprint / Bajada (105 rpm):</b> <code>{res['speed_max_105rpm']} km/h</code>\n\n"

    msg += f"💡 <i>{config['desc']}</i>\n\n"
    msg += "👉 Prueba: <code>/desarrollo 1x</code>, <code>/desarrollo 2x</code> o <code>/desarrollo 2x11</code>"
    return msg
