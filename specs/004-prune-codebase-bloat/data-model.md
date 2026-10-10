# Data Model & Architectural Consolidations: Prune Codebase Bloat

**Feature**: `004-prune-codebase-bloat`
**Date**: 2026-10-10

## Architectural Adjustments & Consolidations

### 1. Unified CLI Entry Architecture

```
User / Shell Invocation
       │
       ▼
gravel_tracker.py (Lightweight Entrypoint: ~25 lines)
       │
       ▼
gravel_bot.cli.main() (Centralized argparse Dispatcher)
       │
       ├─► cmd_list()
       ├─► cmd_deals()
       ├─► cmd_budget()
       ├─► cmd_audit()
       ├─► cmd_rescore()
       ├─► cmd_web()
       └─► cmd_scan()
```

### 2. Module Removals & Simplifications

| Entity / Module | Action | Justification |
|---|---|---|
| `gravel_bot/scrapers/tuvalum.py` | **DELETE** | Marketplace liquidated; zero functional value; avoids dead HTTP calls. |
| `test_bot.py` | **DELETE (Consolidate)** | Legacy test suite completely subsumed by `test_new_features.py`. |
| `gravel_tracker.py` (manual parser) | **REPLACE** | Replace manual `sys.argv` matching with `gravel_bot.cli.main()`. |
| `gravel_bot/budget_optimizer.py:is_size_compatible` | **REFACTOR** | Delegate to `gravel_bot.geometry_sizing.evaluate_size_compatibility_dynamic()`. |
| `gravel_bot/knowledge_base.py` | **STREAMLINE** | Unify factory model specs with `components_authority.py`. |

### 3. Sizing Compatibility Contract Alignment

`budget_optimizer.is_size_compatible()` aligns with `geometry_sizing`:
- Input: `(marca: str, modelo: str, altura_cm: int, available_sizes: List[str])`
- Output: `Tuple[bool, str, str]` (`compatible`, `recommended_size`, `explanation`)
- Ensures identical size filtering in the optimizer, bot, and web API.
