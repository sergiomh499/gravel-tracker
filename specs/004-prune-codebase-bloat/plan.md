# Implementation Plan: Prune Codebase Bloat & Over-Engineering

**Branch**: `004-prune-codebase-bloat` | **Date**: 2026-10-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-prune-codebase-bloat/spec.md`

## Summary

This feature executes the Ponytail recommendations to eliminate over-engineering and dead weight:
1. Unifies `gravel_tracker.py` into a thin delegator to `gravel_bot.cli.main()`.
2. Deletes the defunct `tuvalum.py` scraper and cleans pipeline references.
3. Streamlines `knowledge_base.py` and consolidates component models into `components_authority.py`.
4. Refactors `budget_optimizer.py` to reuse `geometry_sizing.py`.
5. Consolidates legacy assertions from `test_bot.py` into `test_new_features.py` and removes redundant test files.

## Technical Context

- **Language**: Python 3.11+
- **Dependencies**: Python standard library only (`argparse`, `sqlite3`, `dataclasses`, `unittest`, `urllib`).
- **Target Files**:
  - `gravel_tracker.py` (simplify from ~290 lines to ~35 lines)
  - `gravel_bot/cli.py` (ensure alias support for `--presupuesto`, `--audit`, `--re-score`, etc.)
  - `gravel_bot/scrapers/tuvalum.py` (delete)
  - `gravel_bot/scrapers/multi_store.py` (remove Tuvalum reference)
  - `gravel_bot/scrapers/store_directory.py` (mark Tuvalum as inactive / remove)
  - `gravel_bot/budget_optimizer.py` (reuse `geometry_sizing.py`)
  - `test_bot.py` (delete after merging unique checks)
  - `test_new_features.py` (verify full coverage)

## Constitution Check

- *Principle I (Library-First)*: Code remains modular within `gravel_bot`.
- *Principle II (CLI Interface)*: All functionality accessible via CLI.
- *Principle III (Test-First & Regression Defense)*: Test suite must remain 100% passing.
- *Ponytail (Deletion over Addition)*: Net reduction of >450 lines of duplicate code.

## Complexity Tracking

*Zero new dependencies. Net code reduction: -450+ lines.*
