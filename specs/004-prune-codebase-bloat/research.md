# Phase 0 Research: Prune Codebase Bloat & Over-Engineering

**Feature**: `004-prune-codebase-bloat`
**Date**: 2026-10-10

## Research Findings & Architectural Decisions

### 1. CLI Entry Point Unification
- **Decision**: Refactor `gravel_tracker.py` into a minimal, clean top-level entrypoint that delegates argument parsing and execution directly to `gravel_bot.cli.main()`.
- **Rationale**: Currently, `gravel_tracker.py` contains ~200 lines of manual `if/elif sys.argv[1]` loops that parse flags (`--limit`, `--tienda`, `--presupuesto`, `--audit`, `--re-score`) manually, duplicating the standard `argparse` configuration in `gravel_bot/cli.py`. This introduces drift risk every time a CLI flag is updated.
- **Alternatives Considered**: 
  - Keeping both entry points and keeping them manually synced. Rejected: high cognitive load and code duplication.
  - Deleting `gravel_tracker.py` completely. Rejected: `gravel_tracker.py` is the established root executable expected by users and scripts (`python3 gravel_tracker.py ...`).

### 2. Deletion of Defunct Tuvalum Scraper
- **Decision**: Remove `gravel_bot/scrapers/tuvalum.py` and remove references from `multi_store.py` and `pipeline.py`.
- **Rationale**: Tuvalum has ceased bicycle retail operations and entered liquidation. Querying their domain results in HTTP timeouts or redirected error pages. The budget optimizer already filters out Tuvalum as noise. Removing the scraper saves ~130 lines and avoids dead network traffic.
- **Alternatives Considered**: Leaving a stub scraper that returns an empty list. Rejected: violates YAGNI and Ponytail principles.

### 3. Consolidation of Component Knowledge Base
- **Decision**: Integrate `KNOWN_MODEL_SPECS` and group lookup into `gravel_bot/components_authority.py`, streamlining `gravel_bot/knowledge_base.py` to avoid redundant file I/O on `components_db.json`.
- **Rationale**: `components_authority.py` was established as the authoritative dictionary for components and frame materials. Having a second file (`knowledge_base.py`) reading a JSON file at runtime creates split truth and unnecessary complexity.
- **Alternatives Considered**: Keeping runtime JSON loading for future dynamic additions. Rejected: cycling groups and factory specs are industry constants that change only on annual model releases.

### 4. Sizing Logic Re-use
- **Decision**: Update `is_size_compatible()` in `gravel_bot/budget_optimizer.py` to delegate to `evaluate_size_compatibility_dynamic()` from `gravel_bot/geometry_sizing.py`.
- **Rationale**: Both modules were performing slightly divergent string-matching on size labels. Reusing the dedicated geometry module guarantees identical sizing behavior across the web UI, bot, and budget optimizer.
- **Alternatives Considered**: Duplicating brand-specific sizing tables in `budget_optimizer.py`. Rejected: duplicate code that can drift.

### 5. Test Suite Streamlining
- **Decision**: Verify all unique assertions in `test_bot.py` are incorporated into `test_new_features.py`, then delete `test_bot.py`.
- **Rationale**: `test_bot.py` was the legacy initial test file whose rubric and notifier tests are now thoroughly exercised with higher fidelity in `test_new_features.py` and `test_intensive.py`.
- **Alternatives Considered**: Keeping all three test files. Rejected: running identical tests multiple times slows down feedback with zero added assurance.
