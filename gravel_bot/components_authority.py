"""
gravel_bot/components_authority.py
Matriz de Verdad Inmutable de Componentes Ciclistas y Sanitización Estricta.

Garantiza la verdad técnica del catálogo:
- Corrige falsos frenos hidráulicos en grupos puramente mecánicos (Claris, Tourney, Sora, etc.)
- Normaliza tipos de cuadro (aluminio vs carbono) según modelos canónicos
- Acota PVPs ficticios o inflados contra el MSRP oficial de la industria
"""

import re
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List
from gravel_bot.db import get_connection, update_bike_specs


@dataclass(frozen=True)
class AuthoritativeGroupSpec:
    canonical_name: str
    family: str
    speed_options: Tuple[int, ...]
    default_speeds: int
    actuation: str  # 'hidraulico', 'semihidraulico', 'mecanico'
    msrp_min: float
    msrp_max: float
    tier_componente: str
    disc_only: bool = True


# Diccionario inmutable de especificaciones y límites de la industria
AUTHORITATIVE_GROUPS: Dict[str, AuthoritativeGroupSpec] = {
    # Shimano Carretera / Gravel Entrada (100% mecánicos de fábrica)
    "shimano tourney": AuthoritativeGroupSpec(
        canonical_name="Shimano Tourney A070",
        family="shimano",
        speed_options=(7,),
        default_speeds=7,
        actuation="mecanico",
        msrp_min=350.0,
        msrp_max=650.0,
        tier_componente="Tier C-",
    ),
    "shimano claris": AuthoritativeGroupSpec(
        canonical_name="Shimano Claris R2000",
        family="shimano",
        speed_options=(8,),
        default_speeds=8,
        actuation="mecanico",
        msrp_min=500.0,
        msrp_max=950.0,
        tier_componente="Tier C",
    ),
    "shimano sora": AuthoritativeGroupSpec(
        canonical_name="Shimano Sora R3000",
        family="shimano",
        speed_options=(9,),
        default_speeds=9,
        actuation="mecanico",
        msrp_min=600.0,
        msrp_max=1150.0,
        tier_componente="Tier C+",
    ),
    "shimano tiagra": AuthoritativeGroupSpec(
        canonical_name="Shimano Tiagra 4700/4720",
        family="shimano",
        speed_options=(10,),
        default_speeds=10,
        actuation="mecanico",  # 4720 es hidraulico pero la base 4700 es mecánica
        msrp_min=850.0,
        msrp_max=1450.0,
        tier_componente="Tier B",
    ),
    "shimano cues": AuthoritativeGroupSpec(
        canonical_name="Shimano CUES U6000",
        family="shimano",
        speed_options=(9, 10, 11),
        default_speeds=10,
        actuation="hidraulico",
        msrp_min=650.0,
        msrp_max=1300.0,
        tier_componente="Tier B-",
    ),
    # Shimano Gravel Específico & Gama Media/Alta
    "shimano grx 400": AuthoritativeGroupSpec(
        canonical_name="Shimano GRX RX400",
        family="shimano",
        speed_options=(10,),
        default_speeds=10,
        actuation="hidraulico",
        msrp_min=1100.0,
        msrp_max=1750.0,
        tier_componente="Tier A",
    ),
    "shimano 105": AuthoritativeGroupSpec(
        canonical_name="Shimano 105 R7000/R7100",
        family="shimano",
        speed_options=(11, 12),
        default_speeds=11,
        actuation="hidraulico",
        msrp_min=1250.0,
        msrp_max=2300.0,
        tier_componente="Tier A",
    ),
    "shimano grx 600": AuthoritativeGroupSpec(
        canonical_name="Shimano GRX RX600",
        family="shimano",
        speed_options=(11, 12),
        default_speeds=11,
        actuation="hidraulico",
        msrp_min=1400.0,
        msrp_max=2400.0,
        tier_componente="Tier A+",
    ),
    "shimano grx 800": AuthoritativeGroupSpec(
        canonical_name="Shimano GRX RX810/RX820",
        family="shimano",
        speed_options=(11, 12),
        default_speeds=11,
        actuation="hidraulico",
        msrp_min=1800.0,
        msrp_max=3200.0,
        tier_componente="Tier S",
    ),
    "shimano grx di2": AuthoritativeGroupSpec(
        canonical_name="Shimano GRX Di2",
        family="shimano",
        speed_options=(11, 12),
        default_speeds=11,
        actuation="hidraulico",
        msrp_min=2800.0,
        msrp_max=4900.0,
        tier_componente="Tier S+",
    ),
    # SRAM
    "sram apex 1": AuthoritativeGroupSpec(
        canonical_name="SRAM Apex 1 Mechanical/HRD",
        family="sram",
        speed_options=(11,),
        default_speeds=11,
        actuation="mecanico",
        msrp_min=1000.0,
        msrp_max=1750.0,
        tier_componente="Tier A-",
    ),
    "sram apex axs": AuthoritativeGroupSpec(
        canonical_name="SRAM Apex AXS XPLR",
        family="sram",
        speed_options=(12,),
        default_speeds=12,
        actuation="hidraulico",
        msrp_min=1700.0,
        msrp_max=2600.0,
        tier_componente="Tier A+",
    ),
    "sram rival 1": AuthoritativeGroupSpec(
        canonical_name="SRAM Rival 1 HRD",
        family="sram",
        speed_options=(11,),
        default_speeds=11,
        actuation="hidraulico",
        msrp_min=1300.0,
        msrp_max=2100.0,
        tier_componente="Tier A",
    ),
    "sram rival axs": AuthoritativeGroupSpec(
        canonical_name="SRAM Rival eTap AXS",
        family="sram",
        speed_options=(12,),
        default_speeds=12,
        actuation="hidraulico",
        msrp_min=2100.0,
        msrp_max=3400.0,
        tier_componente="Tier S",
    ),
    "sram force axs": AuthoritativeGroupSpec(
        canonical_name="SRAM Force AXS XPLR",
        family="sram",
        speed_options=(12,),
        default_speeds=12,
        actuation="hidraulico",
        msrp_min=3200.0,
        msrp_max=5400.0,
        tier_componente="Tier S+",
    ),
    # Campagnolo
    "campagnolo ekar": AuthoritativeGroupSpec(
        canonical_name="Campagnolo Ekar 1x13",
        family="campagnolo",
        speed_options=(13,),
        default_speeds=13,
        actuation="hidraulico",
        msrp_min=2400.0,
        msrp_max=4600.0,
        tier_componente="Tier S+",
    ),
    # Microshift
    "microshift advent": AuthoritativeGroupSpec(
        canonical_name="Microshift Advent",
        family="microshift",
        speed_options=(9,),
        default_speeds=9,
        actuation="mecanico",
        msrp_min=500.0,
        msrp_max=900.0,
        tier_componente="Tier C+",
    ),
    "microshift advent x": AuthoritativeGroupSpec(
        canonical_name="Microshift Advent X",
        family="microshift",
        speed_options=(10,),
        default_speeds=10,
        actuation="mecanico",
        msrp_min=600.0,
        msrp_max=1150.0,
        tier_componente="Tier B-",
    ),
    "microshift sword": AuthoritativeGroupSpec(
        canonical_name="Microshift Sword",
        family="microshift",
        speed_options=(10,),
        default_speeds=10,
        actuation="mecanico",
        msrp_min=750.0,
        msrp_max=1300.0,
        tier_componente="Tier B",
    ),
    # Sensah / LTWOO
    "sensah srx": AuthoritativeGroupSpec(
        canonical_name="Sensah SRX Pro",
        family="sensah",
        speed_options=(11,),
        default_speeds=11,
        actuation="mecanico",
        msrp_min=400.0,
        msrp_max=850.0,
        tier_componente="Tier C",
    ),
    "sensah empire": AuthoritativeGroupSpec(
        canonical_name="Sensah Empire",
        family="sensah",
        speed_options=(11, 12),
        default_speeds=11,
        actuation="mecanico",
        msrp_min=450.0,
        msrp_max=900.0,
        tier_componente="Tier C",
    ),
    "ltwoo gr7": AuthoritativeGroupSpec(
        canonical_name="LTWOO GR7",
        family="ltwoo",
        speed_options=(10,),
        default_speeds=10,
        actuation="mecanico",
        msrp_min=400.0,
        msrp_max=800.0,
        tier_componente="Tier C",
    ),
    "ltwoo gr9": AuthoritativeGroupSpec(
        canonical_name="LTWOO GR9",
        family="ltwoo",
        speed_options=(11,),
        default_speeds=11,
        actuation="hidraulico",
        msrp_min=550.0,
        msrp_max=950.0,
        tier_componente="Tier C+",
    ),
}

