# Phase 0 Research: Telegram Alert Formatting & Autonomous Cloud Worker

**Feature**: `005-telegram-alerts-cloud-worker`
**Date**: 2026-10-10

## Research Findings & Architectural Decisions

### 1. Telegram Message Formatting & HTML Escaping
- **Decision**: Standardize all alert formatting on HTML mode (`parse_mode="HTML"`) with strict `html.escape()` applied to all dynamic data fields (brand, model, store name, transmission, brakes, notes) prior to tag insertion.
- **Rationale**: Telegram's MarkdownV2 parser requires escaping more than 18 ASCII characters (including `.`, `-`, `!`, `(`, `)`), which causes frequent parsing failures on real store product titles with punctuation. HTML parsing only requires escaping `<`, `>`, and `&`. Escaping dynamic values with Python's standard `html.escape(str, quote=True)` guarantees zero parse failures.
- **Alternatives Considered**: 
  - MarkdownV2: Rejected due to fragile escaping of dots, dashes, and parentheses in cycling model names (e.g. `1.0`, `LG103-2023`, `(2x10)`).
  - Plain text: Rejected because it cannot provide bold headers, strikethrough prices, or clean hyperlinks.

### 2. Guaranteed Store Links & Inline Keyboard Buttons
- **Decision**: Provide both an embedded hyperlink in the message body and a prominent Telegram `inline_keyboard` button with `[🛒 Ver Oferta en Tienda]` for direct one-tap opening in the browser.
- **Rationale**: In the Telegram mobile client, inline buttons provide the best user experience. Users can immediately open the retailer's product page with a single tap.
- **Alert Quality Gate**: Add a strict check `is_valid_purchase_url(url: str) -> bool`. If a bike does not have an absolute HTTP/HTTPS URL, suppress the alert or resolve the retailer's search URL. Never deliver an alert with a broken or missing link.
- **Alternatives Considered**: Only formatting text links in the body. Rejected: buttons are more noticeable and easier to tap on mobile.

### 3. Autonomous Cloud Processing on Free Infrastructure
- **Decision**: Configure a self-contained, scheduled GitHub Actions workflow (`gravel_cloud_worker.yml`) running in GitHub Cloud every 3 hours (from 06:00 to 21:00 UTC).
- **Rationale**: GitHub Actions provides 2,000 free runner minutes per month for private/public repositories. A pipeline run takes ~40-60 seconds. Running 6 times per day uses ~120-180 minutes per month (less than 10% of the free quota). This frees the user's laptop from running background processes or consuming CPU/battery.
- **Alternatives Considered**:
  - Free VPS / Render / Fly.io container: Requires external account setup, credit card verification, and persistent daemon management. GitHub Actions is already authenticated, native to the repo, and requires zero extra infrastructure.

### 4. Automated Secret Synchronization
- **Decision**: Implement a helper command `gravel_tracker.py cloud-sync` that reads `.env` and sets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as repository secrets using the GitHub CLI (`gh secret set`), and triggers a test cloud execution (`gh workflow run`).
- **Rationale**: Eliminates manual navigation to GitHub repository settings, ensuring one-command cloud deployment.
