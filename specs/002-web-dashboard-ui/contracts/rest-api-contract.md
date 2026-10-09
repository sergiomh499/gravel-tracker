# REST API Contract: Lightweight Interactive Web Dashboard

**Feature**: `002-web-dashboard-ui`
**Service**: `gravel_bot/web_server.py`
**Default Address**: `http://127.0.0.1:8080`

---

## Endpoints

### 1. `GET /`
Serves the responsive single-page web dashboard application (`index.html`).

- **Headers**: `Content-Type: text/html; charset=utf-8`
- **Response**: HTML5 document with embedded styling and JavaScript logic.

---

### 2. `GET /api/bikes`
Retrieves all sanitized, active gravel bikes available in the SQLite catalog.

- **Query Parameters**: None (client filters locally for 60fps responsiveness)
- **Headers**: `Content-Type: application/json; charset=utf-8`
- **Response Schema**:
  ```json
  {
    "status": "success",
    "count": 142,
    "timestamp": "2026-10-09T20:00:00",
    "bikes": [
      {
        "id": 943,
        "slug": "bicicleta_gravel_megamo_jakar_30_2024",
        "brand": "Megamo",
        "model": "Gravel Megamo Jakar 30 (2024)",
        "price": 790.0,
        "pvp": 1066.5,
        "discount_pct": 25.9,
        "discipline": "gravel",
        "frame_material": "Carbono Toray High Modulus",
        "fork_material": "Carbono Disc",
        "drivetrain": "Shimano GRX RX-400 (2x10) 2x10",
        "brake_type": "hidraulico",
        "has_hydraulic_brakes": true,
        "has_carbon_fork": true,
        "available_sizes": ["S (52 cm)"],
        "size_compatibility": "S (52 cm)",
        "store_name": "Wallapop (Particulares Madrid 25km)",
        "channel_type": "particular",
        "product_url": "https://...",
        "rubric_score": 100.0,
        "rubric_nota": 10.0,
        "rubric_tier": "Tier S+",
        "vfm_index": 126.58
      }
    ]
  }
  ```

---

### 3. `GET /api/recommend`
Generates the executive recommendation podio for a specified budget threshold.

- **Query Parameters**:
  - `budget` (required, float): Budget ceiling in € (e.g. `1000`)
  - `height` (optional, int): Rider height in cm (default: `169`)
  - `size` (optional, string): Nominal size filter (e.g. `S`)
  - `channel` (optional, string): Filter channel (`all`, `local_madrid`, `certified`)
  - `stretch` (optional, bool): Whether to calculate Smart Stretch (default: `true`)
- **Headers**: `Content-Type: application/json; charset=utf-8`
- **Response Schema**:
  ```json
  {
    "status": "success",
    "budget": 1000.0,
    "best_value": { "brand": "Megamo", "model": "Jakar 30", "price": 790.0, "rubric_tier": "Tier S+", ... },
    "top_bargain": { "brand": "BH", "model": "Gravelx Alu 1.0", "price": 999.0, ... },
    "smart_stretch": null,
    "stretch_reason": null,
    "budget_saver": null
  }
  ```

---

### 4. `GET /api/stats`
Provides aggregate metrics for the dashboard header.

- **Response Schema**:
  ```json
  {
    "status": "success",
    "total_bikes": 444,
    "active_gravel_bikes": 142,
    "min_price": 500.0,
    "max_price": 8900.0,
    "avg_price": 1640.5
  }
  ```