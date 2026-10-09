---

description: "Task list for Lightweight Interactive Web Dashboard implementation"
---

# Tasks: Lightweight Interactive Web Dashboard

**Input**: Design documents from `specs/002-web-dashboard-ui/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

## Format: `- [ ] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Every task includes an exact file path.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module structure initialization and static assets directory setup.

- [ ] T026 Initialize web server module structure in `gravel_bot/web_server.py`
- [ ] T027 [P] Create static web assets directory structure in `gravel_bot/web/index.html`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Embedded `ThreadingHTTPServer`, REST routing, and baseline test harness.

**⚠️ CRITICAL**: Must be completed before user story implementation begins.

- [ ] T028 Implement `ThreadingHTTPServer` and base handler skeleton in `gravel_bot/web_server.py`
- [ ] T029 [P] Implement REST endpoint routing (`/api/bikes`, `/api/recommend`, `/api/stats`) in `gravel_bot/web_server.py`
- [ ] T030 [P] Setup unit test harness for HTTP server and API endpoints in `test_new_features.py`

**Checkpoint**: Foundation ready — user story implementation can proceed.

---

## Phase 3: User Story 1 - Real-Time Budget & Visual Catalog Explorer (Priority: P1) 🎯 MVP

**Goal**: Deliver a responsive Single Page Application with interactive budget slider, dynamic card grid, and direct purchase links.

**Independent Test**: Run `python3 gravel_tracker.py --web` and open `http://localhost:8080`. Drag budget slider to 1.000 €; verify bike cards update in real time with #1 Best Value and #2 Bargain, and purchase links work.

### Tests for User Story 1

- [ ] T031 [P] [US1] Write unit tests for `/api/bikes` and `/api/recommend` JSON endpoints in `test_new_features.py`

### Implementation for User Story 1

- [ ] T032 [US1] Implement JSON serialization for sanitized gravel catalog in `gravel_bot/web_server.py`
- [ ] T033 [US1] Build responsive HTML layout and design system in `gravel_bot/web/index.html`
- [ ] T034 [US1] Implement client-side reactive budget slider and live card grid rendering in `gravel_bot/web/app.js`
- [ ] T035 [US1] Implement modern responsive CSS styling and badge styles in `gravel_bot/web/style.css`
- [ ] T036 [US1] Implement CLI `--web` flag and server launcher in `gravel_tracker.py`

**Checkpoint**: User Story 1 functional and independently testable as an MVP.

---

## Phase 4: User Story 2 - Visual 1v1 Bike Face-Off & Comparison (Priority: P2)

**Goal**: Enable side-by-side visual comparison between two selected bikes with differential spec highlights.

**Independent Test**: Select two bikes and click "Comparar (1v1)"; verify modal renders with winner specs highlighted in green.

### Tests for User Story 2

- [ ] T037 [P] [US2] Write unit tests for comparison advantage calculation in `test_new_features.py`

### Implementation for User Story 2

- [ ] T038 [US2] Implement side-by-side spec differential calculation in `gravel_bot/web_server.py`
- [ ] T039 [US2] Implement comparison modal UI and winner spec highlights in `gravel_bot/web/app.js`
- [ ] T040 [US2] Add modal animation and comparative table styling in `gravel_bot/web/style.css`

**Checkpoint**: User Stories 1 and 2 operate in tandem with interactive comparison capabilities.

---

## Phase 5: User Story 3 - Local Store Radius & Purchasing Channel Filter (Priority: P3)

**Goal**: Filter by local physical stores (Madrid / user zone) and show shop distance and address.

**Independent Test**: Toggle "Solo Tiendas Físicas"; verify online-only stores are hidden and distances in km are displayed.

### Implementation for User Story 3

- [ ] T041 [P] [US3] Implement physical store filtering toggle and distance badge logic in `gravel_bot/web/app.js`
- [ ] T042 [US3] Add channel filter UI controls in `gravel_bot/web/index.html`
- [ ] T043 [US3] Style store badges and local pickup indicators in `gravel_bot/web/style.css`

**Checkpoint**: All user stories functional across catalog exploration, 1v1 face-off, and local channels.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: CLI wiring, documentation, quickstart validation, and mobile polish.

- [ ] T044 [P] Wire CLI subcommand `web` in `gravel_bot/cli.py`
- [ ] T045 [P] Add quickstart integration smoke test in `test_new_features.py`
- [ ] T046 [P] Update user documentation with web launcher instructions in `directorio_bicicletas.md`
- [ ] T047 Validate mobile viewport responsiveness and browser asset caching in `gravel_bot/web/index.html`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Delivers MVP.
- **User Story 2 (Phase 4)**: Depends on US1 completion (adds comparison modal over existing grid).
- **User Story 3 (Phase 5)**: Depends on US1 completion (adds channel filter to grid).
- **Polish (Phase 6)**: Depends on all user stories being complete.

---

## Parallel Opportunities

- **Setup**: T026 and T027 can run concurrently.
- **Foundational**: T029 and T030 can run in parallel with T028.
- **Tests**: T031 and T037 can be written concurrently with server endpoints.
- **Frontend / Backend**: T033, T035 can be developed in parallel with T032.
- **Polish**: T044, T045, T046 can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1).
3. Validate: `python3 gravel_tracker.py --web` and explore catalog on `http://localhost:8080`.
4. Visual exploration is fully usable!

### Incremental Delivery

1. Foundation ready: HTTP server and `/api/bikes` endpoint working (Phases 1-2).
2. MVP delivered: Web catalog with reactive slider and direct links (Phase 3).
3. 1v1 face-off modal added (Phase 4).
4. Local store radius filter added (Phase 5).
5. CLI wiring & mobile polish (Phase 6).
