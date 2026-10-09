# Feature Specification: Lightweight Interactive Web Dashboard

**Feature Branch**: `002-web-dashboard-ui`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Dashboard Web Ligero / Interfaz Visual Interactiva"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-Time Budget & Visual Catalog Explorer (Priority: P1) 🎯 MVP

As a cyclist looking for a gravel bike, I want to open a clean and lightweight web dashboard in my browser (desktop or mobile) where I can adjust a budget slider, select my height or size, and filter by components (e.g. hydraulic brakes, 1x vs 2x) so that I instantly see bike cards with specs, real prices, discounts, tier rating, and direct purchase links without page reloads.

**Why this priority**: Solves the primary visual usability need. While CLI and Telegram are great for quick text queries, a web interface provides immediate visual scanning, slider adjustments, and side-by-side exploration of the entire catalog.

**Independent Test**: Launch the web server via `python3 gravel_tracker.py --web` and open `http://localhost:8080`. Adjust the budget slider to 1.000 €; verify that cards update in real time with the #1 Best Value and #2 Bargain prominently featured, and clicking any card takes the user to the store.

**Acceptance Scenarios**:

1. **Given** the web dashboard loaded with the active gravel catalog, **When** the user drags the budget slider to 1.000 € and selects size S, **Then** the bike card grid updates instantly (<50 ms) showing only compatible models priced $\le 1.000\text{ €}$, sorted by Value-for-Money index.
2. **Given** a displayed bike card, **When** the user clicks the "Ver Oferta" button, **Then** the product's direct purchase URL opens in a new tab.

---

### User Story 2 - Visual 1v1 Bike Face-Off & Comparison (Priority: P2)

As a buyer hesitating between two potential bikes, I want to select any two models and open an interactive side-by-side comparison modal that pits their components against each other (frame material, fork, drivetrain, brake type, weight, and rubric score), highlighting winner features in green.

**Why this priority**: Choosing between gravel bikes often comes down to technical nuances (e.g., Shimano GRX 400 hydraulic vs Microshift Sword mechanical). A visual head-to-head comparison removes doubt and gives clear buying confidence.

**Independent Test**: Click "Comparar" on Megamo Jakar 30 and Conor Kalima; verify that the comparison modal opens displaying differential advantages (e.g. hydraulic vs mechanical brakes) with winning specs highlighted.

**Acceptance Scenarios**:

1. **Given** two selected bikes in the catalog, **When** the user clicks "Comparar (1v1)", **Then** a modal opens with a side-by-side spec matrix highlighting superior components in each row.
2. **Given** the comparison modal open, **When** the user clicks "Cerrar" or clicks outside, **Then** the modal closes and returns to the catalog grid preserving the user's active filters.

---

### User Story 3 - Local Store Radius & Purchasing Channel Filter (Priority: P3)

As a rider who prefers testing the bike in person or having local warranty support, I want to toggle a "Tiendas Físicas (Madrid / Mi Zona)" filter and see the shop name, distance in km, and address, so that I can choose between online bargains and immediate local shop pickup.

**Why this priority**: Provides channel clarity and physical convenience. Many riders will gladly pay 50 € more to buy from a local shop with workshop support rather than waiting for shipping from abroad.

**Independent Test**: Toggle "Solo Tiendas Físicas"; verify that all displayed bikes belong to verified brick-and-mortar stores in the user's region, showing store distance in km.

**Acceptance Scenarios**:

1. **Given** the catalog grid, **When** the user activates the "Tiendas Físicas" toggle, **Then** online-only and international retailers are filtered out, displaying only stores with physical location in the target territory with distance indicators.

---

### Edge Cases

- **Zero bikes matching filter criteria**: When the user sets an impossible filter (e.g. budget under 400 € with hydraulic brakes), the dashboard displays a clean empty state with a recommendation of the lowest viable entry price for complete gravel bikes.
- **Offline or disconnected environment**: The dashboard assets (HTML, CSS, JS) are self-contained or cached so the user can browse local catalog data even without an active internet connection.
- **Mobile viewports**: On narrow screens (<640px), filter controls collapse into a mobile drawer or sticky header, ensuring full usability on smartphones.
- **Port already in use**: If the default port (8080) is occupied, the server attempts fallback to the next available port (e.g. 8081) and informs the user.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST launch a local web server with a single CLI command (`python3 gravel_tracker.py --web` or `python3 -m gravel_bot.web`).
- **FR-002**: The web server MUST NOT require any external Node.js, npm, or build-step dependencies (must run entirely on standard Python runtime).
- **FR-003**: The interface MUST provide real-time client-side filtering by budget ceiling (slider), rider height / frame size, transmission type (1x vs 2x), and brake system (hydraulic vs mechanical).
- **FR-004**: The dashboard MUST include an executive "Podio del Presupuesto" banner showing the #1 Best Value and #2 Bargain for the currently selected budget threshold.
- **FR-005**: Each bike card in the grid MUST render: Brand, Model, Asking Price, Original PVP, Discount %, Tier rating badge, Drivetrain group, Brake type, Fork material, Store name & channel type, and a direct purchase button.
- **FR-006**: The interface MUST provide an instant search input allowing the user to search by brand or model name with latency $< 50$ ms.
- **FR-007**: The system MUST provide an interactive 1v1 comparison tool comparing two selected bikes side-by-side with color-coded winner specs.
- **FR-008**: The interface MUST include a toggle to filter strictly for physical stores in the user's declared geographical region.
- **FR-009**: The web application MUST expose a lightweight JSON REST API endpoint (`/api/bikes` and `/api/budget-podio`) to decouple data retrieval from presentation.
- **FR-010**: The user interface MUST be fully responsive and functional on both mobile (375px+) and desktop viewports.

### Key Entities

- **Web Dashboard View**: Represents the single-page application state (active budget, active filters, search query, selected bikes for comparison).
- **Bike Card Model**: Visual representation of a `CleanCandidateBike` including price, discount, tier badge, spec chips, and purchase URL.
- **Comparison Face-Off State**: Pair of selected bike identifiers and calculated differential advantages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dashboard startup time: The web server starts and serves the initial page in $< 1.0$ second.
- **SC-002**: Client-side filter latency: Adjusting budget sliders or filter checkboxes updates the card grid in $< 50$ ms.
- **SC-003**: Zero build dependency overhead: 0 npm packages or JavaScript build tooling required to run the dashboard.
- **SC-004**: Purchase link integrity: 100% of rendered bike cards provide an accessible, active external URL to the vendor.
- **SC-005**: Mobile responsiveness: 100% of core interactions (slider, filters, search, comparison modal) are fully functional on screen widths down to 375px.
- **SC-006**: Noise exclusion fidelity: 0% of cards displayed in the catalog correspond to bare frames, motorized e-bikes, or liquidated stores.

## Assumptions

- The default server port is 8080 (bound to `127.0.0.1` for local privacy), configurable via `--port`.
- Styling is implemented using clean modern CSS with responsive Flexbox/Grid (optionally lightweight CDN utilities) without compilation pipelines.
- Data is read directly from `gravel_madrid.db` using the existing domain models and `budget_optimizer.py`.