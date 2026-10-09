"""
gravel_bot.geometry_sizing - Motor Biomecánico Dinámico de Tallas por Marca y Modelo
Calcula de forma específica y no global la talla exacta, tolerancias y descartes biomecánicos
para cualquier estatura, analizando la geometría real de cada fabricante.
"""

import re
from typing import Dict, Any, List, Tuple, Set, Union
# Tabla maestra de tallajes específicos por fabricante y modelo
BRAND_GEOMETRY_RULES: Dict[str, Dict[str, Any]] = {
    "canyon": {
        "comportamiento": "talla_muy_grande",
        "factor_ajuste": -1, # Equivale a 1 talla menos que el estándar
        "rangos_estatura": [
            (0, 165, "2XS", {"2xs", "xxs", "46"}),
            (166, 172, "XS", {"xs", "48", "extra small"}),
            (173, 178, "S", {"s", "51", "small"}),
            (179, 184, "M", {"m", "54", "medium"}),
            (185, 190, "L", {"l", "57", "large"}),
            (191, 999, "XL", {"xl", "60", "extra large"})
        ],
        "descartes_estrictos_169": {"s", "m", "l", "xl", "54", "56"},
        "razon": "Canyon utiliza Stack/Reach alargado. La talla S es para estaturas >1,73m; a 1,69m causa hiperextensión lumbar y cervical."
    },
    "focus": {
        "comportamiento": "talla_muy_grande",
        "factor_ajuste": -1,
        "rangos_estatura": [
            (0, 165, "2XS", {"2xs", "xxs"}),
            (166, 172, "XS (48)", {"xs", "48"}),
            (173, 179, "S (51)", {"s", "51"}),
            (180, 186, "M (54)", {"m", "54"}),
            (187, 999, "L (57)", {"l", "57"})
        ],
        "descartes_estrictos_169": {"s", "m", "l", "54"},
        "razon": "Focus ATLAS tiene geometría inspirada en MTB muy larga. La XS es obligatoria a 1,69m."
    },
    "trek": {
        "comportamiento": "numerica_centimetros",
        "factor_ajuste": 0,
        "rangos_estatura": [
            (0, 164, "49 cm", {"49", "xs"}),
            (165, 172, "52 cm", {"52", "s"}),
            (173, 179, "54 cm", {"54", "m"}),
            (180, 185, "56 cm", {"56", "ml", "l"}),
            (186, 191, "58 cm", {"58", "xl"}),
            (192, 999, "61 cm", {"61", "2xl"})
        ],
        "descartes_estrictos_169": {"54", "56", "58", "m", "l"},
        "razon": "Trek Checkpoint usa tallaje numérico por centímetros. Para 1,69m la talla es estrictamente 52 cm."
    },
    "orbea": {
        "comportamiento": "estandar_alargado",
        "factor_ajuste": 0,
        "rangos_estatura": [
            (0, 166, "XS", {"xs", "48"}),
            (167, 172, "S (51 cm)", {"s", "51", "small"}),
            (173, 179, "M (54 cm)", {"m", "54", "medium"}),
            (180, 185, "L (57 cm)", {"l", "57", "large"}),
            (186, 999, "XL", {"xl", "60"})
        ],
        "descartes_estrictos_169": {"m", "54", "l", "57"},
        "razon": "Orbea Terra: rango oficial para S es 167 a 172 cm (centro biométrico exacto a 1,69m). La M empieza en 173 cm."
    },
    "conor": {
        "comportamiento": "doble_letra_conor",
        "factor_ajuste": 0,
        "rangos_estatura": [
            (0, 165, "XS (48)", {"48", "xs"}),
            (166, 173, "SM (51 cm)", {"sm", "51", "s"}),
            (174, 180, "MD (54 cm)", {"md", "54", "m"}),
            (181, 999, "LA (57 cm)", {"la", "57", "l"})
        ],
        "descartes_estrictos_169": {"md", "la", "54", "57", "m", "l"},
        "razon": "Conor Kalima etiqueta como SM (51 cm). Esquivar radicalmente la MD (54)."
    },
    "megamo": {
        "comportamiento": "estandar_compacto",
        "factor_ajuste": 0,
        "rangos_estatura": [
            (0, 165, "XS", {"xs", "48"}),
            (166, 173, "S (52 cm)", {"s", "52", "small"}),
            (174, 180, "M (54 cm)", {"m", "54", "medium"}),
            (181, 188, "L (56 cm)", {"l", "56", "large"}),
            (189, 999, "XL", {"xl", "58"})
        ],
        "descartes_estrictos_169": {"m", "l", "54", "56"},
        "razon": "Megamo Jakar y West: Talla S (52) óptima para 166-173 cm."
    },
    "specialized": {
        "comportamiento": "numerica_centimetros",
        "factor_ajuste": 0,
        "rangos_estatura": [
            (0, 163, "49 cm", {"49", "xs"}),
            (164, 172, "52 cm", {"52", "s"}),
            (173, 178, "54 cm", {"54", "m"}),
            (179, 185, "56 cm", {"56", "l"}),
            (186, 999, "58 cm", {"58", "xl"})
        ],
        "descartes_estrictos_169": {"54", "56", "58", "m", "l"},
        "razon": "Specialized Diverge: Talla 52 cm exacta para 1,69 m."
    },
    "cannondale": {
        "comportamiento": "stack_alto",
        "factor_ajuste": 0,
        "rangos_estatura": [
            (0, 164, "XS", {"xs", "48"}),
            (165, 173, "SM (51 cm)", {"sm", "s", "51"}),
            (174, 180, "MD (54 cm)", {"md", "m", "54"}),
            (181, 188, "LG (57 cm)", {"lg", "l", "57"}),
            (189, 999, "XL", {"xl"})
        ],
        "descartes_estrictos_169": {"md", "lg", "m", "l", "54"},
        "razon": "Cannondale Topstone tiene tubo de dirección elevado; la SM es la adecuada para 1,69 m."
    },
    "merida": {
        "comportamiento": "mtb_reach_alargado",
        "factor_ajuste": -1,
        "rangos_estatura": [
            (0, 165, "XS", {"xs", "48"}),
            (166, 173, "XS / S", {"xs", "s", "50"}),
            (174, 181, "M", {"m", "53"}),
            (182, 999, "L", {"l", "56"})
        ],
        "descartes_estrictos_169": {"m", "l", "53", "56"},
        "razon": "Merida Silex tiene geometría muy lanzada inspirada en bicis de montaña; la M es enorme a 1,69m."
    },
    "cube": {
        "comportamiento": "estandar_aleman",
        "factor_ajuste": 0,
        "rangos_estatura": [
            (0, 165, "XS (50)", {"xs", "50"}),
            (166, 173, "S (53)", {"s", "53"}),
            (174, 180, "M (56)", {"m", "56"}),
            (181, 187, "L (58)", {"l", "58"}),
            (188, 999, "XL", {"xl", "61"})
        ],
        "descartes_estrictos_169": {"m", "56", "l", "58"},
        "razon": "Cube Nuroad: Talla S (53) recomendada para 166-173 cm."
    },
    "ridley": {
        "comportamiento": "talla_grande_belga",
        "factor_ajuste": -1,
        "rangos_estatura": [
            (0, 166, "2XS", {"2xs", "xxs"}),
            (167, 173, "XS", {"xs", "48"}),
            (174, 180, "S", {"s", "51"}),
            (181, 187, "M", {"m", "54"}),
            (188, 999, "L", {"l", "57"})
        ],
        "descartes_estrictos_169": {"s", "m", "l"},
        "razon": "Ridley Kanzo talla muy grande (casi 1 talla completa por encima). A 1,69 m la XS es obligatoria."
    },
    "scott": {
        "comportamiento": "estandar_deportivo",
        "factor_ajuste": 0,
        "rangos_estatura": [
            (0, 165, "XS (49)", {"xs", "49"}),
            (166, 173, "S (52 cm)", {"s", "52"}),
            (174, 180, "M (54 cm)", {"m", "54"}),
            (181, 187, "L (56 cm)", {"l", "56"}),
            (188, 999, "XL (58 cm)", {"xl", "58"})
        ],
        "descartes_estrictos_169": {"m", "54", "l", "56"},
        "razon": "Scott Speedster y Addict Gravel: Talla S (52) ajusta de 166 a 173 cm."
    }
}

