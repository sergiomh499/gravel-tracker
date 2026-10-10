# Feature Specification: Prune Codebase Bloat & Over-Engineering

**Feature Branch**: `004-prune-codebase-bloat`
**Created**: 2026-10-10
**Status**: Draft
**Input**: User description: "corrige lo auditado por ponytail"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unified CLI Entry Point & Parameter Parity (Priority: P1)

As a cyclist using the command line, I want `gravel_tracker.py` to remain the single, responsive entry point with full parameter support, but without hundreds of lines of duplicate manual argument parsing duplicating `gravel_bot.cli`.

**Why this priority**: Eliminates the largest source of maintenance debt and risk of CLI option drift between `gravel_tracker.py` and `gravel_bot.cli`.

**Independent Test**: Execute `python3 gravel_tracker.py --presupuesto 1000`, `python3 gravel_tracker.py --audit --limit 5`, `python3 gravel_tracker.py --ficha "Jakar 30"` and verify all subcommands and flags behave identically to `gravel_bot.cli`.

**Acceptance Scenarios**:
1. Given a user running `python3 gravel_tracker.py [command] [args]`, the call routes directly through `gravel_bot.cli.main()` with zero loss of options or flags.
2. Given a user running `gravel_tracker.py` without arguments, it defaults to ranking and deals display.

---

### User Story 2 - Deletion of Defunct Scrapers & Unification of Component Truth (Priority: P1)

As an automated pipeline runner, I want obsolete and dead scrapers (e.g. Tuvalum marketplace, which is bankrupt and liquidated) deleted, and component data lookup unified within `components_authority.py` instead of maintaining duplicate runtime files.

**Why this priority**: Prevents wasted network cycles, timeouts, and cognitive overhead maintaining code for businesses that no longer exist, while ensuring single-source-of-truth for component specifications.

**Independent Test**: Verify `scrapers/tuvalum.py` is removed, the multi-store scraper lists no longer query defunct portals, and component specs resolve seamlessly from `components_authority.py`.

**Acceptance Scenarios**:
1. Scraper directory contains only active, operative store scrapers.
2. The model specifications and group resolutions route cleanly through `components_authority.py` without depending on external unparsed JSON loaders.

---

### User Story 3 - Unification of Sizing Logic & Test Suite Consolidation (Priority: P2)

As a developer and continuous integration runner, I want a single source of truth for rider sizing calculations and a consolidated, deterministic test suite without duplicate legacy suites.

**Why this priority**: Guarantees sizing consistency across CLI, web, and Telegram bot, while keeping test execution fast and lean.

**Independent Test**: Run `python3 -m unittest test_new_features.py` and verify all legacy assertions from `test_bot.py` are preserved, sizing calculations in `budget_optimizer.py` use `geometry_sizing.py`, and test execution finishes in seconds with zero regressions.

**Acceptance Scenarios**:
1. `budget_optimizer.py` delegates sizing compatibility evaluation directly to `geometry_sizing.evaluate_size_compatibility_dynamic()`.
2. Unique assertions from `test_bot.py` are integrated into `test_new_features.py`, and redundant test files are pruned.

---

## Functional Requirements *(mandatory)*

- **FR-001**: `gravel_tracker.py` MUST be a lightweight wrapper delegating execution to `gravel_bot.cli.main()`, preserving backward compatibility for positional and flagged arguments.
- **FR-002**: Defunct scraper `gravel_bot/scrapers/tuvalum.py` MUST be deleted and removed from scraper directory lists and pipeline references.
- **FR-003**: Redundant runtime loading in `gravel_bot/knowledge_base.py` MUST be pruned, routing component model resolutions through the authoritative in-code dictionary in `gravel_bot/components_authority.py`.
- **FR-004**: Size compatibility logic in `gravel_bot/budget_optimizer.py` MUST reuse `evaluate_size_compatibility_dynamic()` from `gravel_bot/geometry_sizing.py` to eradicate duplicate height-to-frame algorithms.
- **FR-005**: Legacy test assertions in `test_bot.py` MUST be consolidated into `test_new_features.py`, removing duplicate test suites.
- **FR-006**: The entire test suite MUST pass with 100% green status after all deletions and simplifications.

---

## Success Criteria *(mandatory)*

- **SC-001**: Net codebase reduction of at least 450 lines of duplicate and dead code (`net: -450+ lines`).
- **SC-002**: 100% of CLI commands (`--list`, `--deals`, `--presupuesto`, `--audit`, `--re-score`, `--ficha`, `--web`) remain fully operational with identical outputs.
- **SC-003**: 100% of unit tests pass cleanly in under 10 seconds.
- **SC-004**: Zero dead network traffic to liquidated stores during full pipeline runs.

---

## Assumptions

- No external tool or script depends on manual string-parsing behavior inside `gravel_tracker.py` that is not already supported by `argparse` in `gravel_bot.cli`.
- Defunct marketplace Tuvalum has no ongoing business or API to monitor.
