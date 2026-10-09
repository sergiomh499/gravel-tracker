# Implementation Plan: Catalog Freshness, Spec Audit & Ranking Calibration

**Branch**: `003-audit-catalog-ranking` | **Date**: 2026-10-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-audit-catalog-ranking/spec.md`

## Summary

This feature resolves catalog staleness, technical classification errors (such as false hydraulic brakes or fabricated discounts), and ranking opacity. It implements an Authoritative Component Matrix (`gravel_bot/components_authority.py`) acting as a ground-truth dictionary, an Automated Live Freshness Audit Engine (`gravel_bot/catalog_auditor.py`) to verify stock and detect price changes, and a Calibrated Scoring Rubric (`gravel_bot/evaluator.py`) featuring itemized score cards (C1 to C6) with buyer protection and legal warranty weighting.

## Technical Context

**Language/Version**: Python 3.11+ (Standard Library only)

**Primary Dependencies**: Zero external pip dependencies (strictly Python stdlib: `sqlite3`, `urllib.request`, `re`, `json`, `math`, `time`)

**Storage**: SQLite (`gravel_madrid.db`), extending `bicicletas` with `fecha_auditoria`, `audit_status`, and `c6_garantia`

**Testing**: Python `unittest` suite (`test_new_features.py`)

**Target Platform**: Linux (x86_64), POSIX, and automated GitHub Actions runners

**Project Type**: Data Verification Engine, Domain Truth Table, and Calibrated Evaluation Rubric

**Performance Goals**: $< 1.5\text{ s}$ to re-score and sanitize 100% of catalog rows (444+ bikes); live audit handles $\ge 20$ listings/min

**Constraints**: Pure stdlib architecture, 100% backward compatibility with CLI and Telegram Bot

**Scale/Scope**: 444 active catalog rows, 17 scraping sources, multi-user Telegram persistence

## Constitution Check

*GATE: Passed before Phase 0 research. Re-evaluated post Phase 1 design.*

- **Principle I: Library-First**: The component truth table and audit engine are encapsulated in standalone library modules (`components_authority.py`, `catalog_auditor.py`) decoupled from CLI presentation.
- **Principle II: CLI Interface**: Full functionality exposed via `gravel_tracker.py --audit` and `gravel_tracker.py --re-score`.
- **Principle III: Simplicity & Ponytail**: Zero external pip bloat. Reuses existing SQLite connection pools and standard `urllib.request`.
- **Principle IV: Observability**: Clear progress logs during audit runs and itemized mathematical scorecards for every bicycle.

## Project Structure

### Documentation (this feature)

```text
specs/003-audit-catalog-ranking/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Technical research & decisions
├── data-model.md        # Component authority & audit schemas
├── quickstart.md        # Runnable verification guide
├── contracts/
│   └── cli-contract.md  # CLI flags and outputs
└── checklists/
    └── requirements.md  # Quality verification checklist
```

### Source Code Layout

```text
gravel_bot/
├── components_authority.py  # [NEW] Canonical group matrix, actuation truth, and MSRP bounds
├── catalog_auditor.py       # [NEW] Multi-tier live URL & stock verification engine
├── evaluator.py             # [UPDATED] Calibrated rubric with C1..C6 itemized breakdown
├── db.py                    # [UPDATED] Schema migrations (fecha_auditoria, audit_status)
├── budget_optimizer.py      # [UPDATED] Incorporates verified specs and warranty bonus
├── cli.py                   # [UPDATED] CLI handlers for --audit and --re-score
└── web_server.py            # [UPDATED] Exposes verification badges and itemized score cards

gravel_tracker.py            # Unified CLI entrypoint (--audit, --re-score)
test_new_features.py         # Test validation suite
```

**Structure Decision**: Clean additions in `gravel_bot/` maintaining the single modular package structure.

## Complexity Tracking

*No constitution violations. Zero external dependencies.*