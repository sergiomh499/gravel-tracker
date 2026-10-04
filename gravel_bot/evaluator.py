"""
gravel_bot.evaluator - Extracción Heurística de Componentes y Motor de Valoración Ponderada
Base: Madrid 50/50 | 1,69 m (Talla S) | Presupuesto flexible ~1.000 € - 1.350 €
"""

import re
from typing import Dict, Any, Tuple, List
from gravel_bot.config import RIDER_PROFILE

KNOWN_BRANDS = [
    "Megamo", "Orbea", "Conor", "Canyon", "Scott", "Trek", "Merida",
    "Kross", "MMR", "Van Rysel", "Triban", "Cannondale", "Ghost", "Focus",
    "KTM", "R-Raymon", "Raymon", "Cube", "BH", "Stevens", "Wilier",
    "Mondraker", "Polygon", "Marin", "Specialized", "Giant", "Kona", "Vitus"
]

def detect_bike_specs(title: str, description: str = "", price: float = 0.0, sizes: List[str] = None) -> Dict[str, Any]:
    """
    Analiza el texto de un anuncio/producto para extraer sus características técnicas,
    compatibilidad con 1,69 m y calcular automáticamente la puntuación de rúbrica.
    """
    full_text = f"{title} {description}".lower()
    sizes = sizes or []
    sizes_clean = [s.strip().lower() for s in sizes]

    # 1. Marca
    marca = "Desconocida"
    for b in KNOWN_BRANDS:
        if b.lower() in full_text:
            marca = b
            break

    # 2. Disciplina
    disciplina = "gravel"
    if "ebike" in full_text or "eléctrica" in full_text or "e-bike" in full_text:
        disciplina = "ebike_gravel"
    elif "junior" in full_text or "niño" in full_text:
        disciplina = "junior"
    elif "carretera" in full_text and "gravel" not in full_text:
        disciplina = "carretera"
    elif "mtb" in full_text or "mountain" in full_text:
        disciplina = "mtb"

    # 3. Transmisión
    tipo_transmision = "2x10" # Default conservador para gravel
    transmision_desc = "Transmisión estándar"

    if re.search(r'2x12|rx820.*2x|grx.*12[vs]', full_text):
        tipo_transmision = "2x12"
        transmision_desc = "Shimano GRX 2x12 velocidades"
    elif re.search(r'2x11|rx810.*2x|rx600.*2x|grx.*11[vs]', full_text):
        tipo_transmision = "2x11"
        transmision_desc = "Shimano GRX 2x11 velocidades"
    elif re.search(r'2x10|rx400.*2x|tiagra.*2x|grx.*10[vs]', full_text):
        tipo_transmision = "2x10"
        transmision_desc = "Shimano GRX RX400 2x10 velocidades"
    elif re.search(r'1x12|apex.*12|rival.*12|sram.*12[vs]', full_text):
        tipo_transmision = "1x12"
        transmision_desc = "SRAM Apex / Rival 1x12 velocidades"
    elif re.search(r'1x11|apex.*11|grx.*1x11|rival.*11', full_text):
        tipo_transmision = "1x11"
        transmision_desc = "SRAM Apex 1x11 o Shimano GRX 1x11"
    elif re.search(r'cues.*10|1x10|cues.*u6000', full_text):
        tipo_transmision = "1x10"
        transmision_desc = "Shimano CUES 1x10 velocidades"
    elif re.search(r'claris|sora|2x8|2x9', full_text):
        tipo_transmision = "2x8"
        transmision_desc = "Shimano Claris/Sora (Iniciación carretera)"
    elif re.search(r'microshift|acolyte|sword', full_text):
        tipo_transmision = "1x10" if "10" in full_text else "1x9"
        transmision_desc = "Microshift Advent / Sword"

    # 4. Frenos
    tipo_frenos = "hidraulico"
    frenos_desc = "Frenos de disco hidráulicos"

    if re.search(r'hidr[aá]ulic|grx\s*rx[468]|br-rx|apex\s*hydr|cues\s*u6000', full_text):
        tipo_frenos = "hidraulico"
        frenos_desc = "Disco Hidráulico (Shimano GRX / CUES / SRAM)"
    elif re.search(r'semi.*hidr[aá]ulic|hy/rd|cable.*hidr', full_text):
        tipo_frenos = "semihidraulico"
        frenos_desc = "Disco Semihidráulico (TRP HY/RD)"
    elif re.search(r'mec[aá]nic|cable|spyre|bb7|claris.*disc|sora.*disc', full_text):
        tipo_frenos = "mecanico_doble"
        frenos_desc = "Disco Mecánico por cable"
    elif "grx" in full_text or "apex" in full_text:
        # Por omisión en gama GRX/Apex suele ser hidráulico
        tipo_frenos = "hidraulico"
        frenos_desc = "Disco Hidráulico"

    # 5. Cuadro y Horquilla
    es_carbono = "carbon" in full_text or "carbono" in full_text
    cuadro = "Carbono Toray High Modulus" if es_carbono else "Aluminio 6061 Hidroformado"
    horquilla = "Carbono con paso de rueda amplio"

    if "horquilla aluminio" in full_text or "fork alu" in full_text:
        horquilla = "Aluminio rígido"

    # 6. Patilla UDH
    patilla_udh = 1 if ("udh" in full_text or "sram udh" in full_text or "universal derailleur" in full_text) else 0

    # 7. Compatibilidad de Talla con 1,69 m
    talla_valida = False
    marca_lower = marca.lower()
    talla_sugerida = "S (51 cm)"

    # Marcas que tallan grande: Canyon, Focus
    if marca_lower in ["canyon", "focus"]:
        talla_sugerida = "XS (48 cm)"
        # Compatible solo si tiene XS o 48
        if any(t in ["xs", "48", "xxs"] for t in sizes_clean):
            talla_valida = True
        elif not sizes:
            # Si no hay tallas especificadas pero el anuncio no fuerza M/L
            talla_valida = True
    else:
        # Marcas estándar (Orbea, Megamo, Conor, MMR, Scott, Trek)
        if any(t in ["s", "sm", "50", "51", "52", "49"] for t in sizes_clean):
            talla_valida = True
        elif not sizes and not any(t in ["m", "l", "xl", "54", "56"] for t in full_text.split()):
            talla_valida = True

    # 8. Cálculo de Rúbrica
    c1, c2, c3, c4, c5, total, nota, tier = calcular_rubrica(
        disciplina=disciplina,
        tipo_frenos=tipo_frenos,
        tipo_transmision=tipo_transmision,
        cuadro=cuadro,
        horquilla=horquilla,
        patilla_udh=patilla_udh,
        precio=price,
        talla_valida=talla_valida
    )

    # 9. Veredicto sintético
    veredicto = f"Detectado {marca} con {transmision_desc} y {frenos_desc}. "
    if talla_valida:
        veredicto += f"Talla adecuada ({talla_sugerida}) para 1,69m."
    else:
        veredicto += "ALERTA: Talla no recomendada para 1,69m."

    # Generar Slug limpio
    clean_title = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_')[:40]
    slug = f"{clean_title}_{int(price)}"

    return {
        "slug": slug,
        "marca": marca,
        "modelo": title[:50],
        "ano": 2025,
        "disciplina": disciplina,
        "transmision": transmision_desc,
        "tipo_transmision": tipo_transmision,
        "frenos": frenos_desc,
        "tipo_frenos": tipo_frenos,
        "cuadro": cuadro,
        "horquilla": horquilla,
        "ejes": "Pasantes 12 mm",
        "patilla_udh": patilla_udh,
        "talla_recomendada_169": talla_sugerida if talla_valida else "No compatible",
        "precio_pvp": price, # por defecto si no hay otro
        "precio_oferta": price,
        "c1_frenos": c1,
        "c2_transmision": c2,
        "c3_cuadro": c3,
        "c4_precio": c4,
        "c5_talla": c5,
        "puntuacion_total": total,
        "nota": nota,
        "tier": tier,
        "notas_veredicto": veredicto
    }