# Modelos canónicos con cuadro de aluminio garantizado
KNOWN_ALUMINUM_MODELS = [
    r"jakar", r"grizl al", r"grail al", r"checkpoint alr", r"terra h\d+", r"terra h-",
    r"diverge e5", r"topstone alloy", r"topstone \d", r"aspero al", r"nicasio",
    r"gestalt", r"triban grvl", r"triban rc", r"jari", r"rove al", r"kanzo a",
    r"scultura endurance al", r"silex \d+00", r"crosshill"
]

# Modelos canónicos con cuadro de carbono garantizado
KNOWN_CARBON_MODELS = [
    r"megamo west", r"grizl cf", r"grail cf", r"checkpoint sl", r"checkpoint slr",
    r"terra m\d+", r"terra m-", r"diverge str", r"diverge comp carbon", r"diverge expert",
    r"topstone carbon", r"kanzo fast", r"kanzo adventure carbon", r"silex carbon"
]


def get_canonical_group_spec(group_name: str) -> Optional[AuthoritativeGroupSpec]:
    """Busca y resuelve la especificación canónica autoritativa para una transmisión dada."""
    if not group_name:
        return None
    name_clean = group_name.lower().strip()
    
    # 1. Búsqueda exacta o prefijos directos
    for key, spec in AUTHORITATIVE_GROUPS.items():
        if key in name_clean:
            return spec
            
    # 2. Búsqueda por palabras clave específicas
    if "claris" in name_clean:
        return AUTHORITATIVE_GROUPS["shimano claris"]
    if "tourney" in name_clean:
        return AUTHORITATIVE_GROUPS["shimano tourney"]
    if "sora" in name_clean:
        return AUTHORITATIVE_GROUPS["shimano sora"]
    if "tiagra" in name_clean:
        return AUTHORITATIVE_GROUPS["shimano tiagra"]
    if "grx 400" in name_clean or "rx400" in name_clean:
        return AUTHORITATIVE_GROUPS["shimano grx 400"]
    if "grx 600" in name_clean or "rx600" in name_clean:
        return AUTHORITATIVE_GROUPS["shimano grx 600"]
    if "grx 8" in name_clean or "rx8" in name_clean:
        return AUTHORITATIVE_GROUPS["shimano grx 800"]
    if "apex axs" in name_clean:
        return AUTHORITATIVE_GROUPS["sram apex axs"]
    if "apex" in name_clean:
        return AUTHORITATIVE_GROUPS["sram apex 1"]
    if "rival axs" in name_clean or "rival etap" in name_clean:
        return AUTHORITATIVE_GROUPS["sram rival axs"]
    if "rival" in name_clean:
        return AUTHORITATIVE_GROUPS["sram rival 1"]
    if "ekar" in name_clean:
        return AUTHORITATIVE_GROUPS["campagnolo ekar"]
    if "sword" in name_clean:
        return AUTHORITATIVE_GROUPS["microshift sword"]
    if "advent x" in name_clean:
        return AUTHORITATIVE_GROUPS["microshift advent x"]
    if "advent" in name_clean:
        return AUTHORITATIVE_GROUPS["microshift advent"]
        
    return None


