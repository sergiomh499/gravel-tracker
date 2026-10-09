# CLI Interface Contract: Catalog Audit & Ranking Calibration

**Feature**: `003-audit-catalog-ranking`
**Target Binary**: `gravel_tracker.py`

---

## 1. Catalog Live Audit Command

Verifies link health, stock availability, and live asking prices.

```bash
python3 gravel_tracker.py --audit [--limit N] [--store STORE] [--verbose] [--dry-run]
```

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--limit`, `-n` | `int` | `50` | Maximum listings to verify in this run |
| `--store`, `-s` | `str` | `None` | Filter audit to a specific merchant (e.g. `decathlon`, `escapa`) |
| `--dry-run` | Flag | `False` | Print audit detections without modifying database |
| `--verbose`, `-v` | Flag | `False` | Detailed per-URL logging |

### Output Example

```text
====================================================================================================
🩺 AUDITORÍA DE CATÁLOGO Y ENLACES EN VIVO
====================================================================================================
Total a auditar: 25 modelos | Modo: Activo con persistencia

  [1/25] 🟢 Orbea Terra H30 (Buycycle) → 200 OK | En Stock | 1.099 € (Sin cambios)
  [2/25] 🟡 Megamo Jakar 20 (Alltricks) → 200 OK | Precio bajó: 1.549 € -> 1.499 € (Actualizado)
  [3/25] 🔴 Conor Kalima (Tuvalum) → TIENDA CERRADA → Marcado fuera de stock
  [4/25] 🔴 Scott Speedster (Wallapop) → Producto vendido / reservado → Marcado fuera de stock

----------------------------------------------------------------------------------------------------
📊 RESUMEN DE AUDITORÍA:
  • Verificados con éxito: 23
  • Sin stock / Desactivados: 2
  • Caídas de precio detectadas: 1
  • Errores 404 / Enlace caído: 0
====================================================================================================
```

---

## 2. Re-Scoring & Spec Normalization Command

Cross-checks specifications against `components_authority.py` and applies the calibrated rubric.

```bash
python3 gravel_tracker.py --re-score [--verbose]
```

### Output Example

```text
====================================================================================================
⚖️ CALIBRACIÓN Y RE-CÁLCULO DE RÚBRICA Y ESPECIFICACIONES
====================================================================================================
Bicicletas procesadas: 444

🛠️ Correcciones Técnicas Aplicadas:
  • Frenos corregidos de "hidráulico" a "mecánico": 14 (ej. Shimano Claris / Tourney falsos hidráulicos)
  • PVPs inflados normalizados a MSRP oficial: 22 (ej. Wallapop con PVP ficticio)
  • Bonificación de Garantía Legal (+5 pts tienda nueva, +3 pts certificada): 189 modelos

📈 Impacto en Tiers:
  • Tier S+: 18 modelos (antes 26, saneados los falsos hidráulicos)
  • Tier S: 42 modelos
  • Tier A: 110 modelos
  • Tier B/C: 274 modelos

✅ Base de datos actualizada con éxito.
====================================================================================================
```

---

## 3. Detailed Inspection Card with Itemized Rubric

```bash
python3 gravel_tracker.py --ficha "Jakar 30"
```

Outputs the itemized breakdown:
```text
Criterios Rúbrica (Calibrada 2026):
  • C1 Frenos:       25.0 / 25  (Shimano GRX 400 Hidráulico verificado)
  • C2 Transmisión:  23.0 / 25  (Shimano GRX 2x10v específico gravel)
  • C3 Cuadro/Horq:  16.0 / 20  (Aluminio hidroformado + Horquilla carbono)
  • C4 Precio/Valor: 18.0 / 20  (999 € vs PVP real 1.248 €)
  • C5 Talla:        10.0 / 10  (Compatible 1.69 m)
  • C6 Garantía:     +5.0 / 5   (Tienda física oficial - 3 años garantía)
Total: 97.0 / 100 | Nota: 9.7 / 10 | Clasificación: Tier S+
```