def calcular_rubrica(disciplina: str, tipo_frenos: str, tipo_transmision: str,
                     cuadro: str, horquilla: str, patilla_udh: int,
                     precio: float, talla_valida: bool) -> Tuple[float, float, float, float, float, float, float, str]:
    """
    Rúbrica matemática ponderada para ciclista de 1,69 m en Madrid (Méndez Álvaro).
    Fórmula: P = C1 (Frenos 25%) + C2 (Transmisión 25%) + C3 (Cuadro 20%) + C4 (Precio 20%) + C5 (Talla 10%)
    """
    # Si la disciplina no es gravel o tiene falla grave
    if disciplina.lower() != "gravel":
        c1 = 8.0 if tipo_frenos != "hidraulico" else 20.0
        c2 = 10.0
        c3 = 2.0
        c4 = 10.0
        c5 = 2.0 if "flat" in disciplina.lower() else 10.0
        total = c1 + c2 + c3 + c4 + c5
        nota = round(total / 10.0, 1)
        return c1, c2, c3, c4, c5, total, nota, "Tier C"

    # C1. Frenos (25 pts)
    if tipo_frenos == "hidraulico":
        c1 = 25.0
    elif tipo_frenos == "semihidraulico":
        c1 = 15.0
    elif tipo_frenos == "mecanico_doble":
        c1 = 10.0
    else:
        c1 = 8.0

    # C2. Transmisión 50/50 (25 pts)
    if tipo_transmision in ["2x10", "2x11", "2x12"]:
        c2 = 25.0
    elif tipo_transmision in ["1x11", "1x12"]:
        c2 = 18.0
    elif tipo_transmision == "1x10":
        c2 = 17.0
    elif tipo_transmision == "1x9":
        c2 = 14.0
    else:
        c2 = 7.0

    # C3. Cuadro, Horquilla y Estándares (20 pts)
    es_carbono = "carbono" in cuadro.lower()
    horquilla_carbono = "carbono" in horquilla.lower()
    if es_carbono and horquilla_carbono:
        c3 = 20.0
    elif horquilla_carbono:
        c3 = 20.0 if patilla_udh else 17.0
        if "acero" in cuadro.lower() or "cromoly" in cuadro.lower():
            c3 = 15.0
    else:
        c3 = 6.0

    # C4. Precio y Logística (20 pts)
    if precio <= 1150:
        c4 = 20.0 if c1 >= 20 else 18.0
    elif 1151 <= precio <= 1300:
        c4 = 18.0 if (patilla_udh or es_carbono or c2 == 25) else 15.0
    elif 1301 <= precio <= 1450:
        c4 = 14.0
    else:
        c4 = 10.0

    # C5. Talla y Ergonomía (10 pts)
    c5 = 10.0 if talla_valida else 2.0

    total = c1 + c2 + c3 + c4 + c5
    nota = round(total / 10.0, 1)

    if total >= 90:
        tier = "Tier S+"
    elif total >= 80:
        tier = "Tier S"
    elif total >= 65:
        tier = "Tier A"
    elif total >= 50:
        tier = "Tier B"
    else:
        tier = "Tier C"

    return c1, c2, c3, c4, c5, total, nota, tier