DEFAULT_GEOMETRY = {
    "comportamiento": "estandar",
    "factor_ajuste": 0,
    "rangos_estatura": [
        (0, 165, "XS", {"xs", "48", "49"}),
        (166, 173, "S (51-52 cm)", {"s", "51", "52", "sm"}),
        (174, 180, "M (54 cm)", {"m", "54", "md"}),
        (181, 187, "L (56 cm)", {"l", "56", "la"}),
        (188, 999, "XL", {"xl", "58"})
    ],
    "descartes_estrictos_169": {"m", "l", "xl", "54", "56", "58"},
    "razon": "Tallaje estándar del mercado ciclista."
}

def get_brand_geometry_rule(marca: str) -> Dict[str, Any]:
    """Recupera la regla de geometría específica para una marca."""
    m_clean = marca.lower().strip()
    for brand_key, rule in BRAND_GEOMETRY_RULES.items():
        if brand_key in m_clean:
            return rule
    return DEFAULT_GEOMETRY

def get_recommended_size_dynamic(marca: str, modelo: str, altura_cm: int = 169) -> Dict[str, Any]:
    """
    Calcula de manera dinámica y específica la talla obligatoria para una marca y modelo,
    con tokens admisibles y tokens que deben ser descartados inmediatamente.
    """
    rule = get_brand_geometry_rule(marca)
    talla_nom = "S"
    admisibles = set()

    for r_min, r_max, nom, tokens in rule["rangos_estatura"]:
        if r_min <= altura_cm <= r_max:
            talla_nom = nom
            admisibles = set(tokens)
            break

    # Obtener descartes específicos para la altura
    descartes = set(rule.get("descartes_estrictos_169", set()))
    # Si la altura es distinta a 169, los descartes son las otras tallas
    if altura_cm != 169:
        descartes = set()
        for r_min, r_max, nom, tokens in rule["rangos_estatura"]:
            if not (r_min <= altura_cm <= r_max):
                descartes.update(tokens)

    return {
        "marca": marca,
        "modelo": modelo,
        "altura_cm": altura_cm,
        "talla_recomendada": talla_nom,
        "tokens_admisibles": admisibles,
        "tokens_rechazados": descartes,
        "razon": rule.get("razon", ""),
        "comportamiento": rule.get("comportamiento", "estandar")
    }

