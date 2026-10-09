# Data Model: Budget Bike Optimizer

**Feature**: `001-budget-bike-optimizer`
**Date**: 2026-10-09

## Entities & Schemas

### 1. `BudgetQuery`

Encapsulates user input criteria for finding the optimal gravel bike.

| Field | Type | Required | Default | Description / Validation |
|---|---|:---:|---|---|
| `budget_ceiling` | `float` | Yes | - | Maximum budget in € (must be $> 0$, typically $300 - 10000$) |
| `rider_height_cm` | `int` | No | `169` | Rider height in cm ($140 - 210$) used for sizing derivation |
| `target_size` | `str` | No | Derived | Target nominal frame size (`XS`, `S`, `M`, `L`, `XL`, `51`, `52`...) |
| `channel_filter` | `str` | No | `"all"` | Allowed channels: `"all"`, `"local_madrid"`, `"certified"`, `"outlet"` |
| `include_stretch` | `bool` | No | `True` | Whether to calculate the Smart Stretch (+15%) advisory |

---

### 2. `CleanCandidateBike`

Represents a sanitized, validated complete bicycle candidate after strict noise exclusion.

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Primary key from `bicicletas` table |
| `slug` | `str` | Unique bike slug (e.g. `megamo_jakar_30_2026`) |
| `brand` | `str` | Clean bike brand (e.g. `Megamo`, `Orbea`, `Canyon`) |
| `model` | `str` | Clean model name (e.g. `Jakar 30`) |
| `price` | `float` | Current verified asking price in € |
| `pvp` | `float` | Original or reference PVP price in € |
| `discount_pct` | `float` | Calculated discount: $\frac{\text{PVP} - \text{Price}}{\text{PVP}} \times 100$ |
| `discipline` | `str` | Must be strictly `"gravel"` |
| `frame_material` | `str` | Frame material (e.g. `Aluminio`, `Carbono`) |
| `fork_material` | `str` | Fork material (e.g. `Carbono`, `Aluminio`) |
| `drivetrain` | `str` | Transmission spec (e.g. `Shimano GRX RX400 2x10`) |
| `brake_type` | `str` | Normalized brake type: `hidraulico`, `semihidraulico`, `mecanico` |
| `has_hydraulic_brakes` | `bool` | Boolean flag: True if `brake_type == 'hidraulico'` |
| `has_carbon_fork` | `bool` | Boolean flag: True if fork contains carbon |
| `available_sizes` | `List[str]`| List of verified available sizes |
| `size_compatibility` | `str` | Status for query: `compatible`, `incompatible`, `verificar` |
| `store_name` | `str` | Selling merchant / store name |
| `channel_type` | `str` | Channel classification: `tienda_fisica`, `tienda_online`, `ocasion_certificada`, `particular` |
| `product_url` | `str` | Direct URL to purchase / inspect |
| `rubric_score` | `float` | Total component rubric score ($0.0 - 100.0$) |
| `rubric_nota` | `float` | Normalized note ($0.0 - 10.0$) |
| `rubric_tier` | `str` | Tier rating (`Tier S+`, `Tier S`, `Tier A`, `Tier B`) |
| `vfm_index` | `float` | Value-for-Money index: $\frac{\text{rubric\_score}}{\text{price}} \times 1000$ |

---

### 3. `RecommendationPodio`

Represents the synthesized executive output delivered to the user.

| Field | Type | Description |
|---|---|---|
| `query` | `BudgetQuery` | Echo of the query parameters evaluated |
| `total_candidates_scanned`| `int` | Total database bikes evaluated before filters |
| `valid_candidates_count` | `int` | Total bikes meeting budget, sizing, and noise filters |
| `best_value` | `Optional[CleanCandidateBike]` | #1 Best component quality bike $\le B$ |
| `top_bargain` | `Optional[CleanCandidateBike]` | #2 Highest discount / outlet bargain $\le B$ |
| `smart_stretch` | `Optional[CleanCandidateBike]` | #3 Candidate in $(B, 1.15B]$ with critical component jump |
| `stretch_reason` | `Optional[str]` | Human-readable explanation of why the stretch is worth it |
| `budget_saver` | `Optional[CleanCandidateBike]` | Alternative priced $< 0.85B$ with comparable spec |
| `status` | `str` | `"success"`, `"no_exact_match"`, or `"budget_too_low"` |

---

## State & Data Flow Diagram

```
[User Input (CLI / Telegram)]
           │
           ▼
     BudgetQuery(budget, height, channel)
           │
           ▼
[SQLite Catalog: gravel_madrid.db]
           │
           ▼  (Filter 1: Exclude frames, ebikes, non-gravel, closed shops)
           ▼  (Filter 2: Check size compatibility with height/profile)
           │
  Candidate Set (All valid complete gravel bikes)
     ├── Price <= Budget ─────────► Rank by Score (Max Score -> Best Value)
     │                             Rank by Discount (Max % -> Top Bargain)
     │
     └── Budget < Price <= 1.15*Budget
                                  │ (Check: unlocks Hydraulic brakes or Carbon fork?)
                                  ▼
                             Smart Stretch Candidate
           │
           ▼
   RecommendationPodio
           │
           ▼
[Executive Decision Card Output (Terminal Table / Telegram HTML)]
```