# Feature Specification: Catalog Freshness, Spec Audit & Ranking Calibration

**Feature Branch**: `003-audit-catalog-ranking`

**Created**: 2026-10-10

**Status**: Draft

**Input**: User description: "la lista de producto no esta actualizada y contiene informacion erronea, ademas no se si el rankeo esta bien realidado"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Catalog Freshness & Stock Verification (Priority: P1) 🎯 MVP

As a gravel bike buyer, I want the system to continuously audit and verify all catalog listings against live store pages so that out-of-stock items, price changes, and dead links are automatically pruned or updated, ensuring every recommended bike is actively purchasable right now at the stated price.

**Why this priority**: Directly solves the complaint of outdated and stale listings. Recommending bikes that are out of stock or have changed prices destroys trust in the tool.

**Independent Test**: Run the catalog audit on active store listings; verify that out-of-stock models have their stock status flipped to inactive, updated prices are recorded in price history, and dead links (HTTP 404/410) are culled from active recommendations.

**Acceptance Scenarios**:

1. **Given** catalog items with stale prices or depleted stock, **When** the catalog audit runs, **Then** asking prices are synchronized with the live merchant page, and models marked "Sin stock" or "Agotado" are deactivated from active search results.
2. **Given** listings with broken or expired URLs, **When** the audit verifies link health, **Then** dead links are logged and excluded from the recommendation pool.

---

### User Story 2 - Strict Spec Sanitization & Truthful Component Classification (Priority: P2)

As a buyer seeking technical reliability, I want the system to cross-reference extracted bike specifications against an authoritative components knowledge base so that erroneous classifications (e.g., mechanical brakes mislabeled as hydraulic, wrong gear counts, or inflated seller PVPs) are automatically corrected.

**Why this priority**: Solves the complaint of "información errónea". Inaccurate specs corrupt the scoring algorithm. An aluminum fork mislabeled as carbon or mechanical brakes mislabeled as hydraulic produces an artificially inflated rating.

**Independent Test**: Audit listings with ambiguous or conflicting text (e.g. an ad claiming "frenos hidráulicos" for Shimano Claris or Sora); verify that the system cross-checks the component database, corrects the brake type to mechanical, and recalculates the rubric score.

**Acceptance Scenarios**:

1. **Given** a listing with mismatched or misleading descriptions (e.g., "Shimano Claris hidráulico"), **When** the specification audit evaluates the components, **Then** the system overrides the extracted spec with the authoritative standard (Claris = mechanical cable), re-evaluates criteria C1–C5, and flags the listing as corrected.
2. **Given** a private listing with an artificially inflated reference PVP (e.g., claiming 2.000 € PVP for an entry-level bike to fabricate a 60% discount), **When** audited, **Then** the reference PVP is normalized against the manufacturer MSRP truth table.

---

### User Story 3 - Transparent & Calibrated Ranking Rubric with Channel Weighting (Priority: P3)

As a buyer evaluating purchasing options, I want the scoring rubric to be rigorously calibrated, objective, and fully explainable, showing an itemized score breakdown (C1 to C5) and factoring in purchasing safety (official factory warranty vs certified refurbished vs uninspected private sales) so that rankings reflect true real-world value.

**Why this priority**: Directly addresses "no se si el rankeo esta bien realizado". Users need to understand *why* bike A scores higher than bike B. Furthermore, an uninspected private bike should not score a 10.0/10 solely on raw price if it lacks a 3-year warranty and return policy compared to a new bike.

**Independent Test**: Request the itemized score card for any bike in the CLI, Web, or Telegram bot; verify that the system outputs the exact mathematical contribution of each criterion (Frenos /25, Transmisión /25, Cuadro/Horquilla /20, Precio /20, Talla /10, and Channel factor) with plain-text justification.

**Acceptance Scenarios**:

1. **Given** any ranked bike in the catalog, **When** the user inspects its ranking card, **Then** an itemized rubric breakdown is displayed showing points awarded per criterion and why.
2. **Given** a brand-new bike with 3-year warranty and a private second-hand bike with identical specs, **When** ranked, **Then** the ranking formula reflects channel reliability and buyer protection, preventing unverified private sales from unfairly monopolizing top tier positions.

