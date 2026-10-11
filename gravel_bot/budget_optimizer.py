"""
gravel_bot.budget_optimizer - Motor de Optimización de Presupuesto y Recomendación Ejecutiva
Filtra ruido (cuadros, ebikes, tiendas cerradas), calcula el índice Value-for-Money (VfM)
y genera el podio ejecutivo: #1 Mejor Valor, #2 Mejor Ganga y #3 Smart Stretch (+15%).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re
import json
from gravel_bot.db import get_candidate_bikes_for_budget


@dataclass
class BudgetQuery:
    """Criterios de búsqueda del usuario para encontrar la mejor bicicleta."""
    budget_ceiling: float
    rider_height_cm: int = 169
    target_size: Optional[str] = None
    channel_filter: str = "all"  # "all", "local_madrid", "certified", "outlet"
    include_stretch: bool = True


@dataclass
class CleanCandidateBike:
    """Bicicleta candidata limpia, verificada y sin ruido."""
    id: int
    slug: str
    brand: str
    model: str
    price: float
    pvp: float
    discount_pct: float
    discipline: str
    frame_material: str
    fork_material: str
    drivetrain: str
    brake_type: str
    has_hydraulic_brakes: bool
    has_carbon_fork: bool
    available_sizes: List[str]
    size_compatibility: str
    store_name: str
    channel_type: str
    product_url: str
    rubric_score: float
    rubric_nota: float
    rubric_tier: str
    vfm_index: float
    audit_status: str = "pendiente"
    especificaciones_verificadas: int = 0
    c1_frenos: float = 0.0
    c2_transmision: float = 0.0
    c3_cuadro: float = 0.0
    c4_precio: float = 0.0
    c5_talla: float = 0.0
    c6_garantia: float = 0.0

@dataclass
class RecommendationPodio:
    """Resultado ejecutivo de recomendación para el usuario."""
    query: BudgetQuery
    total_candidates_scanned: int
    valid_candidates_count: int
    best_value: Optional[CleanCandidateBike] = None
    top_bargain: Optional[CleanCandidateBike] = None
    smart_stretch: Optional[CleanCandidateBike] = None
    stretch_reason: Optional[str] = None
    budget_saver: Optional[CleanCandidateBike] = None
    best_used_deal: Optional[CleanCandidateBike] = None
    status: str = "success"  # "success", "no_exact_match", "budget_too_low"


def calculate_vfm_index(rubric_score: float, price: float) -> float:
    """Calcula el índice Value-for-Money (VfM) normalizado por cada 1.000€ invertidos."""
    if price <= 0:
        return 0.0
    return round((rubric_score / price) * 1000.0, 2)


def is_noise_candidate(model_text: str, brand_text: str, discipline: str, store_name: str) -> bool:
    """Identifica si un registro es ruido (cuadro suelto, ebike, no-gravel o tienda cerrada)."""
    full_text = f"{brand_text} {model_text}".lower()
    store_lower = (store_name or "").lower()
    disc_lower = (discipline or "").lower()

    # 0. Marca desconocida o vacía: no identificable => ruido (aplicado en un único punto compartido por CLI/Telegram/Web)
    brand_clean = (brand_text or "").strip().lower()
    if brand_clean in ("desconocida", "desconocido", "unknown", ""):
        return True

    # 1. Tienda cerrada o en liquidación
    if any(k in store_lower for k in ["cerrada", "liquidación", "liquidacion", "tuvalum"]):
        return True

    # 2. Motorizada / E-Bike
    ebike_keywords = ["ebike", "e-bike", "eléctrica", "electrica", "powerfly", "rise", "trance", "marlin+", "patron", "lumen", "wild"]
    if disc_lower in ["ebike", "e-bike", "electrica"]:
        return True
    if any(k in full_text for k in ebike_keywords):
        return True

    # 3. Cuadro suelto / Frameset (no es bicicleta completa)
    if re.search(r'\b(cuadro|frameset|frame)\b', full_text):
        if not any(k in full_text for k in ["completa", "bici completa", "montada"]):
            return True

    # 4. Disciplina no apta
    if disc_lower in ["carretera", "mtb", "fitness", "infantil", "junior", "enduro", "downhill"]:
        return True

    return False


def is_size_compatible(talla_169: str, tallas_disp_str: str, rider_height_cm: int = 169, target_size: Optional[str] = None,
                       marca: str = "", modelo: str = "") -> Tuple[bool, str]:
    """Evalúa la compatibilidad de talla delegando en el motor de geometría y biomecánica."""
    from gravel_bot.geometry_sizing import evaluate_size_compatibility_dynamic, get_recommended_size_dynamic

    talla_169_clean = (talla_169 or "").strip()
    disp_clean = (tallas_disp_str or "").strip()

    if target_size:
        tgt = target_size.strip().upper()
        if tgt in talla_169_clean.upper() or (disp_clean and tgt in disp_clean.upper()):
            return True, talla_169_clean or tgt
        return False, "incompatible"

    # Placeholder tipo "Consultar tienda" no es una talla: se descarta antes de evaluar
    size_token_re = re.compile(r"^(xxs|xs|s|m|l|xl|xxl)(\s*\(.*\))?$|^\d{2}(-\d{2})?(\s*cm)?(\s*\(.*\))?$", re.IGNORECASE)
    sizes_list = [s.strip() for s in disp_clean.replace(";", ",").split(",") if s.strip() and size_token_re.match(s.strip())]

    # Evaluar compatibilidad dinámica por marca/modelo si hay tallas registradas reales
    if marca and sizes_list:
        compat, size_name, _ = evaluate_size_compatibility_dynamic(marca, modelo, rider_height_cm, sizes_list)
        if not compat:
            return False, "incompatible"
        if size_name and size_name != "Verificar":
            return True, size_name

    if "no compatible" in talla_169_clean.lower() or "incompatible" in talla_169_clean.lower():
        return False, "incompatible"

    rec = get_recommended_size_dynamic(marca or "Standard", modelo or "Gravel", rider_height_cm)
    rec_size = rec.get("talla_recomendada", "S (51-52 cm)")
    return True, talla_169_clean or rec_size

_CHANNEL_LABEL = {
    "tienda_fisica": "Tienda física",
    "tienda_online": "Tienda online",
    "ocasion_certificada": "Ocasión certificada",
    "particular": "Particular",
}

def _frenos_label(has_hydraulic_brakes: bool) -> str:
    """Etiqueta canónica de frenos, idéntica en CLI, Telegram y Web (FR-05)."""
    return "Frenos Hidráulicos" if has_hydraulic_brakes else "Frenos Mecánicos/Semihidráulicos"


def _horquillas_label(has_carbon_fork: bool) -> str:
    return "Horquilla Carbono" if has_carbon_fork else "Horquilla Aluminio"


def _channel_suffix(store_name: str, channel: str) -> str:
    """Calificador de canal mostrado una sola vez, con nomenclatura correcta.

    Evita duplicar el calificador cuando el nombre de la tienda ya lo indica
    (ej. 'Wallapop (Particulares Madrid 25km)').
    """
    label = _CHANNEL_LABEL.get(channel, channel.replace('_', ' ').capitalize())
    if channel == "particular" and "particular" in (store_name or "").lower():
        return ""
    return f" ({label})"


def classify_channel(store_name: str, store_type: Optional[str] = None) -> str:
    """Clasifica el canal de compra: tienda_fisica, online, ocasion_certificada, particular."""
    st_name = (store_name or "").lower()
    st_type = (store_type or "").lower()

    if st_type in ["fisica", "tienda_fisica"]:
        return "tienda_fisica"
    if "buycycle" in st_name or "reacondicionad" in st_name or "certificad" in st_name:
        return "ocasion_certificada"
    if "wallapop" in st_name:
        return "particular"
    physical_indicators = ["vallecas", "m-30", "atocha", "madrid", "sanferbike", "buhobike", "calmera", "decathlon", "escapa", "ciclos corredor", "bicimarket red"]
    if any(k in st_name for k in physical_indicators):
        return "tienda_fisica"
    return "tienda_online"


def _transmision_drivetrain(row: Any) -> str:
    """Concatena transmisión + tipo sin duplicar: si el tipo ya aparece (dentro o fuera de paréntesis) no se repite."""
    trans = (row["transmision"] or "").strip()
    tipo = (row["tipo_transmision"] or "").strip()
    if not tipo:
        return trans or "Transmisión estándar"
    base = re.sub(rf"\s*\({re.escape(tipo)}\)\s*$", "", trans)
    if tipo in base:
        return base
    return f"{base} ({tipo})".strip() or "Transmisión estándar"


def clean_candidate_from_row(row: Any, rider_height_cm: int = 169, target_size: Optional[str] = None) -> Optional[CleanCandidateBike]:
    """Convierte un registro SQLite en un CleanCandidateBike sanitizado o None si es descartado."""
    model = row["modelo"] or ""
    brand = row["marca"] or ""
    disc = row["disciplina"] or "gravel"
    store = row["tienda_nombre"] or ""
    store_type = row["tienda_tipo"] or "online"

    # 1. Filtro de Ruido
    if is_noise_candidate(model, brand, disc, store):
        return None

    # 2. Filtro de Talla
    talla_169 = row["talla_recomendada_169"] or ""
    tallas_disp = row["tallas_disponibles"] if "tallas_disponibles" in row.keys() else ""
    compatible, sizing_label = is_size_compatible(talla_169, tallas_disp, rider_height_cm, target_size, marca=brand, modelo=model)
    if not compatible:
        return None

    price = float(row["precio_oferta"] or 0.0)
    if price <= 0:
        return None

    pvp = float(row["precio_pvp"] or price)
    discount_pct = round(((pvp - price) / pvp * 100.0), 1) if pvp > price else 0.0

    brakes = (row["frenos"] or "") + " " + (row["tipo_frenos"] or "")
    has_hydraulic = "hidraulico" in brakes.lower()
    fork = row["horquilla"] or ""
    has_carbon_fork = "carbono" in fork.lower()

    score = float(row["puntuacion_total"] or 0.0)
    nota = float(row["nota"] or (score / 10.0))
    tier = row["tier"] or "Tier A"
    vfm = calculate_vfm_index(score, price)
    channel = classify_channel(store, store_type)

    return CleanCandidateBike(
        id=row["id"],
        slug=row["slug"],
        brand=brand,
        model=model,
        price=price,
        pvp=pvp,
        discount_pct=discount_pct,
        discipline=disc,
        frame_material=row["cuadro"] or "Aluminio",
        fork_material=fork,
        drivetrain=_transmision_drivetrain(row),
        brake_type=row["tipo_frenos"] or "mecanico",
        has_hydraulic_brakes=has_hydraulic,
        has_carbon_fork=has_carbon_fork,
        available_sizes=[sizing_label],
        size_compatibility=sizing_label,
        store_name=store or "Online",
        channel_type=channel,
        product_url=row["url_oferta"] or "",
        rubric_score=score,
        rubric_nota=nota,
        rubric_tier=tier,
        vfm_index=vfm,
        audit_status=row["audit_status"] if ("audit_status" in row.keys() and row["audit_status"]) else "pendiente",
        especificaciones_verificadas=int(row["especificaciones_verificadas"]) if ("especificaciones_verificadas" in row.keys() and row["especificaciones_verificadas"]) else 0,
        c1_frenos=float(row["c1_frenos"] or 0.0) if "c1_frenos" in row.keys() else 0.0,
        c2_transmision=float(row["c2_transmision"] or 0.0) if "c2_transmision" in row.keys() else 0.0,
        c3_cuadro=float(row["c3_cuadro"] or 0.0) if "c3_cuadro" in row.keys() else 0.0,
        c4_precio=float(row["c4_precio"] or 0.0) if "c4_precio" in row.keys() else 0.0,
        c5_talla=float(row["c5_talla"] or 0.0) if "c5_talla" in row.keys() else 0.0,
        c6_garantia=float(row["c6_garantia"] or 0.0) if "c6_garantia" in row.keys() else 0.0
    )

def optimize_for_budget(
    budget: float,
    height_cm: Optional[int] = 169,
    size: Optional[str] = None,
    channel: str = "all",
    include_stretch: bool = True
) -> RecommendationPodio:
    """Genera el podio ejecutivo optimizado para el presupuesto del usuario."""
    query = BudgetQuery(
        budget_ceiling=budget,
        rider_height_cm=height_cm or 169,
        target_size=size,
        channel_filter=channel,
        include_stretch=include_stretch
    )

    # Margen de extracción para evaluar candidatos dentro de presupuesto y stretch (+15% hasta +150€)
    max_stretch_price = budget * 1.15 if include_stretch else budget
    rows = get_candidate_bikes_for_budget(max_price=max_stretch_price + 50.0)

    clean_candidates: List[CleanCandidateBike] = []
    for r in rows:
        cand = clean_candidate_from_row(r, rider_height_cm=query.rider_height_cm, target_size=query.target_size)
        if cand:
            if channel == "local_madrid" and cand.channel_type != "tienda_fisica":
                continue
            if channel == "certified" and cand.channel_type != "ocasion_certificada":
                continue
            clean_candidates.append(cand)

    # FR-08: el podio ejecutivo solo admite canales con garantía de tienda;
    # particular/segunda mano se presenta en el bloque separado ♻️ Ocasión a destacar.
    new_channel_pool = [c for c in clean_candidates if c.channel_type != "particular"]
    used_channel_pool = [c for c in clean_candidates if c.channel_type == "particular"]

    # Dividir entre presupuesto estricto y stretch
    in_budget = [c for c in new_channel_pool if c.price <= budget]
    stretch_pool = [c for c in new_channel_pool if budget < c.price <= max_stretch_price and (c.price - budget) <= 150.0]
    used_in_budget = [c for c in used_channel_pool if c.price <= budget]

    podio = RecommendationPodio(
        query=query,
        total_candidates_scanned=len(rows),
        valid_candidates_count=len(in_budget),
        status="success" if in_budget else ("no_exact_match" if stretch_pool else "budget_too_low")
    )
    if used_in_budget:
        podio.best_used_deal = sorted(used_in_budget, key=lambda x: (x.rubric_score, x.vfm_index), reverse=True)[0]

    if not in_budget:
        if stretch_pool:
            # Recomendar el más accesible del stretch
            podio.smart_stretch = sorted(stretch_pool, key=lambda x: x.price)[0]
            podio.stretch_reason = f"No hay bicicletas completas por debajo de {budget:.0f} €. Esta es la opción viable más cercana."
        return podio

    # 1. MEJOR COMPRA ABSOLUTA (#1): Máxima puntuación de componentes dentro de presupuesto
    # Desempate: mayor VfM index (menor precio a igual calidad)
    in_budget_sorted = sorted(in_budget, key=lambda x: (x.rubric_score, x.vfm_index), reverse=True)
    best_value = in_budget_sorted[0]
    podio.best_value = best_value

    # 2. MEJOR GANGA (#2): Mayor descuento porcentual (mínimo 15% o ahorro de 100€)
    # Preferiblemente distinta del #1
    bargains = [c for c in in_budget if c.id != best_value.id and (c.discount_pct >= 15.0 or (c.pvp - c.price) >= 100.0)]
    if bargains:
        podio.top_bargain = sorted(bargains, key=lambda x: (x.discount_pct, x.rubric_score), reverse=True)[0]
    elif len(in_budget_sorted) > 1:
        # Alternativa más económica pero de buen nivel
        podio.top_bargain = sorted(in_budget_sorted[1:], key=lambda x: x.price)[0]

    # 3. SMART STRETCH (#3): Si por <= +15% (máx 150€) se desbloquea un salto crítico
    if include_stretch and stretch_pool:
        # Buscar candidatos que desbloqueen frenos hidráulicos, carbono o salto de Tier
        promising_stretch = []
        for s in stretch_pool:
            diff = s.price - budget
            reason = None
            if not best_value.has_hydraulic_brakes and s.has_hydraulic_brakes:
                reason = f"Desbloquea frenos hidráulicos completos frente a frenos mecánicos (+{diff:.0f} €)."
            elif not best_value.has_carbon_fork and s.has_carbon_fork:
                reason = f"Desbloquea horquilla de carbono frente a aluminio (+{diff:.0f} €)."
            elif s.rubric_tier == "Tier S+" and best_value.rubric_tier not in ["Tier S+", "Tier S"]:
                reason = f"Salto de categoría a Tier S+ con transmisión superior (+{diff:.0f} €)."
            elif s.rubric_score >= (best_value.rubric_score + 5.0):
                reason = f"Calidad general sensiblemente superior (+5 pts en rúbrica por +{diff:.0f} €)."

            if reason:
                promising_stretch.append((s, reason, diff))

        if promising_stretch:
            # Elegir la que menor sobrecoste tenga para el salto
            best_stretch, reason_text, _ = sorted(promising_stretch, key=lambda x: (x[2], -x[0].rubric_score))[0]
            podio.smart_stretch = best_stretch
            podio.stretch_reason = reason_text

    # 4. ALTERNATIVA BUDGET SAVER (opcional): si hay una bici a <= 0.85*budget con nota casi igual
    savers = [c for c in in_budget if c.price <= (budget * 0.85) and c.rubric_score >= (best_value.rubric_score - 5.0) and c.id != best_value.id]
    if savers:
        podio.budget_saver = sorted(savers, key=lambda x: x.vfm_index, reverse=True)[0]

    return podio


def format_budget_recommendation_card(podio: RecommendationPodio, format: str = "text") -> str:
    """Formatea el podio ejecutivo en texto para consola o en JSON."""
    if format == "json":
        data = {
            "status": podio.status,
            "budget": podio.query.budget_ceiling,
            "rider": {
                "height_cm": podio.query.rider_height_cm,
                "target_size": podio.query.target_size
            },
            "total_candidates_scanned": podio.total_candidates_scanned,
            "valid_candidates_count": podio.valid_candidates_count,
            "best_value": podio.best_value.__dict__ if podio.best_value else None,
            "top_bargain": podio.top_bargain.__dict__ if podio.top_bargain else None,
            "smart_stretch": podio.smart_stretch.__dict__ if podio.smart_stretch else None,
            "stretch_reason": podio.stretch_reason,
            "budget_saver": podio.budget_saver.__dict__ if podio.budget_saver else None,
            "best_used_deal": podio.best_used_deal.__dict__ if podio.best_used_deal else None
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    # Formato Texto / CLI
    lines = []
    lines.append("=" * 110)
    lines.append(f"🎯 PODIO DE RECOMENDACIÓN PARA TU PRESUPUESTO: {podio.query.budget_ceiling:,.0f} € (Altura: {podio.query.rider_height_cm} cm)")
    lines.append("=" * 110)
    lines.append(f"Modelos evaluados: {podio.total_candidates_scanned} | Opciones válidas en presupuesto y talla: {podio.valid_candidates_count}\n")

    if not podio.best_value:
        lines.append(f"⚠️ No se encontraron bicicletas gravel completas disponibles estrictamente por debajo de {podio.query.budget_ceiling:.0f} €.")
        if podio.smart_stretch:
            ss = podio.smart_stretch
            lines.append(f"\n🚀 OPCIÓN MÁS CERCANA:")
            lines.append(f"   • Modelo:     {ss.brand} {ss.model}")
            lines.append(f"   • Precio:     {ss.price:.0f} € ({podio.stretch_reason})")
            frenos_ss = _frenos_label(ss.has_hydraulic_brakes)
            lines.append(f"   • Componentes: {ss.drivetrain} | {frenos_ss}")
            lines.append(f"   • Talla:      {ss.size_compatibility}")
            lines.append(f"   • Tienda:     {ss.store_name}{_channel_suffix(ss.store_name, ss.channel_type)}")
            lines.append(f"   • Enlace:     {ss.product_url}")
        if podio.best_used_deal:
            lines.append("")
            lines.append("♻️ OCASIÓN A DESTACAR — segunda mano / particular ⚠️ SIN garantía de tienda")
            ud = podio.best_used_deal
            lines.append(f"   • Modelo:     {ud.brand} {ud.model}")
            lines.append(f"   • Precio:     {ud.price:.0f} €")
            lines.append(f"   • Componentes: {ud.drivetrain} | {_frenos_label(ud.has_hydraulic_brakes)}")
            lines.append(f"   • Talla:      {ud.size_compatibility}")
            lines.append(f"   • Tienda:     {ud.store_name}{_channel_suffix(ud.store_name, ud.channel_type)}")
            lines.append(f"   • Enlace:     {ud.product_url}")
            lines.append(f"   • Veredicto:  {ud.rubric_tier} (Nota {ud.rubric_nota:.1f}/10)")
        lines.append("=" * 110)
        return "\n".join(lines)

    # 1. MEJOR COMPRA
    bv = podio.best_value
    lines.append(f"🥇 1. MEJOR COMPRA ABSOLUTA (Calidad Máxima en Presupuesto)")
    lines.append(f"   • Modelo:     {bv.brand} {bv.model}")
    desc_str = f" (PVP: {bv.pvp:.0f} € | Descuento: -{bv.discount_pct:.0f}%)" if bv.discount_pct > 0 else ""
    lines.append(f"   • Precio:     {bv.price:.0f} €{desc_str}")
    frenos_desc = _frenos_label(bv.has_hydraulic_brakes)
    horq_desc = _horquillas_label(bv.has_carbon_fork)
    lines.append(f"   • Componentes: {bv.drivetrain} | {frenos_desc} | {horq_desc}")
    lines.append(f"   • Talla:      {bv.size_compatibility}")
    lines.append(f"   • Tienda:     {bv.store_name}{_channel_suffix(bv.store_name, bv.channel_type)}")
    lines.append(f"   • Enlace:     {bv.product_url}")
    lines.append(f"   • Veredicto:  {bv.rubric_tier} (Nota {bv.rubric_nota:.1f}/10 | Eficiencia VfM: {bv.vfm_index:.1f} pts/k€)")
    lines.append("")

    # 2. MEJOR GANGA
    if podio.top_bargain:
        tb = podio.top_bargain
        lines.append(f"🥈 2. MEJOR GANGA / PRECIO MÁS AJUSTADO")
        lines.append(f"   • Modelo:     {tb.brand} {tb.model}")
        tb_desc = f" (PVP: {tb.pvp:.0f} € | Ahorro: -{tb.discount_pct:.0f}%)" if tb.discount_pct > 0 else f" (Ahorras {podio.query.budget_ceiling - tb.price:.0f} € de tu tope)"
        lines.append(f"   • Precio:     {tb.price:.0f} €{tb_desc}")
        frenos_tb = _frenos_label(tb.has_hydraulic_brakes)
        horq_tb = _horquillas_label(tb.has_carbon_fork)
        lines.append(f"   • Componentes: {tb.drivetrain} | {frenos_tb} | {horq_tb}")
        lines.append(f"   • Talla:      {tb.size_compatibility}")
        lines.append(f"   • Tienda:     {tb.store_name}{_channel_suffix(tb.store_name, tb.channel_type)}")
        lines.append(f"   • Enlace:     {tb.product_url}")
        lines.append(f"   • Veredicto:  {tb.rubric_tier} (Nota {tb.rubric_nota:.1f}/10)")
        lines.append("")

    # 3. SMART STRETCH
    if podio.smart_stretch:
        ss = podio.smart_stretch
        lines.append(f"🚀 3. SMART STRETCH (+{ss.price - podio.query.budget_ceiling:.0f} € que merecen la pena)")
        lines.append(f"   • Modelo:     {ss.brand} {ss.model}")
        lines.append(f"   • Precio:     {ss.price:.0f} €")
        lines.append(f"   • Salto Clave: {podio.stretch_reason}")
        frenos_ss = _frenos_label(ss.has_hydraulic_brakes)
        lines.append(f"   • Componentes: {ss.drivetrain} | {frenos_ss}")
        lines.append(f"   • Talla:      {ss.size_compatibility}")
        lines.append(f"   • Tienda:     {ss.store_name}{_channel_suffix(ss.store_name, ss.channel_type)}")
        lines.append(f"   • Enlace:     {ss.product_url}")
        lines.append("")

    # 4. BUDGET SAVER
    if podio.budget_saver:
        bs = podio.budget_saver
        lines.append(f"💡 OPCIÓN DE AHORRO INTELIGENTE:")
        lines.append(f"   • Modelo:     {bs.brand} {bs.model} por {bs.price:.0f} € (Ahorras {podio.query.budget_ceiling - bs.price:.0f} € manteniendo nivel {bs.rubric_tier})")
        lines.append(f"   • Enlace:     {bs.product_url}")
        lines.append("")

    # BLOQUE SEPARADO ♻️ (FR-08): segunda mano/particulares nunca compiten con nuevas
    if podio.best_used_deal:
        ud = podio.best_used_deal
        lines.append("♻️ OCASIÓN A DESTACAR — segunda mano / particular ⚠️ SIN garantía de tienda")
        lines.append(f"   • Modelo:     {ud.brand} {ud.model}")
        lines.append(f"   • Precio:     {ud.price:.0f} €")
        frenos_ud = _frenos_label(ud.has_hydraulic_brakes)
        horq_ud = _horquillas_label(ud.has_carbon_fork)
        lines.append(f"   • Componentes: {ud.drivetrain} | {frenos_ud} | {horq_ud}")
        lines.append(f"   • Talla:      {ud.size_compatibility}")
        lines.append(f"   • Tienda:     {ud.store_name}{_channel_suffix(ud.store_name, ud.channel_type)}")
        lines.append(f"   • Enlace:     {ud.product_url}")
        lines.append(f"   • Veredicto:  {ud.rubric_tier} (Nota {ud.rubric_nota:.1f}/10)")
        lines.append("")

    lines.append("=" * 110)
    return "\n".join(lines)


def format_budget_podio_html(podio: RecommendationPodio) -> str:
    """Formatea el podio ejecutivo en HTML limpio para Telegram Bot."""
    b = podio.query.budget_ceiling
    h = podio.query.rider_height_cm
    lines = [
        f"🎯 <b>PODIO RECOMENDADO PARA TU PRESUPUESTO: {b:,.0f} €</b>",
        f"<i>Perfil: {h} cm | Cero cuadros sueltos, solo gravel 100% real</i>\n"
    ]
    if not podio.best_value:
        lines.append(f"⚠️ No hay opciones gravel completas disponibles estrictamente por debajo de {b:.0f} €.")
        if podio.smart_stretch:
            ss = podio.smart_stretch
            lines.append(f"\n🚀 <b>Opción viable más cercana:</b>")
            lines.append(f"🚲 <b>{ss.brand} {ss.model}</b> — <b>{ss.price:.0f} €</b>")
            lines.append(f"💡 <i>{podio.stretch_reason}</i>")
            lines.append(f"⚙️ {ss.drivetrain} • {_frenos_label(ss.has_hydraulic_brakes)}")
            lines.append(f"📏 Talla {ss.size_compatibility}")
            lines.append(f"🏪 {ss.store_name}{_channel_suffix(ss.store_name, ss.channel_type)}")
            if ss.product_url:
                lines.append(f"🔗 <a href='{ss.product_url}'>Ver en {ss.store_name}</a>")
        if podio.best_used_deal:
            ud = podio.best_used_deal
            lines.append("")
            lines.append("♻️ <b>OCASIÓN A DESTACAR</b> <i>(segunda mano / particular — ⚠️ SIN garantía de tienda)</i>")
            lines.append(f"🚲 <b>{ud.brand} {ud.model}</b> — <b>{ud.price:.0f} €</b>")
            lines.append(f"⚙️ {ud.drivetrain} • {_frenos_label(ud.has_hydraulic_brakes)}")
            lines.append(f"📏 Talla {ud.size_compatibility}")
            lines.append(f"🏪 {ud.store_name}{_channel_suffix(ud.store_name, ud.channel_type)}")
            if ud.product_url:
                lines.append(f"🔗 <a href='{ud.product_url}'>Ver Oferta del Particular</a>")
        return "\n".join(lines)

    bv = podio.best_value
    lines.append("🥇 <b>1. MEJOR COMPRA EN PRESUPUESTO</b>")
    lines.append(f"🚲 <b>{bv.brand} {bv.model}</b>")
    desc_str = f" (<s>{bv.pvp:.0f} €</s> • -{bv.discount_pct:.0f}%)" if bv.discount_pct > 0 else ""
    lines.append(f"💰 <b>{bv.price:.0f} €</b>{desc_str}")
    frenos = _frenos_label(bv.has_hydraulic_brakes)
    horq = _horquillas_label(bv.has_carbon_fork)
    lines.append(f"⚙️ {bv.drivetrain} • {frenos} • {horq}")
    lines.append(f"📏 Talla {bv.size_compatibility}")
    lines.append(f"🏪 {bv.store_name}{_channel_suffix(bv.store_name, bv.channel_type)}")
    lines.append(f"⭐ Nota: <b>{bv.rubric_nota:.1f}/10 ({bv.rubric_tier})</b>")
    if bv.product_url:
        lines.append(f"🔗 <a href='{bv.product_url}'>Ver y Comprar en Tienda</a>")
    lines.append("")

    if podio.top_bargain:
        tb = podio.top_bargain
        lines.append("🥈 <b>2. MEJOR GANGA / PRECIO MÁS AJUSTADO</b>")
        lines.append(f"🚲 <b>{tb.brand} {tb.model}</b>")
        tb_desc = f" (<s>{tb.pvp:.0f} €</s> • -{tb.discount_pct:.0f}%)" if tb.discount_pct > 0 else f" (Ahorras {b - tb.price:.0f} €)"
        lines.append(f"💰 <b>{tb.price:.0f} €</b>{tb_desc}")
        frenos_tb = _frenos_label(tb.has_hydraulic_brakes)
        horq_tb = _horquillas_label(tb.has_carbon_fork)
        lines.append(f"⚙️ {tb.drivetrain} • {frenos_tb} • {horq_tb}")
        lines.append(f"📏 Talla {tb.size_compatibility}")
        lines.append(f"🏪 {tb.store_name}{_channel_suffix(tb.store_name, tb.channel_type)}")
        lines.append(f"⭐ Nota: <b>{tb.rubric_nota:.1f}/10 ({tb.rubric_tier})</b>")
        if tb.product_url:
            lines.append(f"🔗 <a href='{tb.product_url}'>Ver y Comprar en Tienda</a>")
        lines.append("")

    if podio.smart_stretch:
        ss = podio.smart_stretch
        diff = ss.price - b
        lines.append(f"🚀 <b>3. SMART STRETCH (+{diff:.0f} € que merecen la pena)</b>")
        lines.append(f"🚲 <b>{ss.brand} {ss.model}</b> — <b>{ss.price:.0f} €</b>")
        lines.append(f"💡 <i>{podio.stretch_reason}</i>")
        lines.append(f"⚙️ {ss.drivetrain} • {_frenos_label(ss.has_hydraulic_brakes)}")
        lines.append(f"📏 Talla {ss.size_compatibility}")
        lines.append(f"🏪 {ss.store_name}{_channel_suffix(ss.store_name, ss.channel_type)}")
        if ss.product_url:
            lines.append(f"🔗 <a href='{ss.product_url}'>Ver y Comprar en Tienda</a>")
        lines.append("")

    if podio.budget_saver:
        bs = podio.budget_saver
        lines.append(f"💡 <b>Alternativa de ahorro inteligente:</b>")
        lines.append(f"🚲 <b>{bs.brand} {bs.model}</b> por <b>{bs.price:.0f} €</b> (Ahorras {b - bs.price:.0f} € manteniendo {bs.rubric_tier})")
        if bs.product_url:
            lines.append(f"🔗 <a href='{bs.product_url}'>Ver Oferta</a>")

    # BLOQUE SEPARADO ♻️ (FR-08): segunda mano/particulares con aviso sin garantía
    if podio.best_used_deal:
        ud = podio.best_used_deal
        lines.append("")
        lines.append("♻️ <b>OCASIÓN A DESTACAR</b> <i>(segunda mano / particular — ⚠️ SIN garantía de tienda)</i>")
        lines.append(f"🚲 <b>{ud.brand} {ud.model}</b>")
        lines.append(f"💰 <b>{ud.price:.0f} €</b>")
        lines.append(f"⚙️ {ud.drivetrain} • {_frenos_label(ud.has_hydraulic_brakes)}")
        lines.append(f"📏 Talla {ud.size_compatibility}")
        lines.append(f"🏪 {ud.store_name}{_channel_suffix(ud.store_name, ud.channel_type)}")
        lines.append(f"⭐ Nota: <b>{ud.rubric_nota:.1f}/10 ({ud.rubric_tier})</b>")
        if ud.product_url:
            lines.append(f"🔗 <a href='{ud.product_url}'>Ver Oferta del Particular</a>")

    return "\n".join(lines)
