"""
gravel_bot.evaluator - Extracción Heurística de Componentes y Motor de Valoración Ponderada
Base: Madrid 50/50 | 1,69 m (Talla S) | Presupuesto flexible ~1.000 € - 1.350 €
"""

import re
from typing import Dict, Any, Tuple, List, Optional
from gravel_bot.config import RIDER_PROFILE
from gravel_bot.geometry_sizing import evaluate_size_compatibility_dynamic, get_recommended_size_dynamic
from gravel_bot.knowledge_base import KnowledgeBase
from gravel_bot.biomechanics import evaluate_drivetrain_biomechanics, classify_geometry_aggressiveness
from gravel_bot.components_authority import sanitize_bike_specs
from gravel_bot.db import get_connection, update_bike_rescore, update_bike_specs
KNOWN_BRANDS = [
    "Megamo", "Orbea", "Conor", "Canyon", "Scott", "Trek", "Merida",
    "Kross", "MMR", "Van Rysel", "Triban", "Cannondale", "Ghost", "Focus",
    "KTM", "R-Raymon", "Raymon", "Cube", "BH", "Stevens", "Wilier",
    "Mondraker", "Polygon", "Marin", "Specialized", "Giant", "Kona", "Vitus",
    "Bianchi", "Radon", "Rose", "Mendiz", "Ridley", "Colnago", "Lapierre",
    "Berria", "Fuji", "Salsa", "Cervélo", "Sunn", "Bombtrack", "NS Bikes", "Wolfbike", "Corredor",
    # Ampliación por anuncios reales observados en DB (antes "Desconocida")
    "Whyte", "Centurion", "Bergamont", "Sunpeed", "Liv", "CBK", "Razesa", "Rizzo",
]
_BRAND_CANONICAL = {b.lower(): b for b in KNOWN_BRANDS}

# \b evita falsos positivos de subcadena (ej. "liv" dentro de "delivery")
BRAND_RE = re.compile(r"\b(?:" + "|".join(re.escape(b) for b in KNOWN_BRANDS) + r")\b", re.IGNORECASE)

def _transmision_desc(bike: Dict[str, Any]) -> str:
    """Devuelve la descripción de transmisión sin duplicar el tipo (2x12/1x11), también en filas legacy."""
    trans = str(bike.get("transmision", "") or "")
    tipo = str(bike.get("tipo_transmision", "") or "")
    if not tipo:
        return trans
    base = re.sub(rf"\s*\({re.escape(tipo)}\)\s*$", "", trans)
    if tipo in base:
        return base
    return f"{base} ({tipo})".strip()

