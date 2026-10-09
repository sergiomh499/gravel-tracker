# Data Model: Catalog Freshness, Spec Audit & Ranking Calibration

**Feature**: `003-audit-catalog-ranking`
**Date**: 2026-10-10

## Entities & Schemas

### 1. `AuthoritativeGroupSpec`

Represents canonical ground truth for cycling components.

| Field | Type | Description |
|---|---|---|
| `group_id` | `str` | Normalized identifier (e.g. `shimano_grx_400`, `shimano_claris_r2000`) |
| `family` | `str` | Brand / Family (`Shimano GRX`, `Shimano Road`, `Microshift`, `SRAM Apex`) |
| `speed_count` | `int` | Total rear cogs (e.g. `8`, `9`, `10`, `11`, `12`) |
| `chainrings` | `str` | Chainring options (`"1x"`, `"2x"`, `"1x/2x"`) |
| `actuation` | `str` | Actuation type: `"hidraulico"`, `"mecanico_doble"`, `"mecanico_mono"` |
| `is_hydraulic` | `bool` | True if group levers and calipers are hydraulic |
| `msrp_range` | `Tuple[float, float]` | Realistic manufacturer MSRP bracket in € for complete bikes |
| `tier_baseline` | `str` | Default component quality tier (`"Tier S+"`, `"Tier S"`, `"Tier A"`, `"Tier B"`) |

---

### 2. `AuditResultRecord`

Represents the audit result when verifying a live product listing.

| Field | Type | Description |
|---|---|---|
| `bike_id` | `int` | Foreign key to `bicicletas` table |
| `checked_at` | `str` | ISO 8601 timestamp of verification |
| `http_status` | `int` | HTTP response code (200, 404, 410, etc.) |
| `live_price` | `Optional[float]` | Asking price extracted live from merchant page |
| `price_changed` | `bool` | True if live price differed from database `precio_oferta` |
| `in_stock` | `bool` | Stock availability verified from HTML selectors |
| `specs_corrected` | `Dict[str, Any]` | Dictionary of fields auto-corrected (e.g. `brake_type`, `pvp`) |
| `status` | `str` | Status code: `"verificado"`, `"sin_stock"`, `"enlace_caido"`, `"error_bloqueo"` |

---

### 3. `ItemizedScoreBreakdown`

Transparent rubric points decomposition.

| Field | Range | Description |
|---|---|---|
| `c1_frenos` | 0 – 25 | Points for brake system quality (hydraulic vs mechanical) |
| `c2_transmision` | 0 – 25 | Points for drivetrain speeds, clutch, and gear range |
| `c3_cuadro` | 0 – 20 | Points for frame and fork materials (carbon vs aluminum) |
| `c4_precio` | 0 – 20 | Points for price-to-quality value against market benchmarks |
| `c5_talla` | 0 – 10 | Points for rider size compatibility |
| `c6_garantia` | 0 – 5 | Bonus points for store warranty and buyer protection (channel) |
| `total_score` | 0 – 105 | Composite score (capped at 100) |
| `nota_10` | 0.0 – 10.0 | Normalized rating out of 10 |
| `tier` | `str` | Final tier: `Tier S+` (>=90), `Tier S` (>=80), `Tier A` (>=65), `Tier B` (<65) |
| `justificacion` | `List[str]` | Plain-language reasons supporting the score |

---

### 4. Database Schema Extensions (`bicicletas` table)

Idempotent `ALTER TABLE` additions:
- `fecha_auditoria TEXT`: Last successful audit timestamp.
- `audit_status TEXT DEFAULT 'pendiente'`: `"verificado"`, `"pendiente"`, `"sin_stock"`, `"enlace_caido"`.
- `c6_garantia REAL DEFAULT 0.0`: Stored warranty bonus points.
- `especificaciones_verificadas INTEGER DEFAULT 0`: 1 if verified against authority matrix.