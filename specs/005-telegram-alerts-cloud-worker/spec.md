# Feature Specification: Telegram Alert Formatting & Autonomous Cloud Worker

**Feature Branch**: `005-telegram-alerts-cloud-worker`
**Created**: 2026-10-10
**Status**: Draft
**Input**: User description: "los mensajes de telegram no aparecen bien formateado, muchos sin el enlace a la tienda correctamente, ademas el procesado de todo lo debe hacer un servidor aparte gratuito, no este ordenador"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pristine Telegram Alert Formatting with Guaranteed Store Links (Priority: P1)

As a cyclist receiving Telegram alerts on my phone, I want notifications to have clean, readable typography with guaranteed clickable purchase links and inline action buttons, so that I can immediately review the deal and jump directly to the store without broken formatting or missing URLs.

**Why this priority**: Directly resolves user frustration with unformatted messages, broken HTML tags, and missing store links that prevent purchasing.

**Independent Test**: Trigger a sample deal notification and price drop alert; verify Telegram renders clean bold headers, emojis, sanitized specs, and a functioning clickable button `[🛒 Ver Oferta en Tienda]`.

**Acceptance Scenarios**:
1. Given a bicycle deal with a valid URL, the Telegram message formats with clean HTML typography and includes both a clickable text link and an inline button linking directly to the store product page.
2. Given a bicycle with special characters (`<`, `>`, `&`) in title, model or store name, all text is properly escaped to prevent Telegram HTML parse errors.
3. Given a bicycle without a valid `https://` purchase link, the alert is suppressed or routes to the store search URL, never emitting broken or blank link tags.

---

### User Story 2 - Autonomous Free Cloud Worker Execution (Priority: P1)

As a user, I want all scraping, auditing, and alert dispatching to run 100% on a free external cloud server (GitHub Actions), so that my personal computer does not consume CPU, battery, or network bandwidth, and alerts continue arriving 24/7 even when my laptop is turned off.

**Why this priority**: Fulfills the core constraint that local machine processing must be eliminated in favor of an independent, free cloud environment.

**Independent Test**: Trigger the cloud worker via `gh workflow run` or wait for scheduled cron; verify the cloud worker executes scraping, audits catalog links, sends Telegram alerts, commits database state, and finishes without local machine involvement.

**Acceptance Scenarios**:
1. Given GitHub repository secrets configured with Telegram credentials, the GitHub Actions cloud workflow runs on schedule (every 3 hours) and under manual dispatch without requiring local execution.
2. The workflow automatically persists the updated SQLite database and markdown catalog directly to the Git repository.
3. A helper script or CLI command verifies that Telegram credentials in `.env` are mirrored to GitHub repository secrets seamlessly.

---

### User Story 3 - Alert Link Quality Gate (Priority: P2)

As a deal hunter, I want alerts to be filtered by link quality so that I only receive notifications for products with verifiable, direct purchase links.

**Why this priority**: Eliminates alert noise and spam for catalog items that cannot be purchased online or in-store.

**Independent Test**: Simulate deal discovery with empty URL and verify notification pipeline skips sending alerts for incomplete records.

**Acceptance Scenarios**:
1. Pipeline validates `url_oferta` format (must start with `http://` or `https://`).
2. If `url_oferta` is missing or invalid, notification is logged as skipped with reason "URL no disponible".

---

## Functional Requirements *(mandatory)*

- **FR-001**: Telegram alert formatters (`format_alert_message`, `format_price_drop_message`) MUST use strict HTML escaping (`html.escape`) for all dynamic database strings to prevent Telegram HTML parse failures.
- **FR-002**: Every Telegram alert MUST provide a prominent, verified direct store link via `<a>` hyperlink and inline button (`inline_keyboard`).
- **FR-003**: The notification dispatcher MUST suppress alerts for bicycles lacking a valid URL (`http://` or `https://`).
- **FR-004**: The project MUST provide an autonomous GitHub Actions workflow (`.github/workflows/gravel_cloud_worker.yml`) that executes the entire pipeline in the cloud for free without local machine dependency.
- **FR-005**: The workflow MUST run on an automated cron schedule (every 3 hours during day hours: 06:00, 09:00, 12:00, 15:00, 18:00, 21:00 UTC) and support manual on-demand dispatch (`workflow_dispatch`).
- **FR-006**: The repository MUST include a synchronization command or script (`gravel_tracker.py cloud-sync` or CLI argument) to sync local Telegram credentials to GitHub secrets using `gh secret set`.
- **FR-007**: Cloud execution MUST automatically commit database and catalog state back to the repository using bot git credentials with conflict resolution.

---

## Success Criteria *(mandatory)*

- **SC-001**: 100% of Telegram alerts sent contain an active, clickable store purchase link.
- **SC-002**: 0% Telegram API 400 Bad Request errors caused by unescaped HTML characters.
- **SC-003**: 100% of pipeline processing and periodic alerting operates in cloud execution without requiring the local machine to be turned on.
- **SC-004**: Free tier quota on GitHub Actions remains well below limits (< 150 minutes/month used out of 2,000 free minutes).

---

## Assumptions

- User has GitHub CLI (`gh`) authenticated with repository write access to sync repository secrets.
- Telegram Bot API permits inline keyboard buttons with standard web URLs.
- GitHub Actions provides sufficient free runner capacity (2,000 minutes/month) to run 1-minute scraping batches 6-8 times per day (~240 minutes/month).