def detect_bike_specs(title: str, description: str = "", price: float = 0.0, sizes: List[str] = None) -> Dict[str, Any]:
    """
    Analiza el texto de un anuncio/producto para extraer sus características técnicas,
    compatibilidad con 1,69 m y calcular automáticamente la puntuación de rúbrica.
    """
    full_text = f"{title} {description}".lower()
    sizes = sizes or []
    sizes_clean = [s.strip().lower() for s in sizes]

    # 1. Marca (match por palabra completa; mapea a la forma canónica)
    marca = "Desconocida"
    m_brand = BRAND_RE.search(full_text)
    if m_brand:
        marca = _BRAND_CANONICAL.get(m_brand.group(0).lower(), "Desconocida")

    # 2. Disciplina
    disciplina = "gravel"
    if any(w in full_text for w in [" tv ", "televisor", "samsung oled", "ruedas ", "juego de ruedas", "par de ruedas", "rodillo", "maillot", "culotte", "zapatillas"]):
        disciplina = "no_bicicleta"
    elif marca.lower() in ["testbrand", "test"] or title.lower().startswith("test "):
        disciplina = "test_artifact"
    elif "ebike" in full_text or "eléctrica" in full_text or "e-bike" in full_text:
        disciplina = "ebike_gravel"
    elif "junior" in full_text or "niño" in full_text:
        disciplina = "junior"
    elif "ciclocross" in full_text and "gravel" not in full_text:
        disciplina = "ciclocross"
    elif "carretera" in full_text and "gravel" not in full_text:
        disciplina = "carretera"
    elif "mtb" in full_text or "mountain" in full_text:
        disciplina = "mtb"
    # 3. Transmisión y Biomecánica (Knowledge Base Dinámica)
    kb = KnowledgeBase.get_instance()
    matched_dt = kb.match_drivetrain(full_text)

    if matched_dt:
        tipo_transmision = matched_dt.get("tipo", "2x10")
        modelo_dt = str(matched_dt.get("modelo") or "")
        if tipo_transmision and tipo_transmision not in modelo_dt:
            transmision_desc = f"{matched_dt.get('marca')} {modelo_dt} ({tipo_transmision})"
        else:
            transmision_desc = f"{matched_dt.get('marca')} {modelo_dt}".strip()
        bio_info = evaluate_drivetrain_biomechanics(matched_dt.get("platos", []), matched_dt.get("cassette", []))
    else:
        tipo_transmision = "2x10"
        transmision_desc = "Transmisión estándar 2x10"
        bio_info = evaluate_drivetrain_biomechanics([46, 30], [11, 36])
    # 4. Frenos (Knowledge Base Dinámica)
    matched_br = kb.match_brakes(full_text)
    tipo_frenos = matched_br.get("tipo", "hidraulico")
    if tipo_frenos == "hidraulico":
        frenos_desc = "Frenos de disco hidráulicos"
    elif tipo_frenos == "semihidraulico":
        frenos_desc = "Frenos semihidráulicos (TRP HY/RD)"
    elif tipo_frenos == "mecanico_doble":
        frenos_desc = "Frenos mecánicos de doble pistón"
    else:
        frenos_desc = "Frenos mecánicos por cable"
    # 5. Cuadro y Horquilla
    model_spec = kb.find_known_model_spec(full_text)
    es_carbono = "carbon" in full_text or "carbono" in full_text
    if model_spec and "cuadro" in model_spec and not es_carbono:
        cuadro = model_spec["cuadro"]
    else:
        cuadro = "Carbono Toray High Modulus" if es_carbono else "Aluminio 6061 Hidroformado"

    if model_spec and "horquilla" in model_spec:
        horquilla = model_spec["horquilla"]
    else:
        horquilla = "Carbono con paso de rueda amplio"

    if "horquilla aluminio" in full_text or "fork alu" in full_text:
        horquilla = "Aluminio rígido"
    # 6. Patilla UDH y Paso de Rueda
    patilla_udh = 1 if ("udh" in full_text or "sram udh" in full_text or "universal derailleur" in full_text) else (model_spec.get("udh", 0) if model_spec else 0)
    paso_rueda_apto = True
    if any(re.search(pat, full_text) for pat in [
        r'\bmax(?:imo)?\s*(?:3[0-5]|2[0-9])\s*mm\b',
        r'\bpaso(?:\s+de\s+rueda)?\s*(?:3[0-5]|2[0-9])\s*mm\b',
        r'\buci\s*33\b',
        r'\bcx\s*race\b'
    ]):
        paso_rueda_apto = False

    # 7. Compatibilidad Dinámica de Talla según Marca y Modelo (no global)
    if disciplina != "gravel":
        talla_valida = False
        talla_sugerida = "Incompatible (No gravel)"
        explicacion_talla = f"Descartada por disciplina ({disciplina})."
    else:
        talla_valida, talla_sugerida, explicacion_talla = evaluate_size_compatibility_dynamic(
            marca=marca,
            modelo=title,
            altura_cm=169,
            sizes_encontradas=sizes_clean
        )
    c1, c2, c3, c4, c5, total, nota, tier = calcular_rubrica(
        disciplina=disciplina,
        tipo_frenos=tipo_frenos,
        tipo_transmision=tipo_transmision,
        cuadro=cuadro,
        horquilla=horquilla,
        patilla_udh=patilla_udh,
        precio=price,
        talla_valida=talla_valida,
        paso_rueda_apto=paso_rueda_apto
    )

    # 9. Veredicto sintético
    veredicto = f"Detectado {marca} con {transmision_desc} y {frenos_desc}. {explicacion_talla}"
    if not paso_rueda_apto:
        veredicto += " ⚠️ Paso de rueda limitado (<38mm); penalizada para pistas de tierra."
    # Generar Slug limpio e invariante al precio para acumular historial del mismo modelo
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_')[:50]
    raw_bike = {
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
        "tallas_disponibles": ", ".join(sizes) if sizes else "Consultar tienda",
        "precio_pvp": model_spec.get("pvp", price) if model_spec and (price == 0.0 or price >= model_spec.get("pvp", price) * 0.95) else price,
        "precio_oferta": price,
        "c1_frenos": c1,
        "c2_transmision": c2,
        "c3_cuadro": c3,
        "c4_precio": c4,
        "c5_talla": c5,
        "c6_garantia": 4.0,
        "puntuacion_total": total,
        "nota": nota,
        "tier": tier,
        "notas_veredicto": veredicto,
        "climbing_ratio": bio_info.get("climbing_ratio", 0.85),
        "highest_gear_inches": bio_info.get("highest_gear_inches", 115.0),
        "apto_tierra": bio_info.get("apto_tierra", True) and paso_rueda_apto,
        "paso_rueda_apto": paso_rueda_apto
    }
    # Sanitizar inmediatamente contra la matriz de autoridad para erradicar falsos hidráulicos
    sanitized = sanitize_bike_specs(raw_bike)
    # Si hubo corrección en los frenos o cuadro, recalcular rúbrica para ser 100% verídicos
    if sanitized["tipo_frenos"] != tipo_frenos or sanitized["cuadro"] != cuadro:
        c1_s, c2_s, c3_s, c4_s, c5_s, tot_s, not_s, tr_s = calcular_rubrica(
            disciplina=sanitized["disciplina"],
            tipo_frenos=sanitized["tipo_frenos"],
            tipo_transmision=sanitized["tipo_transmision"],
            cuadro=sanitized["cuadro"],
            horquilla=sanitized["horquilla"],
            patilla_udh=sanitized["patilla_udh"],
            precio=sanitized["precio_oferta"],
            talla_valida=talla_valida,
            paso_rueda_apto=paso_rueda_apto
        )
        sanitized["c1_frenos"] = c1_s
        sanitized["c2_transmision"] = c2_s
        sanitized["c3_cuadro"] = c3_s
        sanitized["c4_precio"] = c4_s
        sanitized["c5_talla"] = c5_s
        sanitized["puntuacion_total"] = tot_s
        sanitized["nota"] = not_s
        sanitized["tier"] = tr_s
    return sanitized

