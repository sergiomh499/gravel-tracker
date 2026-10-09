# Phase 0 Research: Budget Bike Optimizer

**Feature**: `001-budget-bike-optimizer`
**Date**: 2026-10-09

## Research Overview

This document resolves the key technical decisions for implementing the Budget Bike Optimizer feature in `gravel-tracker`. It establishes the ranking mathematics, strict noise filtration heuristics, "Smart Stretch" detection, and delivery mechanisms across CLI and Telegram.

---

### Decision 1: Value-for-Money (VfM) Scoring & Ranking Model

- **Decision**: Implement a dual-component ranking metric:
  $$\text{VfM Index} = \left(\frac{\text{Score}_{\text{rubrica}}}{\text{Price}_{\text{real}}}\right) \times 1000$$
  The primary recommendation for budget ceiling $B$ is selected via:
  1. **Candidate Pool**: Active complete gravel bikes with verified compatible size where $\text{Price}_{\text{real}} \le B$.
  2. **Primary Winner (#1 Mejor Compra Absoluta)**: The candidate that maximizes $\text{Score}_{\text{rubrica}}$ within $B$. If scores are within 2 points, tie-breaker goes to higher $\text{VfM Index}$ (cheaper price).
  3. **Bargain Winner (#2 Chollo / Mayor Descuento)**: The candidate with the highest nominal discount percentage $\ge 20\%$ or absolute savings $\ge 150\text{ €}$ that meets minimum component quality ($\text{Score} \ge 7.0$).
- **Rationale**: Cyclists asking "what is the best bike for 1.000 €" do not just want the cheapest possible bike (which is often poorly equipped with mechanical disc brakes or steel forks); they want the absolute best machine their money can buy. Pairing the top absolute quality bike with the steepest discounted bargain offers two distinct, valuable choices.
- **Alternatives Considered**:
  - *Pure Price Ordering (Lowest first)*: Rejected because a 500 € bike with inferior Claris and mechanical brakes is not a good purchase if the user has 1.000 € to spend.
  - *Pure Rubric Ordering without budget constraint*: Rejected because it returns bikes far beyond the user's spending limit.

---

### Decision 2: Deterministic Noise & Phantom Deal Filtration

- **Decision**: Centralize filtering logic in a dedicated module (`gravel_bot/budget_optimizer.py`) with strict rejection predicates:
  1. **Bare Frames**: Exclude if title or slug matches `\b(cuadro|frameset|frame)\b` unless explicitly identified as a complete bicycle.
  2. **Motorized / E-Bikes**: Exclude if discipline is `ebike` or title contains `ebike`, `e-bike`, `eléctrica`, `powerfly`, `rise`, `trance`, `marlin+`, `patron`, `lumen`.
  3. **Non-Gravel Disciplines**: Exclude if discipline is `carretera`, `mtb`, `enduro`, `infantil`, `junior`, `fitness`.
  4. **Closed / Liquidated Merchants**: Exclude stores whose name or status contains `CERRADA`, `Liquidación`, or known bankrupt entities (e.g. Tuvalum).
  5. **Size Incompatibility**: When the rider specifies height or nominal size, discard records flagged as `No compatible` or whose size list excludes the target size.
  6. **Stale / Zero-PVP Anomaly**: Discard or auto-repair records with missing price or price $< 150\text{ €}$ (unless verified frameset/part, which is already excluded).
- **Rationale**: The catalog currently contains artifacts like "Kross Cuadro 350 €" (a bare frame given 9.2 points) and 10.000 € e-bikes. Eliminating this noise before evaluation is mandatory for professional credibility and trust.
- **Alternatives Considered**:
  - *Patching scrapers individually*: Scrapers can break or ingest legacy data; defensive centralized filtration at the query/domain layer guarantees zero leakages regardless of scraper idiosyncrasies.

---

### Decision 3: "Smart Stretch" Advisory Logic

- **Decision**: Define the "Smart Stretch" candidate as a bike located in the price bracket $(B, B \times 1.15]$ (maximum +15% over budget, capped at $+150\text{ €}$) that achieves a *critical specification threshold* not present in the within-budget winner:
  - Critical thresholds:
    - Brakes: Mechanical / Semihydraulic $\rightarrow$ Full Hydraulic (e.g., Shimano GRX RX400/600/800 or SRAM Apex/Rival Hydraulic).
    - Fork/Frame: Full Aluminum $\rightarrow$ Carbon Fork or Full Carbon Frame.
    - Tier jump: Tier A / B $\rightarrow$ Tier S / S+.
    - Drivetrain: Entry 2x8/2x9 or 1x9 $\rightarrow$ Dedicated Gravel 2x10/2x11 or 1x11/1x12 with clutch.
  If no candidate in that $+15\%$ window offers a critical threshold leap, no Smart Stretch is suggested (avoids pointless upselling).
- **Rationale**: Bike pricing often clusters around component cliffs (e.g., 900 € bikes usually have mechanical brakes, while 1.050 € unlocks hydraulic GRX). Explaining this exact spec leap empowers the user to make a conscious, regret-free choice.
- **Alternatives Considered**:
  - *Always recommending a more expensive bike*: Annoying and counterproductive if the user has a hard budget ceiling.

---

### Decision 4: Architecture & Integration in Existing System

- **Decision**:
  1. Add engine core: `gravel_bot/budget_optimizer.py` exposing clean functions:
     - `optimize_for_budget(budget, height_cm=None, size=None, channel=None, limit=3)`
     - `format_budget_recommendation_card(recommendation_result, format="text"|"html")`
  2. CLI Integration: Add `--presupuesto` / `--recomendar` flags in `gravel_tracker.py` and `gravel_bot/cli.py`.
  3. Telegram Bot Integration: Add `/presupuesto` command, handle natural numbers (e.g. typing "1000" or "/presupuesto 1000"), and integrate quick-budget inline buttons in the Telegram UI.
  4. Storage/Profile: Read default rider height and budget from `perfiles_ciclista` (or fallback to `RIDER_PROFILE` in `config.py`), with auto-persistence when user specifies custom values.
- **Rationale**: Follows the existing modular Python stdlib architecture with zero external dependencies, seamless CLI backward compatibility, and instant Telegram responsiveness.
- **Alternatives Considered**:
  - *Creating a separate CLI executable*: Fragmenting the tool into multiple scripts confuses users. `gravel_tracker.py` remains the single entry point.