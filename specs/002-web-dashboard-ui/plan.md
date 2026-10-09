# Implementation Plan: Lightweight Interactive Web Dashboard

**Branch**: `002-web-dashboard-ui` | **Date**: 2026-10-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-web-dashboard-ui/spec.md`

## Summary

The Lightweight Interactive Web Dashboard provides a visual exploration surface for the gravel catalog. Running on an embedded, zero-dependency Python HTTP server (`http.server.ThreadingHTTPServer`), it serves an ultra-fast Single Page Application (SPA) with real-time budget sliders, rider size selection, 1v1 comparison modals, local store indicators, and direct purchase links. It introduces zero npm/Node build steps and executes locally via `python3 gravel_tracker.py --web`.

## Technical Context

**Language/Version**: Python 3.11+ (Backend) | HTML5, CSS3, Vanilla ES6+ JavaScript (Frontend)

**Primary Dependencies**: Zero third-party dependencies (strictly Python stdlib: `http.server`, `urllib.parse`, `json`, `sqlite3`)

**Storage**: SQLite (`gravel_madrid.db`), reading through existing domain helpers in `gravel_bot/budget_optimizer.py` and `gravel_bot/db.py`

**Testing**: Python `unittest` suite (`test_new_features.py` testing HTTP server endpoints and API serialization)

**Target Platform**: Any modern web browser (Mobile & Desktop) | Headless / Desktop Linux host

**Project Type**: Embedded Web Server & Frontend Single Page Application

**Performance Goals**: $< 100\text{ ms}$ server cold start, $< 50\text{ ms}$ client-side search/slider update, $< 15\text{ MB}$ server RAM footprint

**Constraints**: Zero npm/Node tooling, zero external build steps, 100% responsive design down to 375px screens

**Scale/Scope**: 140+ active gravel bikes in catalog, instant client-side in-memory filtering

## Constitution Check

*GATE: Passed before Phase 0 research. Re-evaluated post Phase 1 design.*

- **Principle I: Library-First**: The HTTP server reuses domain models from `gravel_bot/budget_optimizer.py` and `gravel_bot/db.py` without coupling business rules to HTTP transport.
- **Principle II: CLI Interface**: Server can be started directly via CLI: `python3 gravel_tracker.py --web [--port 8080]`.
- **Principle III: Simplicity & Ponytail**: Zero build tooling, zero framework bloat. Pure standard library Python server and standard web technologies (HTML/CSS/JS).
- **Principle IV: Observability**: Clear startup banner with port, address, and HTTP access logging.

## Project Structure

### Documentation (this feature)

```text
specs/002-web-dashboard-ui/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Technical research & architectural decisions
├── data-model.md        # Frontend & API entities
├── quickstart.md        # Runnable verification guide
├── contracts/
│   └── rest-api-contract.md # HTTP endpoint specifications
└── checklists/
    └── requirements.md  # Quality verification checklist
```

### Source Code Layout

```text
gravel_bot/
├── web_server.py        # [NEW] Embedded ThreadingHTTPServer & REST API handlers
├── web/                 # [NEW] Static frontend assets
│   ├── index.html       # Single Page Application HTML layout
│   ├── app.js           # Client-side reactivity, slider & 1v1 modal logic
│   └── style.css        # Responsive CSS styling & design system
├── budget_optimizer.py  # Domain recommendation engine (reused by /api/recommend)
├── db.py                # Database catalog access
└── cli.py               # CLI subcommands & flag dispatcher

gravel_tracker.py        # Unified CLI entrypoint (--web flag)
test_new_features.py     # HTTP integration test suite
```

**Structure Decision**: Static assets live in `gravel_bot/web/`, and server logic lives in `gravel_bot/web_server.py`. The CLI entrypoint `gravel_tracker.py` exposes `--web` to launch the server.

## Complexity Tracking

*No constitution violations. Pure standard library implementation.*