def calcular_rubrica(disciplina: str, tipo_frenos: str, tipo_transmision: str,
                     cuadro: str, horquilla: str, patilla_udh: int,
                     precio: float, talla_valida: bool,
                     paso_rueda_apto: bool = True) -> Tuple[float, float, float, float, float, float, float, str]:
    """
    Rúbrica matemática ponderada para ciclista de 1,69 m en Madrid (Méndez Álvaro).
    Fórmula: P = C1 (Frenos 25%) + C2 (Transmisión 25%) + C3 (Cuadro 20%) + C4 (Precio 20%) + C5 (Talla 10%)
    """
    # Si la disciplina no es gravel o tiene falla grave
    if disciplina.lower() != "gravel":
        c1 = 4.0
        c2 = 4.0
        c3 = 2.0
        c4 = 5.0
        c5 = 0.0
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

    # Penalización rígida si el paso de rueda es < 38mm (geometría CX pura o limitada)
    if not paso_rueda_apto:
        c3 = min(c3, 8.0)
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

def calcular_rubrica_calibrada(bike: Dict[str, Any], tienda_tipo: Optional[str] = None) -> Dict[str, Any]:
    """
    Rúbrica matemática calibrada y ponderada con factor de canal / garantía C6 (+5 pts).
    Criterios:
      C1 Frenos: 25 pts (Hidráulico: 25, Semihidráulico: 15, Mecánico doble: 10, Mecánico mono: 6)
      C2 Transmisión: 25 pts (2x11/2x12: 25, 2x10: 23, 1x12: 20, 1x11: 18, 1x10: 16, 2x8/2x9: 14, 1x9: 13, otros: 7)
      C3 Cuadro & Horquilla: 20 pts (Carbono completo: 20, Alu+Carbono+UDH: 20, Alu+Carbono: 17, Acero+Carbono: 15, Alu/Acero pelado: 6)
      C4 Precio VFM: 20 pts (<950€: 20, 951-1150€: 18-19, 1151-1300€: 16, 1301-1500€: 13, >1500€: decreciente)
      C5 Talla 1,69 m: 10 pts (Compatible: 10, No compatible: 2)
      C6 Canal & Garantía: +5 pts (Tienda física oficial: 5.0, Tienda online: 4.0, Ocasión certificada: 3.0, Particular: 0.0)
    """
    disciplina = str(bike.get("disciplina", "gravel")).lower()
    tipo_frenos = str(bike.get("tipo_frenos", "mecanico_mono")).lower()
    tipo_trans = str(bike.get("tipo_transmision", "2x10")).lower()
    cuadro = str(bike.get("cuadro", "")).lower()
    horquilla = str(bike.get("horquilla", "")).lower()
    patilla_udh = int(bike.get("patilla_udh") or 0)
    precio = float(bike.get("precio_oferta") or 0.0)
    talla_rec = str(bike.get("talla_recomendada_169", "")).lower()
    talla_valida = "no compatible" not in talla_rec and "incompatible" not in talla_rec
    paso_rueda_apto = bool(bike.get("paso_rueda_apto", True))

    if disciplina != "gravel":
        return {
            "c1_frenos": 4.0, "c2_transmision": 4.0, "c3_cuadro": 2.0,
            "c4_precio": 5.0, "c5_talla": 0.0, "c6_garantia": 0.0,
            "puntuacion_total": 15.0, "nota": 1.5, "tier": "Tier C",
            "veredicto": f"Descartada por disciplina no gravel ({disciplina})"
        }

    # C1. Frenos (25 pts)
    if "hidraulico" in tipo_frenos and "semi" not in tipo_frenos:
        c1 = 25.0
    elif "semihidraulico" in tipo_frenos or "semi" in tipo_frenos:
        c1 = 15.0
    elif "mecanico_doble" in tipo_frenos or "doble" in tipo_frenos:
        c1 = 10.0
    else:
        c1 = 6.0

    # C2. Transmisión (25 pts)
    if tipo_trans in ["2x11", "2x12"]:
        c2 = 25.0
    elif tipo_trans == "2x10":
        c2 = 23.0
    elif tipo_trans == "1x12":
        c2 = 20.0
    elif tipo_trans == "1x11":
        c2 = 18.0
    elif tipo_trans == "1x10":
        c2 = 16.0
    elif tipo_trans in ["2x8", "2x9"]:
        c2 = 14.0
    elif tipo_trans == "1x9":
        c2 = 13.0
    else:
        c2 = 7.0

    # C3. Cuadro & Horquilla (20 pts)
    es_carbono = "carbono" in cuadro or "carbon" in cuadro
    horq_carbono = "carbono" in horquilla or "carbon" in horquilla
    if es_carbono and horq_carbono:
        c3 = 20.0
    elif horq_carbono:
        c3 = 20.0 if patilla_udh else 17.0
        if "acero" in cuadro or "cromoly" in cuadro:
            c3 = 15.0
    else:
        c3 = 6.0
    if not paso_rueda_apto:
        c3 = min(c3, 8.0)

    # C4. Precio VFM (20 pts)
    if precio <= 950.0:
        c4 = 20.0 if c1 >= 20.0 else 18.0
    elif 951.0 <= precio <= 1150.0:
        c4 = 19.0 if c1 >= 20.0 else 17.0
    elif 1151.0 <= precio <= 1300.0:
        c4 = 16.0
    elif 1301.0 <= precio <= 1500.0:
        c4 = 13.0
    else:
        c4 = max(6.0, round(12.0 - (precio - 1500.0) / 250.0, 1))

    # C5. Talla (10 pts)
    c5 = 10.0 if talla_valida else 2.0

    # C6. Factor Garantía / Canal de Compra (+5 pts)
    st_type = str(tienda_tipo or bike.get("tienda_tipo") or "online").lower()
    if st_type in ["fisica", "tienda_fisica", "local_madrid"]:
        c6 = 5.0
    elif st_type in ["online", "tienda_online"]:
        c6 = 4.0
    elif st_type in ["ocasion_certificada", "reacondicionada"]:
        c6 = 3.0
    elif st_type in ["particular", "wallapop"]:
        c6 = 0.0
    else:
        c6 = 3.5

    total = min(c1 + c2 + c3 + c4 + c5 + c6, 100.0)
    nota = round(total / 10.0, 1)

    if total >= 90.0:
        tier = "Tier S+"
    elif total >= 80.0:
        tier = "Tier S"
    elif total >= 68.0:
        tier = "Tier A"
    elif total >= 52.0:
        tier = "Tier B"
    else:
        tier = "Tier C"

    veredicto = f"Puntuación calibrada C1..C6: Frenos ({c1:.0f}), Transmisión ({c2:.0f}), Cuadro ({c3:.0f}), Precio ({c4:.0f}), Talla ({c5:.0f}), Garantía ({c6:.0f})."

    return {
        "c1_frenos": c1,
        "c2_transmision": c2,
        "c3_cuadro": c3,
        "c4_precio": c4,
        "c5_talla": c5,
        "c6_garantia": c6,
        "puntuacion_total": total,
        "nota": nota,
        "tier": tier,
        "veredicto": veredicto,
    }

