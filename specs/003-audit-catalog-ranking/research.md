# Phase 0 Research: Catalog Freshness, Spec Audit & Ranking Calibration

**Feature**: `003-audit-catalog-ranking`
**Date**: 2026-10-10

## Research Overview

This document resolves the architectural decisions for eliminating catalog staleness, eradicating erroneous specifications (such as fake hydraulic brakes or inflated PVPs), and calibrating the ranking formula with transparent, itemized scoring and buyer protection/warranty weighting.

---

### Decision 1: Authoritative Component Matrix & Ground Truth Dictionary

- **Decision**: Create `gravel_bot/components_authority.py` as an immutable source of truth for gravel bike components, actuation types, and manufacturer MSRP boundaries.
  - **Drivetrain & Brakes Mapping**:
    - `Shimano Claris (R2000)`: Strictly 2x8 mechanical cable disc. Never hydraulic. MSRP 700 € – 950 €.
    - `Shimano Sora (R3000)`: Strictly 2x9 mechanical cable disc. Never hydraulic. MSRP 800 € – 1.050 €.
    - `Shimano Tiagra (4700)`: 2x10 mechanical cable disc (unless explicit RS405 levers). MSRP 950 € – 1.200 €.
    - `Shimano GRX 400`: Strictly 2x10 hydraulic disc. MSRP 1.100 € – 1.450 €.
    - `Shimano GRX 600 / 610`: Strictly 1x11, 2x11, 1x12, 2x12 hydraulic disc. MSRP 1.400 € – 1.950 €.
    - `Shimano GRX 810 / 820`: Strictly 1x11, 2x11, 1x12, 2x12 hydraulic disc. MSRP 1.900 € – 2.800 €.
    - `Microshift Sword`: Strictly 1x10 / 2x10 mechanical disc. Never hydraulic. MSRP 850 € – 1.100 €.
    - `SRAM Apex 1 Mechanical`: Strictly 1x11 mechanical cable disc. MSRP 900 € – 1.200 €.
    - `SRAM Apex 1 / Rival / Force AXS`: Electronic/hydraulic disc. MSRP > 1.300 €.
  - **Frame & Material Heuristic**:
    - Model name patterns `H30`, `H40`, `H50`, `AL`, `ALR`, `Alu`, `HP` map strictly to Aluminum frame + Carbon fork.
    - Model name patterns `M20`, `M30`, `CF`, `SLR`, `C:62`, `Advanced`, `Carbon` map to Carbon frame + Carbon fork.
  - **MSRP Bounds Enforcement**:
    - If a private or outlet listing declares an inflated reference PVP (e.g. 2.500 € for an entry-level Megamo Jakar), it is capped to official manufacturer MSRP + 10% maximum to eliminate phantom discount inflation.
- **Rationale**: Eliminates human and scraper misclassification at the root. If an ad claims "Shimano Claris con frenos hidráulicos", the system corrects it to mechanical brakes with 100% certainty.

---

### Decision 2: Automated Live Freshness Audit Engine

- **Decision**: Implement `gravel_bot/catalog_auditor.py` with multi-tier link and stock health checks:
  1. **HTTP Status Check**: Detect dead URLs (HTTP 404, 410, 500) and flag `en_stock = 0`, setting audit status `enlace_invalido`.
  2. **Merchant Stock Parsers**:
     - Decathlon: Search for text `Agotado`, `No disponible`, or disabled purchase CTA.
     - Specialized stores (Biciescapa, Mammoth, Bikestocks, Buhobike, Fabregues): Detect `Sin stock`, `Agotado temporalmente`.
     - Wallapop: Detect `Reservado`, `Vendido`, `Este producto ya no está disponible`.
     - Tuvalum: Mark 100% of remaining listings inactive due to merchant liquidation.
  3. **Price Drift Reconciliation**: Extract the live asking price from HTML. If it differs from `precio_oferta`, record a price update in `historial_precios` and update the catalog row.
  4. **Domain Rate-Limiting**: Apply randomized delay (0.4s to 0.9s) per domain to avoid triggering WAF / IP blocks.
- **Rationale**: Guarantees that every bike presented in the top recommendations is truly in stock and buyable at the shown price.

---

### Decision 3: Calibrated Scoring Rubric with Buyer Protection & Itemized Breakdown

- **Decision**: Update `gravel_bot/evaluator.py` to produce an itemized score card and incorporate purchasing channel reliability:
  - **C1: Frenos (0–25 pts)**: Hidráulico = 25, Semihidráulico/Doble pistón = 16, Mecánico mono-pistón = 10.
  - **C2: Transmisión (0–25 pts)**: Dedicated Gravel 2x11/2x12 = 25, GRX 2x10 = 23, 1x11/1x12 Clutch = 20, 1x10/2x9 = 15, Entry 2x8 = 10.
  - **C3: Cuadro & Horquilla (0–20 pts)**: Carbono completo = 20, Aluminio + Horquilla Carbono = 16, Solo Aluminio = 8.
  - **C4: Relación Calidad-Precio (0–20 pts)**: Normalizado por precio real contra PVP verificado y percentil de mercado.
  - **C5: Talla (0–10 pts)**: Compatible = 10, Dudosa = 5, Incompatible = 0.
  - **C6: Factor Canal & Garantía (0–5 pts bonus)**:
    - Tienda oficial / nueva (3 años de garantía oficial): **+5 pts**.
    - Segunda mano certificada (Buycycle con revisión/garantía 1 año): **+3 pts**.
    - Particular (Wallapop sin garantía legal): **+0 pts** (más penalización de -2 pts si el PVP declarado era ficticio).
  - **Itemized Breakdown Dictionary**:
    ```python
    {
      "c1_frenos": 25.0,
      "c2_transmision": 23.0,
      "c3_cuadro": 16.0,
      "c4_precio": 18.0,
      "c5_talla": 10.0,
      "c6_canal_garantia": 5.0,
      "total_score": 97.0,
      "nota_10": 9.7,
      "tier": "Tier S+",
      "justificacion": ["Frenos hidráulicos Shimano GRX", "3 años de garantía oficial en tienda"]
    }
    ```
- **Rationale**: Restores justice to the ranking. A brand-new bike with 3-year warranty and consumer protection is objectively a safer, higher-value purchase than an uninspected private bike for a negligible price difference.

---

### Decision 4: CLI Commands & Badge Integration

- **Decision**: Add unified commands in `gravel_tracker.py`:
  - `python3 gravel_tracker.py --audit [--limit N]`: Runs the live stock/price freshness audit.
  - `python3 gravel_tracker.py --re-score`: Re-evaluates 100% of catalog entries against the authoritative component matrix and calibrated rubric.
  - Add `fecha_auditoria` and `audit_status` (`verificado`, `pendiente`, `sin_stock`, `enlace_caido`) in `bicicletas` schema.
  - Display verification chips in Web (`🟢 Verificado`) and Telegram bot.