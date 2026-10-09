# Quickstart Validation Guide: Budget Bike Optimizer

**Feature**: `001-budget-bike-optimizer`
**Date**: 2026-10-09

## Prerequisites

- Python 3.11+ installed.
- SQLite database `gravel_madrid.db` present in repository root (or initialized via `python3 gravel_tracker.py --daemon`).

---

## Validation Scenario 1: Standard Budget Search (1.000 €)

### Command
```bash
python3 gravel_tracker.py --presupuesto 1000
```

### Expected Outcome
- The output displays the executive 3-card podio.
- All candidate bikes are strictly complete gravel bicycles (no bare frames, no e-bikes, no road/MTB).
- Primary bike (#1) asking price is $\le 1.000\text{ €}$.
- Sizing matches the rider profile (default 1,69 m / Talla S).
- A valid purchase URL is printed for each recommended model.
- Execution completes in $< 2$ seconds.

---

## Validation Scenario 2: Noise Filtration Verification

### Command
```bash
python3 -c "
from gravel_bot.budget_optimizer import optimize_for_budget
res = optimize_for_budget(budget=1500, height_cm=169)
# Assert no frames or ebikes leaked
for bike in [res.best_value, res.top_bargain, res.smart_stretch]:
    if bike:
        assert 'cuadro' not in bike.model.lower() and 'cuadro' not in bike.brand.lower(), 'Leaked frame!'
        assert 'ebike' not in bike.model.lower() and bike.discipline == 'gravel', 'Leaked ebike!'
        assert 'tuvalum' not in bike.store_name.lower(), 'Leaked closed shop!'
print('✅ Noise exclusion passed: 0 frames, 0 ebikes, 0 closed shops!')
"
```

### Expected Outcome
- Console prints `✅ Noise exclusion passed: 0 frames, 0 ebikes, 0 closed shops!`.

---

## Validation Scenario 3: Smart Stretch Trigger

### Command
```bash
python3 gravel_tracker.py --presupuesto 950
```

### Expected Outcome
- Primary option has price $\le 950\text{ €}$.
- If a bike priced between $951\text{ €}$ and $1.092\text{ €}$ ($+15\%$) provides hydraulic brakes or superior transmission, the Smart Stretch block is displayed with the exact technical justification.

---

## Validation Scenario 4: JSON Output for Integration / Automation

### Command
```bash
python3 gravel_tracker.py --presupuesto 1200 --json
```

### Expected Outcome
- Valid JSON string parsed on stdout.
- Top-level keys: `"status"`, `"budget"`, `"best_value"`, `"top_bargain"`.
- Clean programmatic structure conformant with `contracts/cli-contract.md`.