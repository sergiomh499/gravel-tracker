---

description: "Task list for Catalog Freshness, Spec Audit and Ranking Calibration"
---

# Tasks: Catalog Freshness, Spec Audit & Ranking Calibration

**Input**: Design documents from `specs/003-audit-catalog-ranking/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module structure initialization and database schema extensions.

- [X] T048 Add schema migrations for audit fields (`fecha_auditoria`, `audit_status`, `c6_garantia`) in `gravel_bot/db.py`
- [X] T049 [P] Initialize component authority matrix module structure in `gravel_bot/components_authority.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core component authority truth dictionary, live HTTP checker, and test harness.

**⚠️ CRITICAL**: Must be completed before user story implementation begins.

- [X] T050 Implement ground-truth mapping for groups, actuation types, and MSRP bounds in `gravel_bot/components_authority.py`
- [X] T051 [P] Implement live HTTP link checker and stock status extractor in `gravel_bot/catalog_auditor.py`
- [X] T052 [P] Setup baseline unit test harness for catalog audit and spec sanitization in test_new_features.py

**Checkpoint**: Foundation ready — user story implementation can proceed.

---

## Phase 3: User Story 1 - Automated Catalog Freshness & Stock Verification (Priority: P1) 🎯 MVP

**Goal**: Deliver an automated live verification pipeline that prunes out-of-stock listings and detects price drift.

**Independent Test**: Execute `python3 gravel_tracker.py --audit --limit 10`; verify out-of-stock models are flagged inactive, live prices updated, and audit summary printed.

### Tests for User Story 1

- [X] T053 [P] [US1] Write unit tests for live stock verification and HTTP health checks in `test_new_features.py`

### Implementation for User Story 1

- [X] T054 [US1] Implement multi-store out-of-stock selectors and price drift tracking in `gravel_bot/catalog_auditor.py`
- [X] T055 [US1] Implement catalog audit coordinator function (`run_catalog_audit`) in `gravel_bot/catalog_auditor.py`
- [X] T056 [US1] Implement CLI `--audit` command handler and terminal progress output in `gravel_tracker.py`
- [X] T057 [US1] Wire CLI `--audit subcommand and arguments in `gravel_bot/cli.py`

**Checkpoint**: User Story 1 functional and independently testable as an MVP.

---

## Phase 4: User Story 2 - Strict Spec Sanitization & Truthful Component Classification (Priority: P2)

**Goal**: Correct technical inaccuracies (e.g. false hydraulic brakes on Claris/Tourney) and enforce MSRP price ceilings to eliminate inflated discounts.

**Independent Test**: Run specification sanitization on sample ad with "Shimano Claris frenos hidráulicos" and 3.000 € PVP; verify brake is forced to mechanical and PVP bounded to MSRP.

### Tests for User Story 2

- [X] T058 [P] [US2] Write unit tests for false hydraulic brake correction and MSRP capping in `test_new_features.py`

### Implementation for User Story 2

- [X] T059 [US2] Implement specification sanitization function (`sanitize_bike_specs`) in `gravel_bot/components_authority.py`
- [X] T060 [US2] Implement frame and fork material cross-validation rules in `gravel_bot/components_authority.py`
- [X] T061 [US2] Integrate authoritative spec sanitization into catalog extraction pipeline in `gravel_bot/evaluator.py`
- [X] T062 [US2] Implement batch specification normalization script in `gravel_bot/components_authority.py`

**Checkpoint**: User Stories 1 and 2 operate in tandem with 100% truthful technical data.

---

## Phase 5: User Story 3 - Transparent & Calibrated Ranking Rubric with Channel Weighting (Priority: P3)

**Goal**: Calibrate scoring rubric with itemized score breakdown (C1..C6) and incorporate buyer protection / warranty factors.

**Independent Test**: Execute `python3 gravel_tracker.py --re-score`; verify itemized points C1–C6 calculated, warranty bonus added for official dealers, and updated rankings saved.

### Tests for User Story 3

- [X] T063 [P] [US3] Write unit tests for calibrated rubric and warranty bonus calculation in `test_new_features.py`

### Implementation for User Story 3

- [X] T064 [US3] Implement calibrated scoring rubric with C1..C6 criteria and warranty weighting in `gravel_bot/evaluator.py`
- [X] T065 [US3] Implement itemized score card generator (`get_itemized_score_card`) in `gravel_bot/evaluator.py`
- [X] T066 [US3] Implement catalog re-scoring command (`run_catalog_rescore`) in `gravel_bot/evaluator.py`
- [X] T067 [US3] Implement CLI `--re-score` flag in `gravel_tracker.py` and `gravel_bot/cli.py`

**Checkpoint**: All user stories functional with transparent, explainable rankings.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Card inspection updates, web API badge integration, and quickstart validation.

- [X] T068 [P] Update `--ficha` inspection command with itemized rubric score breakdown in `gravel_bot/bike_inspector.py`
- [X] T069 [P] Expose audit status and itemized score cards in REST API endpoints (`/api/bikes`) in `gravel_bot/web_server.py`
- [X] T070 [P] Add quickstart end-to-end smoke verification tests in `test_new_features.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Delivers MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational completion. Delivers spec truthfulness.
- **User Story 3 (Phase 5)**: Depends on US2 completion (calibrated rubric uses sanitized specs).
- **Polish (Phase 6)**: Depends on all user stories being complete.

---

## Parallel Opportunities

- **Setup**: T048 and T049 can run concurrently.
- **Foundational**: T051 and T052 can run in parallel with T050.
- **Tests**: T053, T058, T063 can be written concurrently with their respective modules.
- **Polish**: T068, T069, T070 can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1).
3. Validate: `python3 gravel_tracker.py --audit --limit 10`.
4. Catalog freshness audit is operational!

### Incremental Delivery

1. Foundation ready (Phases 1-2).
2. MVP delivered: Live freshness audit (`--audit`) working (Phase 3).
3. False specs and inflated PVPs eradicated (Phase 4).
4. Calibrated rubric and itemized scorecard (`--re-score`) active (Phase 5).
5. Detailed inspection and web API integration polished (Phase 6).