def get_itemized_score_card(bike: Dict[str, Any]) -> Dict[str, Any]:
    """Genera la ficha desglosada por cada criterio C1..C6 para inspección detallada y UI."""
    cal = calcular_rubrica_calibrada(bike, tienda_tipo=bike.get("tienda_tipo"))
    return {
        "bike_id": bike.get("id"),
        "marca": bike.get("marca"),
        "modelo": bike.get("modelo"),
        "precio": bike.get("precio_oferta"),
        "tienda_nombre": bike.get("tienda_nombre", "Online"),
        "tienda_tipo": bike.get("tienda_tipo", "online"),
        "c1": {"pts": cal["c1_frenos"], "max": 25, "label": "Frenos", "desc": str(bike.get("tipo_frenos", "")).replace("_", " ").capitalize()},
        "c2": {"pts": cal["c2_transmision"], "max": 25, "label": "Transmisión", "desc": _transmision_desc(bike)},
        "c3": {"pts": cal["c3_cuadro"], "max": 20, "label": "Cuadro & Horquilla", "desc": f"{bike.get('cuadro', '')} / {bike.get('horquilla', '')}"},
        "c4": {"pts": cal["c4_precio"], "max": 20, "label": "Relación Precio VFM", "desc": f"{bike.get('precio_oferta', 0):.0f} €"},
        "c5": {"pts": cal["c5_talla"], "max": 10, "label": "Talla 1,69 m", "desc": str(bike.get("talla_recomendada_169", "S"))},
        "c6": {"pts": cal["c6_garantia"], "max": 5, "label": "Garantía & Canal", "desc": f"Canal {bike.get('tienda_tipo', 'online').capitalize()}"},
        "total": cal["puntuacion_total"],
        "nota": cal["nota"],
        "tier": cal["tier"],
        "veredicto": cal["veredicto"],
        "especificaciones_verificadas": bike.get("especificaciones_verificadas", 0)
    }

