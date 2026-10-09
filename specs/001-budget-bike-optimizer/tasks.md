---

description: "Task list for Budget Bike Optimizer implementation"
---

# Tasks: Budget Bike Optimizer

**Input**: Design documents from `specs/001-budget-bike-optimizer/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`, `[US4]`)
- Every task includes an exact file path.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module structure initialization and data container definitions.

- [ ] T001 Initialize budget optimizer module structure in `gravel_bot/budget_optimizer.py`
- [ ] T002 [P] Configure data classes (`BudgetQuery`, `CleanCandidateBike`, `RecommendationPodio`) in `gravel_bot/budget_optimizer.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core candidate extraction, Value-for-Money index calculation, and test harness setup.

**⚠️ CRITICAL**: Must be completed before user story implementation begins.

- [ ] T003 Implement candidate bikes extraction query helper in `gravel_bot/db.py`
- [ ] T004 [P] Implement Value-for-Money (VfM) index calculation logic in `gravel_bot/budget_optimizer.py`
- [ ] T005 [P] Setup baseline unit test harness for budget optimizer in `test_new_features.py`

**Checkpoint**: Foundation ready — user story implementation can proceed.

---

## Phase 3: User Story 1 - Budget-Targeted Real Deal Recommendation (Priority: P1) 🎯 MVP

**Goal**: Deliver a single-command executive recommendation of the top complete gravel bikes strictly within the user's budget ceiling.

**Independent Test**: Execute `python3 gravel_tracker.py --presupuesto 1000`; verify the #1 Best Value and #2 Bargain bikes have asking price $\le 1.000\text{ €}$, verified direct buy links, and complete component specs.

### Tests for User Story 1

- [ ] T006 [P] [US1] Write unit tests for budget ceiling filtering and podio ranking in `test_new_features.py`

### Implementation for User Story 1

- [ ] T007 [US1] Implement primary recommendation ranking algorithm (`optimize_for_budget`) in `gravel_bot/budget_optimizer.py`
- [ ] T008 [US1] Implement executive terminal card text formatter in `gravel_bot/budget_optimizer.py`
- [ ] T009 [US1] Implement CLI `--presupuesto`, `--recomendar`, and `--json` flags in `gravel_tracker.py`
- [ ] T010 [US1] Wire CLI subcommands, argument parsing, and help text in `gravel_bot/cli.py`

**Checkpoint**: User Story 1 functional and independently testable as an MVP.

---

## Phase 4: User Story 2 - Strict Noise Exclusion & Reality Filter (Priority: P2)

**Goal**: Rigorously exclude loose framesets, motorized e-bikes, non-gravel disciplines, and closed/liquidated merchants (e.g. Tuvalum) from all recommendation sets.

**Independent Test**: Run budget search; assert that 0% of recommendations are labeled as frames, ebikes, or closed shops, and 100% match the declared rider height/size.

### Tests for User Story 2

- [ ] T011 [P] [US2] Write unit tests for bare frames, ebikes, closed shops, and size exclusion in `test_new_features.py`

### Implementation for User Story 2

- [ ] T012 [US2] Implement deterministic noise exclusion filters (`is_complete_gravel_bike`, `is_active_store`) in `gravel_bot/budget_optimizer.py`
- [ ] T013 [US2] Implement rider size and height compatibility validation against catalog size lists in `gravel_bot/budget_optimizer.py`
- [ ] T014 [US2] Integrate noise exclusion predicates into database catalog queries in `gravel_bot/db.py`

**Checkpoint**: User Stories 1 and 2 operate in tandem with zero false-positive listings.

---

## Phase 5: User Story 3 - Smart Stretch & Compromise Analysis (Priority: P3)

**Goal**: Detect when spending $\le 15\%$ over budget unlocks a critical component upgrade (e.g., hydraulic GRX brakes or carbon fork) and highlight Budget Saver options ($\le 0.85B$).

**Independent Test**: Query for 950 € budget; verify that the Smart Stretch candidate (if priced $\le 1.092\text{ €}$) explicitly articulates the component leap.

### Tests for User Story 3

- [ ] T015 [P] [US3] Write unit tests for +15% budget stretch and hydraulic brake threshold detection in `test_new_features.py`

### Implementation for User Story 3

- [ ] T016 [US3] Implement Smart Stretch evaluation algorithm (threshold jumps) in `gravel_bot/budget_optimizer.py`
- [ ] T017 [US3] Implement Budget Saver alternative detection ($\le 0.85B$) in `gravel_bot/budget_optimizer.py`
- [ ] T018 [US3] Add Smart Stretch and Budget Saver sections to card formatters in `gravel_bot/budget_optimizer.py`

**Checkpoint**: User Story 3 delivers actionable trade-off advice alongside primary recommendations.

---

## Phase 6: User Story 4 - Multi-Channel Purchasing Clarity & Telegram Bot (Priority: P4)

**Goal**: Provide channel transparency (local physical shops, online retailers, certified refurbished) and full Telegram bot interactive integration.

**Independent Test**: Test `/presupuesto 1000` on Telegram; verify formatted HTML message with inline preset buttons and channel labels.

### Implementation for User Story 4

- [ ] T019 [P] [US4] Implement store channel categorization (`tienda_fisica`, `online`, `ocasion`) in `gravel_bot/budget_optimizer.py`
- [ ] T020 [US4] Implement `/presupuesto` command handler and HTML formatting in `gravel_bot/bot_service.py`
- [ ] T021 [US4] Add interactive Telegram preset keyboard buttons (`<800€`, `1.000€`, `1.200€`, `1.500€`) in `gravel_bot/bot_service.py`
- [ ] T022 [US4] Implement conversational numeric message handler for budget queries in `gravel_bot/bot_service.py`

**Checkpoint**: All user stories functional across both CLI and Telegram bot interfaces.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end verification, documentation updates, and catalog validation.

- [ ] T023 [P] Add end-to-end smoke verification script per `quickstart.md` in `test_new_features.py`
- [ ] T024 [P] Update user documentation and command guide in `directorio_bicicletas.md`
- [ ] T025 Run catalog integrity check and purge verification in `gravel_tracker.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Delivers MVP.
- **User Story 2 (Phase 4)**: Depends on US1 completion (integrates noise filters into candidate pool).
- **User Story 3 (Phase 5)**: Depends on US1 & US2 completion (evaluates stretch pool).
- **User Story 4 (Phase 6)**: Depends on US1-US3 completion (exposes complete engine to Telegram).
- **Polish (Phase 7)**: Depends on all user stories being complete.

---

## Parallel Opportunities

- **Setup**: T001 and T002 can run concurrently.
- **Foundational**: T004 and T005 can run in parallel with T003.
- **Tests**: T006, T011, T015 can be written concurrently with their respective models.
- **Polish**: T023 and T024 can be performed in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1).
3. Validate: `python3 gravel_tracker.py --presupuesto 1000`.
4. MVP is immediately usable and solves the primary user need!

### Incremental Delivery

1. Foundation ready (Phases 1-2).
2. MVP delivered: Budget recommendations work in CLI (Phase 3).
3. Noise eliminated: 0% frames, 0% ebikes, 0% closed stores (Phase 4).
4. Advisory added: Smart Stretch highlights hydraulic upgrades (Phase 5).
5. Omnichannel & Telegram: Bot interactive buttons and channel transparency (Phase 6).
6. Polish & validation completed (Phase 7).