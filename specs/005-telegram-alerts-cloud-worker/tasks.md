---

description: "Task list for Telegram Alert Formatting and Autonomous Cloud Worker"
---

# Tasks: Telegram Alert Formatting & Autonomous Cloud Worker

**Input**: Design documents from `specs/005-telegram-alerts-cloud-worker/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Core sanitization, URL validation helpers, and HTML escaping utilities.

- [X] T087 [P] Add URL validation helper (`is_valid_purchase_url`) in `gravel_bot/notifier.py`
- [X] T088 [P] Add HTML escaping utilities for Telegram markup in `gravel_bot/notifier.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Payload builder with inline keyboard support and test harness.

**⚠️ CRITICAL**: Must be completed before user story formatting cutover.

- [X] T089 Implement Telegram `inline_keyboard` payload constructor (`build_telegram_payload`) in `gravel_bot/notifier.py`
- [X] T090 [P] Implement URL quality gate in `send_telegram_alert` in `gravel_bot/notifier.py`
- [X] T091 [P] Setup unit tests for Telegram formatting and payload builder in `test_new_features.py`

**Checkpoint**: Foundation ready — payload constructor and URL gate operational.

---

## Phase 3: User Story 1 - Pristine Telegram Alert Formatting with Guaranteed Store Links (Priority: P1) 🎯 MVP

**Goal**: Eradicate unescaped HTML parse errors and provide direct, verified store links with one-tap inline buttons in Telegram.

**Independent Test**: Trigger a sample alert; verify Telegram renders bold headers, strikethrough savings, sanitized specs, and a working button `[🛒 Ver Oferta en Tienda]`.

### Tests for User Story 1

- [X] T092 [P] [US1] Write unit tests for escaped alert messages and inline buttons in `test_new_features.py`

### Implementation for User Story 1

- [X] T093 [US1] Refactor `format_alert_message` with strict HTML escaping and formatted purchase link in `gravel_bot/notifier.py`
- [X] T094 [US1] Refactor `format_price_drop_message` with strict HTML escaping and direct purchase link in `gravel_bot/notifier.py`
- [X] T095 [US1] Update `send_telegram_alert` to transmit `inline_keyboard` action buttons in `gravel_bot/notifier.py`

**Checkpoint**: User Story 1 complete; Telegram alerts are visually pristine and clickable.

---

## Phase 4: User Story 2 - Autonomous Free Cloud Worker Execution (Priority: P1)

**Goal**: Enable 100% cloud execution in GitHub Actions so the user's personal laptop does not need to run scrapers or consume battery/network.

**Independent Test**: Execute `python3 gravel_tracker.py cloud-sync --trigger`; verify secrets are mirrored to GitHub and cloud worker executes in GitHub Actions.

### Implementation for User Story 2

- [X] T096 [P] [US2] Implement CLI `cloud-sync` command in `gravel_bot/cli.py` to mirror `.env` to GitHub repository secrets via `gh secret set`
- [X] T097 [US2] Wire `cloud-sync` command alias in `gravel_tracker.py`
- [X] T098 [US2] Create autonomous cloud worker workflow `.github/workflows/gravel_cloud_worker.yml` with scheduled cron and auto-commit
- [X] T099 [US2] Verify automated secret sync and trigger test cloud execution via GitHub CLI

**Checkpoint**: User Story 2 complete; cloud worker operates 24/7 autonomously.

---

## Phase 5: User Story 3 - Alert Link Quality Gate (Priority: P2)

**Goal**: Guarantee no alerts are ever dispatched without a valid, direct purchase link.

**Independent Test**: Dispatch deal with missing or malformed URL; verify pipeline logs skipped alert and suppresses notification.

### Implementation for User Story 3

- [X] T100 [P] [US3] Write unit tests for missing URL suppression and link normalization in `test_new_features.py`
- [X] T101 [US3] Integrate alert quality gate in pipeline notification dispatch in `gravel_bot/pipeline.py`

**Checkpoint**: Quality gate verified; zero alerts sent without valid links.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Execute end-to-end quickstart validation and full test suite regression checks.

- [X] T102 [P] Run quickstart validation scenarios in `specs/005-telegram-alerts-cloud-worker/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can begin immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 completion.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Delivers MVP.
- **User Story 2 (Phase 4)**: Can run concurrently with US1.
- **User Story 3 (Phase 5)**: Depends on US1 completion.
- **Polish (Phase 6)**: Depends on all prior phases.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2.
2. Complete Phase 3 (escaped formatting + inline button).
3. Test delivery to Telegram mobile client.

### Incremental Delivery

1. Foundation: URL validator & HTML escaper (Phases 1-2).
2. MVP: Pristine message formatting & inline button (Phase 3).
3. Cloud Worker: GitHub Actions 24/7 cron runner & `cloud-sync` (Phase 4).
4. Quality Gate: Suppress alerts lacking direct links (Phase 5).
5. Quickstart verification (Phase 6).