def run_catalog_rescore(dry_run: bool = False) -> Dict[str, Any]:
    """
    Recalcula la puntuación de todas las bicicletas del catálogo con la rúbrica calibrada C1..C6,
    incorporando el factor garantía/canal de compra y actualizando en SQLite.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT b.*, t.nombre as tienda_nombre, t.tipo as tienda_tipo
        FROM bicicletas b
        LEFT JOIN tiendas t ON b.tienda_id = t.id
    """)
    rows = c.fetchall()
    conn.close()

    tier_counts = {"Tier S+": 0, "Tier S": 0, "Tier A": 0, "Tier B": 0, "Tier C": 0}
    rescore_list = []

    for r in rows:
        b_dict = dict(r)
        # Sanitizar especificaciones con matriz de autoridad
        sanitized = sanitize_bike_specs(b_dict)
        # Calcular rúbrica calibrada C1..C6
        t_tipo = str(b_dict.get("tienda_tipo") or "online")
        cal = calcular_rubrica_calibrada(sanitized, tienda_tipo=t_tipo)

        t_name = cal["tier"]
        tier_counts[t_name] = tier_counts.get(t_name, 0) + 1

        diff_nota = round(cal["nota"] - float(b_dict.get("nota") or 0.0), 1)
        rescore_list.append({
            "id": b_dict["id"],
            "modelo": f"{b_dict.get('marca')} {b_dict.get('modelo')}",
            "old_tier": b_dict.get("tier"),
            "new_tier": cal["tier"],
            "old_nota": b_dict.get("nota"),
            "new_nota": cal["nota"],
            "diff_nota": diff_nota,
            "total": cal["puntuacion_total"],
            "c1": cal["c1_frenos"],
            "c2": cal["c2_transmision"],
            "c3": cal["c3_cuadro"],
            "c4": cal["c4_precio"],
            "c5": cal["c5_talla"],
            "c6": cal["c6_garantia"]
        })

        if not dry_run:
            update_bike_rescore(
                bike_id=b_dict["id"],
                c1=cal["c1_frenos"],
                c2=cal["c2_transmision"],
                c3=cal["c3_cuadro"],
                c4=cal["c4_precio"],
                c5=cal["c5_talla"],
                c6=cal["c6_garantia"],
                puntuacion_total=cal["puntuacion_total"],
                nota=cal["nota"],
                tier=cal["tier"],
                notas_veredicto=cal["veredicto"]
            )
            # Si las especificaciones fueron saneadas, actualizarlas en DB
            if (sanitized["tipo_frenos"] != b_dict["tipo_frenos"] or
                sanitized["cuadro"] != b_dict["cuadro"] or
                sanitized.get("precio_pvp") != b_dict.get("precio_pvp")):
                update_bike_specs(
                    bike_id=b_dict["id"],
                    transmision=sanitized["transmision"],
                    tipo_transmision=sanitized["tipo_transmision"],
                    frenos=sanitized["frenos"],
                    tipo_frenos=sanitized["tipo_frenos"],
                    cuadro=sanitized["cuadro"],
                    horquilla=sanitized["horquilla"],
                    precio_pvp=sanitized.get("precio_pvp")
                )

    return {
        "total_bikes": len(rows),
        "dry_run": dry_run,
        "tier_counts": tier_counts,
        "cambios": rescore_list
    }

