# Implementation Plan: Budget Bike Optimizer

**Branch**: `001-budget-bike-optimizer` | **Date**: 2026-10-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-budget-bike-optimizer/spec.md`

## Summary

The Budget Bike Optimizer professionalizes the project into a razor-sharp, zero-noise decision engine. Instead of dumping overwhelming lists of hundreds of uncurated rows (including bare frames, motorized e-bikes, and defunct merchants), it provides a single-command executive recommendation ("El Podio de mi Presupuesto"): the #1 Best Absolute Value within budget, the #2 Top Discounted Bargain, and an optional #3 Smart Stretch (+15% max) that unlocks critical component jumps (such as hydraulic disc brakes). It is delivered through an extensible library module (`gravel_bot/budget_optimizer.py`), backward-compatible CLI flags in `gravel_tracker.py`, and interactive Telegram bot commands with inline keyboards.

## Technical Context

**Language/Version**: Python 3.11+ (standard library only)

**Primary Dependencies**: Zero external third-party dependencies (strictly Python stdlib: `sqlite3`, `urllib.request`, `json`, `re`, `math`, `sys`)

**Storage**: SQLite (`gravel_madrid.db`), utilizing existing tables (`bicicletas`, `perfiles_ciclista`, `tiendas`) with zero breaking schema migrations

**Testing**: Python `unittest` suite (`test_new_features.py` and dedicated test cases)

**Target Platform**: Linux (x86_64), POSIX, and headless GitHub Actions runners

**Project Type**: Standalone Python Domain Library, CLI tool, and Telegram Bot Polling Service

**Performance Goals**: Recommendation generation latency $< 2.0$ seconds across 1.000+ catalog rows

**Constraints**: Zero avoidable allocation, pure stdlib architecture, 100% backward compatibility with existing CLI arguments and bot commands

**Scale/Scope**: ~1.200 active catalog bikes, 17 scraping sources, multi-user Telegram persistence

## Constitution Check

*GATE: Passed before Phase 0 research. Re-evaluated post Phase 1 design.*

- **Principle I: Library-First**: The core recommendation algorithm is encapsulated in `gravel_bot/budget_optimizer.py`, completely decoupled from presentation logic (CLI/Telegram).
- **Principle II: CLI Interface**: Full functionality exposed via `gravel_tracker.py --presupuesto [EUR]` supporting both formatted terminal output and `--json` serialization.
- **Principle III: Test-First & Validation**: Concrete end-to-end scenarios defined in `quickstart.md` and runnable test scripts.
- **Principle IV: Simplicity & Ponytail**: Minimal diff, zero external pip packages, native SQLite queries, and surgical noise filtration without complex abstraction layers.

## Project Structure

### Documentation (this feature)

```text
specs/001-budget-bike-optimizer/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 technical research & decisions
├── data-model.md        # Phase 1 data entities and schemas
├── quickstart.md        # Phase 1 runnable validation scenarios
├── contracts/           # Phase 1 interface contracts
│   ├── cli-contract.md
│   └── telegram-contract.md
└── checklists/
    └── requirements.md  # Quality verification checklist
```

### Source Code Layout

```text
gravel_bot/
├── budget_optimizer.py      # [NEW] Core optimization engine & executive card builder
├── evaluator.py             # Existing component rubric & detection heuristics
├── db.py                    # Database queries (fetch candidate bikes, user profile)
├── deal_detector.py         # Discount detection & price drop tracking
├── bike_inspector.py        # Bike card formatting & comparison logic
├── bot_service.py           # Telegram bot commands (/presupuesto handler & keyboards)
└── cli.py                   # CLI subcommands & formatting

gravel_tracker.py            # Unified entrypoint CLI (--presupuesto, --recomendar)
test_new_features.py         # Test validation suite
```

**Structure Decision**: Single modular project within the existing `gravel_bot/` package. The new logic is housed in `gravel_bot/budget_optimizer.py` and cleanly called by `gravel_tracker.py` and `gravel_bot/bot_service.py`.

## Complexity Tracking

*No constitution violations or unwarranted abstractions. All gates passed.*