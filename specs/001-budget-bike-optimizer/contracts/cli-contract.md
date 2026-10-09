# CLI Interface Contract: Budget Bike Optimizer

**Feature**: `001-budget-bike-optimizer`
**Target Binary**: `gravel_tracker.py`

## Command Syntax

```bash
python3 gravel_tracker.py --presupuesto <BUDGET_EUR> [--altura <CM>] [--talla <SIZE>] [--local] [--canal <CANAL>]
# Retrocompatible aliases:
python3 gravel_tracker.py --recomendar <BUDGET_EUR>
python3 gravel_tracker.py --budget <BUDGET_EUR>
```

## Options & Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `<BUDGET_EUR>` | `float` | Positional / first arg | Maximum budget limit in Euros (e.g. `1000`, `1250.50`) |
| `--altura`, `-a` | `int` | `169` (from profile) | Rider height in centimeters (e.g. `175`, `169`) |
| `--talla`, `-t` | `str` | Auto from height | Explicit frame size filter (`S`, `M`, `L`, `51`, `52`...) |
| `--local`, `-l` | Flag | `False` | Filter strictly for physical bike stores in Madrid / user zone |
| `--canal` | `str` | `all` | Purchase channel: `all`, `tienda_fisica`, `online`, `ocasion` |
| `--json` | Flag | `False` | Output structured JSON instead of human-readable terminal table |

---

## Output Formats

### 1. Human-Readable Terminal Card (Default)

```text
==============================================================================================================
🎯 PODIO DE RECOMENDACIÓN PARA TU PRESUPUESTO: 1.000 € (Talla S / 1.69 m)
==============================================================================================================
Evaluados: 142 modelos | Válidos en presupuesto y talla: 18

🥇 1. MEJOR COMPRA ABSOLUTA (Calidad Máxima en Presupuesto)
   • Modelo:     Megamo Jakar 30 Flat-Bar 2027
   • Precio:     999 € (PVP: 1.248 € | Ahorro: -20%)
   • Componentes: Shimano GRX 2x10v | Frenos Hidráulicos | Horquilla Carbono
   • Talla:      S (52 cm) [Compatible 1.69 m]
   • Tienda:     Biciescapa Madrid (Tienda Física - Retiro local)
   • Enlace:     https://...
   • Veredicto:  Puntuación 9.7/10 (Tier S+). La mejor transmisión y frenos hidráulicos dentro de 1.000€.

🥈 2. MEJOR GANGA / CHOLLO OUTLET
   • Modelo:     Van Rysel Gravel GRVL AF
   • Precio:     899 € (PVP: 899 €)
   • Componentes: Sram Apex 1x11v | Frenos Mecánicos de doble pistón | Horquilla Carbono
   • Talla:      S (51-52 cm) [Compatible 1.69 m]
   • Tienda:     Decathlon Usera / Madrid
   • Enlace:     https://...
   • Veredicto:  Ahorras 100€ de tu presupuesto máximo manteniendo excelente geometría y horquilla carbono.

🚀 3. SMART STRETCH (+50 € a +150 € que merecen la pena)
   • Modelo:     Cube Nuroad Race
   • Precio:     1.050 € (+50 € sobre tu presupuesto)
   • Salto Clave: Desbloquea Shimano GRX 810 2x11v completo frente al grupo 2x10v.
   • Tienda:     Buycycle España (Segunda Mano Certificada con Garantía)
   • Enlace:     https://...
==============================================================================================================
```

### 2. JSON Format (`--json`)

```json
{
  "status": "success",
  "budget": 1000.0,
  "rider": {
    "height_cm": 169,
    "size": "S"
  },
  "best_value": {
    "brand": "Megamo",
    "model": "Jakar 30 Flat-Bar 2027",
    "price": 999.0,
    "pvp": 1248.0,
    "discount_pct": 20.0,
    "tier": "Tier S+",
    "nota": 9.7,
    "brakes": "hidraulico",
    "drivetrain": "Shimano GRX 2x10v",
    "store": "Biciescapa Madrid",
    "url": "https://..."
  },
  "top_bargain": {
    "brand": "Van Rysel",
    "model": "Gravel GRVL AF",
    "price": 899.0,
    "pvp": 899.0,
    "discount_pct": 0.0,
    "tier": "Tier S+",
    "nota": 9.7,
    "store": "Decathlon Usera / Madrid",
    "url": "https://..."
  },
  "smart_stretch": {
    "brand": "Cube",
    "model": "Nuroad Race",
    "price": 1050.0,
    "stretch_amount": 50.0,
    "upgrade_reason": "Desbloquea Shimano GRX 810 2x11v completo",
    "url": "https://..."
  }
}
```

## Exit Codes

- `0`: Success (recommendations generated).
- `1`: Invalid arguments or budget $\le 0$.
- `2`: Database error or no data available.