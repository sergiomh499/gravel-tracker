# Data Model: Telegram Alert Formatting & Cloud Worker

**Feature**: `005-telegram-alerts-cloud-worker`
**Date**: 2026-10-10

## Entities & Interfaces

### 1. `FormattedAlertPayload`

Represents the sanitized, escaped Telegram notification ready for delivery.

| Field | Type | Description |
|---|---|---|
| `text` | `str` | Strict HTML-escaped text with `<b>`, `<i>`, `<s>`, `<code>` markup. |
| `reply_markup` | `Dict[str, Any]` | Telegram `inline_keyboard` with `url` button to the store. |
| `parse_mode` | `str` | Fixed to `"HTML"`. |
| `chat_id` | `Union[int, str]` | Destination Telegram Chat ID. |
| `url_verified` | `bool` | True if product has a valid `https://` purchase link. |

### 2. `InlineButtonDefinition`

| Field | Type | Example |
|---|---|---|
| `text` | `str` | `"🛒 Ver Oferta en Tienda"` |
| `url` | `str` | `"https://www.escapa.com/bicicletas/jakar-30"` |

### 3. Cloud Worker Configuration & Secrets

| Secret / Config | Destination | Purpose |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | GitHub Secrets | Telegram bot token for cloud alert delivery. |
| `TELEGRAM_CHAT_ID` | GitHub Secrets | User chat ID for notifications. |
| `GRAVEL_PROXIES` | GitHub Secrets (Optional) | Rotating proxy list if anti-bot challenges occur. |
