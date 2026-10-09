# Telegram Bot Contract: Budget Bike Optimizer

**Feature**: `001-budget-bike-optimizer`
**Target Service**: `gravel_bot/bot_service.py`

## Commands & Triggers

| Trigger | Example | Behavior |
|---|---|---|
| `/presupuesto <EUR>` | `/presupuesto 1000` | Generates the executive 3-card recommendation directly for 1.000 €. Updates user profile budget preference. |
| `/presupuesto` (bare) | `/presupuesto` | Prompts with inline keyboard buttons for common budget brackets (`<800€`, `1.000€`, `1.200€`, `1.500€`, `1.800€`). |
| Bare Numeric Message | `1000` or `1200 €` | If sent in context or after `/presupuesto`, triggers budget recommendation automatically. |
| Inline Button Callback | `budget_preset_1000` | Triggered by clicking `🎯 1.000 €` on interactive Telegram keyboards. |

---

## Message Format (HTML)

```html
🎯 <b>RECOMENDACIÓN TOP PARA TU PRESUPUESTO: 1.000 €</b>
<i>Perfil: 1,69 m (Talla S) | Filtrado: Cero cuadros sueltos, solo gravel 100% real</i>

🥇 <b>1. MEJOR COMPRA EN PRESUPUESTO</b>
🚲 <b>Megamo Jakar 30 Flat-Bar 2027</b>
💰 <b>999 €</b> (<s>1.248 €</s> • Ahorro 20%)
⚙️ Shimano GRX 2x10v • Frenos Hidráulicos • Horquilla Carbono
📏 Talla S (52 cm) • Compatible
🏪 Biciescapa Madrid (Tienda física)
⭐ Nota: <b>9.7 / 10 (Tier S+)</b>
🔗 <a href="...">Ver y Comprar en Tienda</a>

🥈 <b>2. MEJOR CHOLLO / PRECIO MÁS AJUSTADO</b>
🚲 <b>Van Rysel Gravel GRVL AF</b>
💰 <b>899 €</b> (Ahorras 100 € de tu presupuesto)
⚙️ Sram Apex 1x11v • Doble Pistón • Horquilla Carbono
📏 Talla S (51-52 cm)
🏪 Decathlon Usera / Madrid
🔗 <a href="...">Ver y Comprar en Tienda</a>

🚀 <b>3. SMART STRETCH (+50 € que merecen la pena)</b>
🚲 <b>Cube Nuroad Race</b> — <b>1.050 €</b>
💡 <i>Por 50 € más sobre tu presupuesto, desbloqueas Shimano GRX 810 2x11v completo frente a 2x10v.</i>
🏪 Buycycle España (Garantía certificada)
🔗 <a href="...">Ver y Comprar en Tienda</a>
```

## Inline Keyboards

Below the message, the bot appends inline buttons:
- `[🔄 Cambiar Presupuesto]` (Prompts input or shows presets)
- `[⚔️ Comparar #1 vs #2]` (Triggers `/vs` comparison)
- `[📍 Ver Tiendas Físicas]` (Shows physical store locations for the top options)