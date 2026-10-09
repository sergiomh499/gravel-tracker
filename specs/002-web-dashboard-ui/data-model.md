# Data Model: Lightweight Interactive Web Dashboard

**Feature**: `002-web-dashboard-ui`
**Date**: 2026-10-09

## Entities & Schemas

### 1. `ClientCatalogState` (Frontend State)

Represents the reactive client-side application state held in the browser's JavaScript runtime.

| Field | Type | Default | Description |
|---|---|---|---|
| `all_bikes` | `Array<CleanCandidateBike>` | `[]` | Complete sanitized catalog loaded from `/api/bikes` |
| `filtered_bikes` | `Array<CleanCandidateBike>` | `[]` | Active subset meeting all selected filters |
| `active_budget` | `number` | `1000` | Current position of the budget slider in € |
| `active_height_cm` | `number` | `169` | Rider height parameter for sizing evaluation |
| `active_size` | `string` | `"all"` | Target nominal frame size filter (`"all"`, `"XS"`, `"S"`, `"M"`, `"L"`) |
| `active_drivetrain`| `string` | `"all"` | Transmission filter: `"all"`, `"2x"`, `"1x"` |
| `active_brakes` | `string` | `"all"` | Brake filter: `"all"`, `"hidraulico"`, `"mecanico"` |
| `active_channel` | `string` | `"all"` | Channel filter: `"all"`, `"tienda_fisica"`, `"ocasion_certificada"` |
| `search_query` | `string` | `""` | Search text matched against brand and model names |
| `compare_selection`| `Array<number>` | `[]` | List of selected bike IDs for 1v1 comparison (max 2) |

---

### 2. `ComparisonPair`

Represents the two bicycles selected for side-by-side technical evaluation.

| Field | Type | Description |
|---|---|---|
| `bike_a` | `CleanCandidateBike` | First selected bicycle |
| `bike_b` | `CleanCandidateBike` | Second selected bicycle |
| `advantages_a` | `Array<string>` | Highlights where Bike A beats Bike B (e.g. "Frenos Hidráulicos", "PVP con 25% descuento") |
| `advantages_b` | `Array<string>` | Highlights where Bike B beats Bike A (e.g. "Transmisión 2x11v", "Horquilla Carbono") |
| `price_difference` | `number` | $\text{Price}_A - \text{Price}_B$ |

---

### 3. `WebApiResponse` (API Envelopes)

Standardized JSON serialization for server endpoints.

```typescript
interface ApiResponse<T> {
  status: "success" | "error";
  data?: T;
  message?: string;
  count?: number;
  timestamp: string;
}
```

- **`/api/bikes`**: Returns `ApiResponse<CleanCandidateBike[]>`
- **`/api/recommend`**: Returns `ApiResponse<RecommendationPodio>`
- **`/api/stats`**: Returns `ApiResponse<{ total_bikes: number, avg_price: number, min_price: number, max_price: number }>`