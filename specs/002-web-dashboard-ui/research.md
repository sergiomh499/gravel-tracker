# Phase 0 Research: Lightweight Interactive Web Dashboard

**Feature**: `002-web-dashboard-ui`
**Date**: 2026-10-09

## Research Overview

This document resolves the key technical decisions for implementing the Lightweight Interactive Web Dashboard in `gravel-tracker`. It details the zero-dependency Python embedded web server, single-page application frontend architecture, REST API design, and CLI integration.

---

### Decision 1: Embedded Web Server Architecture

- **Decision**: Implement a native multi-threaded HTTP server using Python's standard library `http.server.ThreadingHTTPServer` and custom `http.server.BaseHTTPRequestHandler` in `gravel_bot/web_server.py`.
- **Rationale**:
  - Requires **zero external pip dependencies** and **zero Node.js/npm runtimes**.
  - `ThreadingHTTPServer` handles concurrent client requests gracefully (browser preflights, asset loading, API calls).
  - Can serve both static files (`index.html`, `app.js`, `style.css`) and dynamic JSON endpoints (`/api/bikes`, `/api/recommend`).
  - Starts in $< 100\text{ ms}$ and consumes $< 15\text{ MB}$ of RAM.
- **Alternatives Considered**:
  - *FastAPI / Uvicorn / Flask*: Rejected because they require third-party pip packages (`fastapi`, `uvicorn`, `starlette`), breaking the project's zero-dependency portable stdlib philosophy.
  - *Pure Static Files without Python server*: Rejected because the browser requires a local HTTP context to fetch JSON and dynamic API endpoints without CORS or filesystem security restrictions.

---

### Decision 2: Frontend Architecture & Styling

- **Decision**: Implement a client-side Single Page Application (SPA) using modern vanilla ES6+ JavaScript, native DOM manipulation, and modern CSS3 Grid/Flexbox styling (with optional Tailwind CSS utility classes via CDN).
- **Rationale**:
  - Client-side filtering ensures instant slider response ($< 20\text{ ms}$) without hitting the server on every tick of the budget slider.
  - No build step, no Babel, no Webpack, no node_modules.
  - Assets are stored directly under `gravel_bot/web/` (`index.html`, `app.js`, `style.css`).
  - Full mobile responsiveness using responsive CSS media queries and flex layouts.
- **Alternatives Considered**:
  - *React / Vue / Svelte with Vite*: Rejected because it introduces node_modules, build steps, and complexity unnecessary for a catalog dashboard.
  - *Server-Side Rendering (Jinja2)*: Rejected because slider dragging and real-time filtering would either require full page reloads or clunky HTMX requests instead of buttery-smooth 60fps client-side filtering.

---

### Decision 3: REST API Contracts & Endpoint Design

- **Decision**: Expose clean REST endpoints from the Python server:
  1. `GET /`: Returns the main single-page application HTML document.
  2. `GET /api/bikes`: Returns the complete sanitized gravel catalog as JSON (array of `CleanCandidateBike` dictionaries), allowing the client browser to cache and filter locally in memory.
  3. `GET /api/recommend?budget=1000&height=169&size=S&channel=all`: Invokes `optimize_for_budget()` and returns the executive `RecommendationPodio` JSON structure.
  4. `GET /api/stats`: Returns summary catalog statistics (total active models, average price, brand breakdown).
- **Rationale**: Reuses the core business logic from `gravel_bot/budget_optimizer.py` and `gravel_bot/db.py`, ensuring 100% data consistency between CLI, Telegram, and Web interfaces.
- **Alternatives Considered**:
  - *Embedding JSON directly into HTML*: Discards API reusability and bloats HTML payloads.

---

### Decision 4: CLI Entrypoint & Server Lifecycle

- **Decision**: Wire the server launcher into `gravel_tracker.py` and `gravel_bot/cli.py`:
  - `python3 gravel_tracker.py --web [--port 8080] [--host 127.0.0.1]`
  - Prints clean startup message with clickable URL: `🚀 Servidor web activo en http://127.0.0.1:8080`
  - Graceful shutdown upon `SIGINT` (Ctrl+C).
- **Rationale**: Provides an immediate, user-friendly command for users wanting visual exploration.