# -----------------------------------------------------------------------------
# Extensiones Multiusuario y Personalización Dinámica
# -----------------------------------------------------------------------------

def calcular_talla_desde_estatura(altura_cm: int, marca: str = "") -> str:
    """
    Calcula la talla de cuadro recomendada según la estatura en cm,
    teniendo en cuenta las peculiaridades de marcas que tallan grande (Canyon, Focus).
    """
    marca_l = marca.lower()
    talla_grande = marca_l in ["canyon", "focus"]

    if altura_cm < 165:
        return "2XS" if talla_grande else "XS"
    elif 165 <= altura_cm <= 173:
        return "XS" if talla_grande else "S"
    elif 174 <= altura_cm <= 181:
        return "S" if talla_grande else "M"
    elif 182 <= altura_cm <= 189:
        return "M" if talla_grande else "L"
    else:
        return "L" if talla_grande else "XL"

def calcular_rubrica_personalizada(bike: Dict[str, Any], perfil: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recalcula la puntuación de rúbrica y el Tier de una bicicleta
    adaptándola específicamente al perfil del ciclista (presupuesto, uso %, estatura/talla).
    """
    disciplina = bike.get("disciplina", "gravel")
    tipo_frenos = bike.get("tipo_frenos", "hidraulico")
    tipo_trans = bike.get("tipo_transmision", "2x10")
    cuadro = bike.get("cuadro", "")
    horquilla = bike.get("horquilla", "")
    patilla_udh = bike.get("patilla_udh", 0)
    precio = float(bike.get("precio_oferta", 0.0))
    marca = bike.get("marca", "")

    if disciplina.lower() != "gravel":
        result = dict(bike)
        result["c1_frenos"] = 4.0
        result["c2_transmision"] = 4.0
        result["c3_cuadro"] = 2.0
        result["c4_precio"] = 5.0
        result["c5_talla"] = 0.0
        result["puntuacion_total"] = 15.0
        result["nota"] = 1.5
        result["tier"] = "Tier C"
        result["talla_recomendada_169"] = "No compatible"
        result["notas_veredicto"] = f"Descartada: Disciplina {disciplina} no apta para gravel 50/50."
        return result

    # 1. C1: Frenos (25 pts)
    if tipo_frenos == "hidraulico":
        c1 = 25.0
    elif tipo_frenos == "semihidraulico":
        c1 = 15.0
    elif tipo_frenos == "mecanico_doble":
        c1 = 10.0
    else:
        c1 = 8.0

    # 2. C2: Transmisión adaptada al perfil (25 pts)
    asfalto_pct = perfil.get("terreno_asfalto_pct", 50)
    pref_trans = perfil.get("preferencia_transmision", "2x")

    if asfalto_pct >= 50 or pref_trans == "2x":
        if tipo_trans in ["2x10", "2x11", "2x12"]:
            c2 = 25.0
        elif tipo_trans in ["1x11", "1x12"]:
            c2 = 18.0
        elif tipo_trans == "1x10":
            c2 = 17.0
        else:
            c2 = 10.0
    else:
        if tipo_trans in ["1x11", "1x12"]:
            c2 = 25.0
        elif tipo_trans == "1x10":
            c2 = 22.0
        elif tipo_trans in ["2x10", "2x11", "2x12"]:
            c2 = 20.0
        else:
            c2 = 12.0

    # 3. C3: Cuadro y Horquilla (20 pts)
    es_carb = "carbono" in cuadro.lower()
    horq_carb = "carbono" in horquilla.lower()
    if es_carb and horq_carb:
        c3 = 20.0
    elif horq_carb:
        c3 = 20.0 if patilla_udh else 17.0
    else:
        c3 = 8.0

    if bike.get("paso_rueda_apto") is False:
        c3 = min(c3, 8.0)
    # 4. C4: Precio adaptado al presupuesto con holgura por buena oferta (20 pts)
    presupuesto = float(perfil.get("presupuesto_max", 1000.0))
    holgura_pct = float(perfil.get("holgura_max_pct", 15.0))
    limite_holgura = presupuesto * (1.0 + holgura_pct / 100.0)

    pvp = float(bike.get("precio_pvp", precio))
    descuento_pct = ((pvp - precio) / pvp * 100.0) if pvp > precio else 0.0

    # Es un chollazo justificado si tiene buen descuento, frenos hidráulicos o grupo GRX
    es_gran_oferta = (
        descuento_pct >= 18.0 or
        bike.get("tipo_frenos") == "hidraulico" or
        "carbono" in str(bike.get("cuadro", "")).lower() or
        "grx" in str(bike.get("transmision", "")).lower()
    )

    holgura_aplicada = False
    if precio <= (presupuesto * 0.9):
        c4 = 20.0
    elif precio <= presupuesto:
        c4 = 18.0
    elif precio <= limite_holgura:
        if es_gran_oferta:
            c4 = 16.0
            holgura_aplicada = True
        else:
            c4 = 11.0
    elif precio <= (presupuesto * 1.35):
        c4 = 7.0
    else:
        c4 = 2.0
    # 5. C5: Talla y Ergonomía Dinámica por Marca y Modelo (10 pts)
    estatura = perfil.get("estatura_cm", 169)
    modelo = bike.get("modelo", "")
    rec = get_recommended_size_dynamic(marca, modelo, estatura)
    talla_bici_txt = str(bike.get("talla_recomendada_169", "")).lower()
    
    # Comprobar coincidencia con tokens admisibles de la marca
    talla_valida = any(token in talla_bici_txt for token in rec["tokens_admisibles"])
    if not talla_valida and (rec["talla_recomendada"].lower() in talla_bici_txt):
        talla_valida = True

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

    result = dict(bike)
    result["c1_frenos"] = c1
    result["c2_transmision"] = c2
    result["c3_cuadro"] = c3
    result["c4_precio"] = c4
    result["c5_talla"] = c5
    result["puntuacion_total"] = total
    result["nota"] = nota
    result["tier"] = tier
    result["talla_valida"] = talla_valida
    result["holgura_aplicada"] = holgura_aplicada
    return result