---

### Edge Cases

- **Merchant anti-bot protection blocking live audit**: When a merchant site blocks automated HTTP requests (Cloudflare/WAF), the audit must gracefully fall back to cached data without destroying historical price points, marking the listing as "Verificación pendiente".
- **Discontinued models with missing manufacturer MSRP**: For older models where official MSRP is unavailable, the system estimates reference PVP from comparable model years and flags it with an "Estimado" indicator.
- **Bikes with custom aftermarket upgrades**: For second-hand bikes with verified custom upgrades (e.g. upgraded to carbon wheels or GRX 800), the audit allows verified overrides while keeping unverified seller claims strictly validated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an automated catalog audit command (`python3 gravel_tracker.py --audit` or `--sync-live`) that checks listing freshness and stock availability.
- **FR-002**: The audit pipeline MUST detect HTTP errors (404, 410, 500) and out-of-stock indicators, immediately updating the `en_stock` database flag.
- **FR-003**: The system MUST validate extracted drivetrains and brakes against an authoritative components dictionary (`KnowledgeBase`), ensuring groups (e.g. Claris, Sora, Tiagra, GRX 400/600/810, Apex 1, Rival AXS) strictly map to their true mechanical or hydraulic actuation.
- **FR-004**: The system MUST never assign hydraulic brake points (C1 = 25 pts) to a bicycle unless the brake calipers and levers are verified hydraulic systems.
- **FR-005**: The system MUST sanitize reference PVP prices against manufacturer MSRP boundaries, preventing inflated seller claims from distorting discount rankings.
- **FR-006**: The ranking formula MUST provide an itemized score breakdown (C1 Frenos, C2 Transmisión, C3 Cuadro/Horquilla, C4 Precio real, C5 Talla) accessible via CLI, Web API, and Telegram.
- **FR-007**: The ranking algorithm MUST incorporate a Channel & Warranty Confidence modifier that differentiates brand-new retailer stock (full legal warranty), certified refurbished stock (inspected with guarantee), and private sales (as-is, no warranty).
- **FR-008**: The system MUST record a `fecha_auditoria` timestamp on each catalog item to indicate when its price, stock, and specs were last verified.
- **FR-009**: The system MUST support a re-scoring command (`--re-score`) that recalculates the rubric score and tier for all catalog rows using the calibrated formula.
- **FR-010**: All user-facing interfaces (CLI, Web, Telegram) MUST display a verification badge indicating whether a listing's data was verified by audit or is pending verification.

### Key Entities

- **Authoritative Component Matrix**: Master reference of drivetrains, brake actuation, gear ranges, and manufacturer MSRP benchmarks.
- **Audit Log Record**: Record of verification runs, tracking status code, live price, stock status, and corrected attributes per bicycle.
- **Itemized Score Breakdown**: Comprehensive decomposition of rubric points (C1 through C5 + Channel modifier) for a given bike.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Brake classification accuracy: 100% of bikes classified as having hydraulic brakes are verified hydraulic systems (0% false positives).
- **SC-002**: Active stock fidelity: 100% of top-tier recommendations (Tier S/S+) correspond to listings with active stock and accessible product pages.
- **SC-003**: Discount truthfulness: 0% of active listings exhibit discounts based on unverified PVPs exceeding official manufacturer MSRP by more than 10%.
- **SC-004**: Full explainability: 100% of bikes in the catalog provide an itemized 5-criteria score card upon request.
- **SC-005**: Audit throughput: The complete catalog audit processes at least 20 listings per minute without triggering IP rate limits.

## Assumptions

- Official manufacturer MSRPs for major gravel brands (Megamo, Orbea, Canyon, Scott, Trek, Conor, MMR, Cannondale) can be cataloged in a reference dictionary.
- Private seller listings (e.g. Wallapop) inherently carry greater buyer risk (lack of warranty, wear and tear, potential shipping fraud) than authorized dealers, and the calibrated ranking must objectively reflect this reality.
- When live scraping encounters anti-bot challenges on certain stores, manual URL ingestion (`--add-url`) remains available as a verification fallback.