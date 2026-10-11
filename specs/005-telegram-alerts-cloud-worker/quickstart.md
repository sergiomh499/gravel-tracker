# Quickstart Validation Guide: Telegram Alert Formatting & Cloud Worker

**Feature**: `005-telegram-alerts-cloud-worker`
**Date**: 2026-10-10

## Validation Scenarios

### Scenario 1: Test Telegram Alert Formatting & HTML Escaping
Verifies that text with characters like `<`, `>`, `&` is escaped properly and formats without crashing.

```bash
python3 -c "
from gravel_bot.notifier import format_alert_message, build_telegram_payload

test_bike = {
    'marca': 'Trek <Custom>',
    'modelo': 'Checkpoint & Domane 1.0',
    'tier': 'Tier S+',
    'nota': 9.8,
    'precio_oferta': 999.0,
    'precio_pvp': 1499.0,
    'talla_recomendada_169': 'S (52 cm)',
    'transmision': 'Shimano GRX (2x10)',
    'frenos': 'Hidráulico',
    'cuadro': 'Aluminio & Carbono',
    'tienda_nombre': 'Biciescapa Madrid',
    'url_oferta': 'https://www.escapa.com/bicicletas/checkpoint'
}

msg = format_alert_message(test_bike)
payload = build_telegram_payload(test_bike)
assert '&lt;' in msg
assert '&amp;' in msg
assert payload['reply_markup']['inline_keyboard'][0][0]['url'] == 'https://www.escapa.com/bicicletas/checkpoint'
print('Telegram formatting & inline buttons verified!')
"
```

---

### Scenario 2: Test URL Quality Gate
Verifies that bikes with invalid or missing URLs do not trigger broken alerts.

```bash
python3 -c "
from gravel_bot.notifier import is_valid_purchase_url, send_telegram_alert

assert is_valid_purchase_url('https://www.escapa.com/bicicleta') is True
assert is_valid_purchase_url('ftp://invalid') is False
assert is_valid_purchase_url('') is False
assert is_valid_purchase_url(None) is False

# Alert suppression check
res = send_telegram_alert({'marca': 'Test', 'modelo': 'NoURL', 'url_oferta': ''})
assert res is False, 'Alert with missing URL must be suppressed'
print('URL quality gate verified!')
"
```

---

### Scenario 3: Verify Cloud Sync Command
Verifies that `gravel_tracker.py cloud-sync` executes and validates credentials.

```bash
python3 gravel_tracker.py cloud-sync
```
**Expected Outcome**: Reads `.env`, synchronizes repository secrets via `gh secret set`, and confirms cloud execution readiness.
