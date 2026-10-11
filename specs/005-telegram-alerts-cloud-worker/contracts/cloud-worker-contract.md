# Interface Contract: Cloud Worker & Telegram Payload

**Feature**: `005-telegram-alerts-cloud-worker`
**Date**: 2026-10-10

---

## 1. Telegram Alert API Contract

### Request Payload (`POST https://api.telegram.org/bot<TOKEN>/sendMessage`)

```json
{
  "chat_id": 4983947,
  "text": "🏆 <b>¡NUEVA GANGA GRAVEL DETECTADA!</b> 🏆\n\n🚲 <b>Modelo:</b> Megamo Jakar 30 2026\n🏅 <b>Calificación:</b> <code>Tier S+</code> | <b>Nota:</b> <b>9.9 / 10</b>\n💰 <b>Precio:</b> <b>1099 €</b> <s>1373 €</s> <b>(-20% | Ahorras 274 €)</b>\n📏 <b>Talla para 1,69 m:</b> <b>S (52 cm)</b> ✅\n📍 <b>Tienda:</b> Biciescapa Madrid\n\n⚙️ <b>Montaje Técnico:</b>\n • <b>Transmisión:</b> Shimano GRX RX-400 (2x10)\n • <b>Frenos:</b> Frenos de disco hidráulicos\n • <b>Cuadro:</b> Aluminio 6061 Hidroformado / Carbono Disc",
  "parse_mode": "HTML",
  "disable_web_page_preview": false,
  "reply_markup": {
    "inline_keyboard": [
      [
        {
          "text": "🛒 Ver Oferta en Tienda",
          "url": "https://www.escapa.com/bicicletas/bicicleta-megamo-jakar-30-2026/"
        }
      ]
    ]
  }
}
```

---

## 2. CLI `cloud-sync` Command Contract

```bash
python3 gravel_tracker.py cloud-sync [--trigger]
```

### Options:
- `--trigger`: Triggers a test execution of the cloud worker immediately via `gh workflow run`.

### Expected Output:
```text
================================================================================
☁️ SINCRONIZACIÓN DE SECRETOS Y CONFIGURACIÓN CLOUD (GitHub Actions)
================================================================================
 * Repositorio remoto: sergiomh499/gravel-tracker
 * Leyendo variables de entorno desde .env...
   - TELEGRAM_BOT_TOKEN: Configurado (***...dJQ)
   - TELEGRAM_CHAT_ID:   4983947
 * Sincronizando secretos en GitHub Secrets vía gh CLI...
   ✅ Secret TELEGRAM_BOT_TOKEN actualizado en GitHub.
   ✅ Secret TELEGRAM_CHAT_ID actualizado en GitHub.
 * Estado del worker en la nube: Listo para ejecución 24/7 sin este ordenador.
================================================================================
```
