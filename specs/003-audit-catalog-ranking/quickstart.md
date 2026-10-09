# Quickstart Validation Guide: Catalog Freshness, Spec Audit & Ranking Calibration

**Feature**: `003-audit-catalog-ranking`
**Date**: 2026-10-10

## Prerequisites

- Python 3.11+ installed.
- SQLite catalog database `gravel_madrid.db` initialized.

---

## Scenario 1: Validate Authoritative Component Correction

### Command
```bash
python3 -c "
from gravel_bot.components_authority import sanitize_bike_specs
raw_ad = {
    'marca': 'Decathlon',
    'modelo': 'Triban RC 120 Claris',
    'transmision': 'Shimano Claris 2x8',
    'tipo_frenos': 'hidraulico',  # Afirmación errónea en anuncio
    'precio_pvp': 3000.0,         # PVP ficticio inflado
    'precio_oferta': 650.0
}
clean = sanitize_bike_specs(raw_ad)
assert clean['tipo_frenos'] == 'mecanico_mono', 'Error: Claris debe ser forzado a frenos mecánicos'
assert clean['precio_pvp'] <= 1100.0, 'Error: PVP inflado debe ser acotado al MSRP oficial'
print('✅ Test 1 Superado: Componentes y PVP inflados saneados con éxito.')
"
```

### Expected Output
- `✅ Test 1 Superado: Componentes y PVP inflados saneados con éxito.`

---

## Scenario 2: Validate Itemized Rubric Breakdown & Warranty Bonus

### Command
```bash
python3 -c "
from gravel_bot.evaluator import calcular_rubrica_calibrada
itemized = calcular_rubrica_calibrada(
    disciplina='gravel',
    tipo_frenos='hidraulico',
    tipo_trans='2x10',
    cuadro='Aluminio',
    horquilla='Carbono',
    udh=1,
    precio=999.0,
    talla_ok=True,
    channel_type='tienda_fisica'
)
assert itemized['c1_frenos'] == 25.0, 'Frenos hidráulicos deben otorgar 25 pts'
assert itemized['c6_garantia'] == 5.0, 'Tienda física oficial debe recibir 5 pts de garantía'
assert itemized['total_score'] >= 90.0, 'Montaje de tienda física con GRX debe ser Tier S+'
print(f'✅ Test 2 Superado: Rúbrica calibrada ({itemized[\"total_score\"]}/100 pts, Nota {itemized[\"nota\"]}/10).')
"
```

### Expected Output
- `✅ Test 2 Superado: Rúbrica calibrada (95.0/100 pts, Nota 9.5/10).`

---

## Scenario 3: Execute Catalog Re-scoring Pipeline

### Command
```bash
python3 gravel_tracker.py --re-score
```

### Expected Output
- Prints summary of corrected components and updated Tier classifications.
- Zero crashes; database updated.