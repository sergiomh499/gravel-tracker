---

description: "Task list for Pruning Codebase Bloat and Over-Engineering"
---

# Tasks: Prune Codebase Bloat & Over-Engineering

**Input**: Design documents from `specs/004-prune-codebase-bloat/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify and extend CLI argument parsing options for total parity.

- [X] T071 Verify and update CLI parser aliases in `gravel_bot/cli.py` to support all shorthand flags (`--presupuesto`, `--audit`, `--re-score`, `--ficha`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Unify component authority truth and remove duplicate file loading.

**⚠️ CRITICAL**: Must be completed before user stories 1 and 2 cutovers.

- [X] T072 [P] Consolidate factory model specifications dictionary in `gravel_bot/components_authority.py`
- [X] T073 [P] Streamline `gravel_bot/knowledge_base.py` to route model lookups to `gravel_bot/components_authority.py`

**Checkpoint**: Component truth unified; ready for entrypoint and scraper cleanup.

---

## Phase 3: User Story 1 - Unified CLI Entry Point & Parameter Parity (Priority: P1) 🎯 MVP

**Goal**: Make `gravel_tracker.py` a thin delegator to `gravel_bot.cli.main()`, cutting ~200 lines of manual `sys.argv` parsing.

**Independent Test**: Execute `python3 gravel_tracker.py --presupuesto 1000`, `python3 gravel_tracker.py --audit --limit 2`, and `python3 gravel_tracker.py --ficha "Jakar 30"`; verify identical output and options.

### Tests for User Story 1

- [X] T074 [P] [US1] Write contract unit tests for CLI entrypoint delegation in `test_new_features.py`

### Implementation for User Story 1

- [X] T075 [US1] Refactor `gravel_tracker.py` into a lightweight entry point delegating to `gravel_bot.cli.main()`
- [X] T076 [US1] Verify parameter passthrough and default ranking/deals behavior in `gravel_tracker.py`

**Checkpoint**: User Story 1 functional; duplicate CLI loop eradicated.

---

## Phase 4: User Story 2 - Deletion of Defunct Scrapers & Unification of Component Truth (Priority: P1)

**Goal**: Delete `tuvalum.py` and purge defunct scraper registrations to prevent wasted network requests.

**Independent Test**: Run multi-store scraper initialization; verify no references or network calls to Tuvalum.

### Implementation for User Story 2

- [X] T077 [P] [US2] Remove Tuvalum scraper registration in `gravel_bot/scrapers/multi_store.py`
- [X] T078 [P] [US2] Mark Tuvalum as inactive or remove from `gravel_bot/scrapers/store_directory.py`
- [X] T079 [US2] Delete defunct scraper file `gravel_bot/scrapers/tuvalum.py`
- [X] T080 [US2] Clean any remaining imports of TuvalumScraper in `gravel_bot/pipeline.py`

**Checkpoint**: Defunct scraper completely excised.

---

## Phase 5: User Story 3 - Sizing Logic Unification & Test Suite Consolidation (Priority: P2)

**Goal**: Unify sizing calculation in `budget_optimizer.py` and prune legacy redundant test suite.

**Independent Test**: Run `python3 -m unittest test_new_features.py`; verify sizing logic produces identical recommendations and all legacy tests pass.

### Implementation for User Story 3

- [X] T081 [P] [US3] Port unique test assertions from `test_bot.py` into `test_new_features.py`
- [X] T082 [US3] Delete redundant legacy test file `test_bot.py`
- [X] T083 [US3] Refactor `is_size_compatible` in `gravel_bot/budget_optimizer.py` to delegate to `gravel_bot.geometry_sizing.evaluate_size_compatibility_dynamic`

**Checkpoint**: Sizing unified; redundant test suite eliminated.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quickstart verification, line count reduction accounting, and full regression test run.

- [X] T084 [P] Run quickstart scenarios in `specs/004-prune-codebase-bloat/quickstart.md`
- [X] T085 [P] Audit net lines reduced across the repository using `git diff --stat`
- [X] T086 [P] Execute full unit test suite regression check with `python3 -m unittest discover`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can begin immediately.
- **Foundational (Phase 2)**: Depends on Setup.
- **User Story 1 (Phase 3)**: Depends on Phase 1 & 2. Delivers MVP.
- **User Story 2 (Phase 4)**: Can run in parallel with US1.
- **User Story 3 (Phase 5)**: Depends on US1 & US2 completion.
- **Polish (Phase 6)**: Depends on all prior phases.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2.
2. Complete Phase 3 (thin `gravel_tracker.py`).
3. Validate: `python3 gravel_tracker.py --presupuesto 1000`.

### Incremental Delivery

1. Foundation: Authority consolidation (Phases 1-2).
2. MVP: CLI deduplication (Phase 3).
3. Dead code pruning: Delete `tuvalum.py` (Phase 4).
4. Logic consolidation: Sizing & test suites (Phase 5).
5. Net accounting: Verify -450+ lines removed (Phase 6).