def extract_size_tokens(sizes_raw: Any) -> Set[str]:
    """
    Descompone strings o listas de tallas en tokens atómicos normalizados.
    Ej: "S, M (52 cm)", ["Talla 54", "SM"] -> {"s", "m", "52", "54", "sm"}
    """
    if not sizes_raw:
        return set()
    if isinstance(sizes_raw, str):
        sizes_list = [sizes_raw]
    else:
        sizes_list = list(sizes_raw)

    tokens = set()
    for s in sizes_list:
        if not s:
            continue
        clean = str(s).lower()
        parts = re.split(r'[,/|\s\(\)\-]+', clean)
        for p in parts:
            p = p.strip()
            if p in ["talla", "tallas", "cm", "size", "sizes", "cuadro", "frame", "verde", "negro", "azul", "rojo", "blanco", "gris"]:
                continue
            if p:
                tokens.add(p)
    return tokens

def evaluate_size_compatibility_dynamic(marca: str, modelo: str, altura_cm: int, sizes_encontradas: Any) -> Tuple[bool, str, str]:
    """
    Evalúa automáticamente si las tallas extraídas de un anuncio son compatibles
    con la fisionomía del usuario para ESA marca y ESE modelo concreto.
    Retorna: (es_compatible, talla_recomendada, explicacion)
    """
    rec = get_recommended_size_dynamic(marca, modelo, altura_cm)
    talla_sugerida = rec["talla_recomendada"]
    razon = rec["razon"]

    clean_found = extract_size_tokens(sizes_encontradas)
    if not clean_found:
        # Si no hay lista explícita de tallas, se asume compatible pero con advertencia
        return True, talla_sugerida, f"Talla sugerida: {talla_sugerida}. ({razon})"

    # 1. Comprobar si contiene algún token explícitamente admisible
    has_admissible = bool(clean_found.intersection(rec["tokens_admisibles"]))
    has_rejected_only = bool(clean_found.intersection(rec["tokens_rechazados"])) and not has_admissible

    if has_rejected_only:
        return False, "No compatible", f"RECHAZADA: El anuncio solo ofrece talla incompatible ({', '.join(sorted(clean_found))}). {razon}"

    if has_admissible:
        return True, talla_sugerida, f"COMPATIBLE: Coincide con talla recomendada {talla_sugerida}. {razon}"

    # Si hay variantes pero ninguna coincide claramente
    return False, "Dudosa / No compatible", f"Talla no verificada para {marca} a {altura_cm}cm. Recomendada: {talla_sugerida}."