def cross_validate_frame_material(modelo: str, cuadro_actual: str) -> str:
    """Verifica y rectifica el material del cuadro contra la base canónica de modelos."""
    mod_lower = modelo.lower()
    
    for pat in KNOWN_ALUMINUM_MODELS:
        if re.search(pat, mod_lower):
            # Si el modelo es de aluminio, corregir cualquier mención de carbono
            if "carbono" in cuadro_actual.lower() and "completo" in cuadro_actual.lower():
                return "Aluminio hidroformado (Horquilla carbono)"
            if "carbon" in cuadro_actual.lower():
                return "Aluminio triple conificado"
            return cuadro_actual or "Aluminio hidroformado"
            
    for pat in KNOWN_CARBON_MODELS:
        if re.search(pat, mod_lower):
            if "aluminio" in cuadro_actual.lower():
                return "Carbono monocasco"
            return cuadro_actual or "Carbono monocasco"
            
    return cuadro_actual


def sanitize_bike_specs(bike_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza exhaustivamente una bicicleta contra la matriz de verdad:
    1. Corrige tipo_frenos si un grupo mecánico fue catalogado erróneamente como hidráulico.
    2. Rectifica cuadro/horquilla según el modelo real.
    3. Acota precio_pvp inflado al MSRP oficial para erradicar falsos descuentos del 70%.
    """
    clean_bike = dict(bike_dict)
    corrections = []
    
    transmision = str(clean_bike.get("transmision", "")).strip()
    frenos = str(clean_bike.get("frenos", "")).strip()
    tipo_frenos = str(clean_bike.get("tipo_frenos", "")).strip().lower()
    modelo = str(clean_bike.get("modelo", "")).strip()
    cuadro = str(clean_bike.get("cuadro", "")).strip()
    pvp = float(clean_bike.get("precio_pvp") or clean_bike.get("precio_oferta", 0))
    oferta = float(clean_bike.get("precio_oferta", 0))
    
    spec = get_canonical_group_spec(transmision)
    
    # --- 1. Verificación de Frenos vs Grupo ---
    if spec:
        # Grupos que NUNCA son hidráulicos de serie (Tourney, Claris, Sora, Sensah SRX, Advent...)
        if spec.actuation == "mecanico":
            calipers = (frenos + " " + tipo_frenos).lower()
            es_semihidraulico = any(k in calipers for k in ["trp hy/rd", "hy/rd", "juin tech", "zoom hb", "semi-hidraulico", "semihidraulico"])
            
            if tipo_frenos == "hidraulico":
                if es_semihidraulico:
                    clean_bike["tipo_frenos"] = "semihidraulico"
                    corrections.append(f"Freno corregido a semihidráulico (Grupo {spec.canonical_name})")
                else:
                    # Falso hidráulico detectado
                    clean_bike["tipo_frenos"] = "mecanico_doble" if "doble" in calipers else "mecanico_mono"
                    corrections.append(f"Falso hidráulico corregido a mecánico ({spec.canonical_name})")
        elif spec.actuation == "hidraulico":
            if "mecanico" in tipo_frenos and "semi" not in tipo_frenos:
                # Caso inverso: grupo genuinamente hidráulico (e.g. GRX 400) marcado como mecánico
                clean_bike["tipo_frenos"] = "hidraulico"
                corrections.append(f"Freno actualizado a hidráulico nativo ({spec.canonical_name})")
                
    # --- 2. Verificación de Cuadro / Horquilla ---
    cuadro_corregido = cross_validate_frame_material(modelo, cuadro)
    if cuadro_corregido != cuadro:
        clean_bike["cuadro"] = cuadro_corregido
        corrections.append(f"Material cuadro corregido: '{cuadro}' -> '{cuadro_corregido}'")
        
    # --- 3. Acotación de PVP ficticio / inflado ---
    if spec and pvp > 0:
        techo_msrp = spec.msrp_max * 1.50  # Margen de seguridad del 50% sobre MSRP máximo
        if pvp > techo_msrp:
            clean_bike["precio_pvp"] = spec.msrp_max
            corrections.append(f"PVP inflado acotado de {pvp:.0f}€ a {spec.msrp_max:.0f}€ (MSRP oficial)")
            
    # Marcar registro como verificado por autoridad técnica
    clean_bike["especificaciones_verificadas"] = 1
    
    # Registrar notas si hubo correcciones
    if corrections:
        existing_notes = clean_bike.get("notas_veredicto", "") or ""
        audit_note = " | [Audit]: " + "; ".join(corrections)
        clean_bike["notas_veredicto"] = (existing_notes + audit_note).strip()
        
    return clean_bike


def batch_sanitize_catalog(dry_run: bool = False) -> Dict[str, int]:
    """
    Ejecuta el saneamiento integral de todas las bicicletas del catálogo SQLite.
    Corrige falsos hidráulicos, acota PVPs inflados y guarda en base de datos.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bicicletas")
    rows = c.fetchall()
    conn.close()
    
    stats = {
        "total": len(rows),
        "frenos_corregidos": 0,
        "cuadros_corregidos": 0,
        "pvp_acotados": 0,
        "verificados": 0,
    }
    
    for row in rows:
        b_dict = dict(row)
        sanitized = sanitize_bike_specs(b_dict)
        
        hubo_cambio = False
        if sanitized["tipo_frenos"] != b_dict["tipo_frenos"]:
            stats["frenos_corregidos"] += 1
            hubo_cambio = True
        if sanitized["cuadro"] != b_dict["cuadro"]:
            stats["cuadros_corregidos"] += 1
            hubo_cambio = True
        if sanitized.get("precio_pvp") != b_dict.get("precio_pvp"):
            stats["pvp_acotados"] += 1
            hubo_cambio = True
            
        stats["verificados"] += 1
        
        if not dry_run and (hubo_cambio or b_dict.get("especificaciones_verificadas", 0) == 0):
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
            
    return stats
