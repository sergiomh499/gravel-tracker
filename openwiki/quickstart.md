---
type: guide
title: Guía de Inicio Rápido
description: Cómo ejecutar el scraper, el podio de recomendaciones, el dashboard web y el worker cloud desde línea de comandos.
tags: [quickstart, cli, bot, scraper, sqlite, podio]
---

# Guía de Inicio Rápido

El punto de entrada único del sistema es `gravel_tracker.py`. Todas las operaciones pasan por él (`gravel_bot.cli.main()`).

## Requisitos previos

```bash
# Variables de entorno (o definidas en .env)
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat_id>

# Ruta de la base de datos (por defecto: gravel_madrid.db en el mismo directorio)
# Opcional: GRAVEL_DB_PATH=/ruta/alternativa/gravel_madrid.db
```

El archivo `.env` se carga automáticamente en `gravel_bot/config.py` si existe en la raíz del proyecto.

---

## Podio de recomendación por presupuesto (comando principal)

```bash
python3 gravel_tracker.py presupuesto 1200
python3 gravel_tracker.py presupuesto 1000 --altura 169 --talla S
python3 gravel_tracker.py presupuesto 1350 --local            # solo tiendas físicas locales
python3 gravel_tracker.py presupuesto 1500 --canal ocasion    # ocasión certificada
python3 gravel_tracker.py presupuesto 1000 --json             # salida estructurada para scripts
```

`gravel_bot.budget_optimizer.optimize_for_budget()` genera el **Podio Ejecutivo**:
1. 🥇 **Mejor Compra Absoluta** — máxima calidad dentro del presupuesto (desempate por índice VfM `pts/k€`).
2. 🥈 **Mejor Ganga / Precio Más Ajustado** — mayor descuento (≥ 15 % o ahorro ≥ 100 €).
3. 🚀 **Smart Stretch** — el salto de calidad (a ≤ +15 %, máx. +150 €) que vale la pena: hidráulicos, horquilla de carbono o Tier S+.
4. 💡 **Opción de ahorro inteligente** — ≤ 85 % del presupuesto manteniendo el nivel del #1.

**Reglas de higiene del podio (006-recommendation-consistency):**
- Todo candidato ha de verificar **talla compatible para la estatura** mediante el motor dinámico; los veredictos "Dudosa / No compatible" quedan exclusiados.
- **Segunda mano de particulares (Wallapop) no compite en el podio**: aparece en su propio bloque "♻️ OCASIÓN A DESTACAR — ⚠️ SIN garantía de tienda".
- Las bicis sin marca identificable ("Desconocida"/vacío) se tratan como ruido en el punto de selección compartido (CLI, Telegram y Web).
- Se excluyen cuadros sueltos, e-bikes, no-gravel y tiendas cerradas o en liquidación.

---

## Rastreo y alertas

```bash
python3 gravel_tracker.py scan                  # Ronda completa: scrapers → SQLite → alertas Telegram
python3 gravel_tracker.py scan --no-alert       # Igual pero sin notificar
python3 gravel_tracker.py scan --deep           # Escaneo profundo (más paginación; Wallapop)
python3 gravel_tracker.py daemon                # Bucle continuo (intervalo configurable)
python3 gravel_tracker.py daemon --interval 900
```

`run_pipeline()`:
1. **Purga de ruido** al inicio y al final del rastreo (junior, cuadros sueltos, "Desconocida").
2. Instancia los 16 scrapers activos.
3. Por cada bici: `detect_bike_specs()` → rúbrica C1..C6 → `upsert_bike()` con factor garantía → `historial_precios`.
4. Alertas Telegram **solo con enlace de compra válido** (`is_valid_purchase_url`), formato HTML estricto y **botón inline "🛒 Ver Oferta en {Tienda}"**.
5. Bajadas de precio significativas (`check_price_drop`) generan alerta con enlace directo.
6. Sincroniza `directorio_bicicletas.md` y `catalog_snapshot.json`.

---

## Dashboard web interactivo

```bash
python3 gravel_tracker.py web                    # http://127.0.0.1:8080
python3 gravel_tracker.py web --port 9000
```

Slider de presupuesto en tiempo real, filtros por talla/transmisión/tier y fichas con enlace directo. Usa el mismo `budget_optimizer`, por lo que el podio web es idéntico al CLI y al de Telegram.

---

## Telegram (bot polling)

```bash
python3 gravel_tracker.py --bot [segundos]      # Polling del bot (usado en cloud: --bot 1500)
python3 gravel_tracker.py test-telegram          # Verifica auth del bot y envía alerta de prueba con botón
```

Comandos del bot: `/presupuesto`, wizard de configuración paso a paso, perfiles multiusuario, comparativas, talla, etc. Las respuestas a `reply_markup` con teclado inline están disponibles mediante los botones de acción rápidos.

---

## Auditoría y mantenimiento

```bash
python3 gravel_tracker.py audit                  # Comprobar enlaces vivos (default 20)
python3 gravel_tracker.py audit --all --force    # Catálogo completo, ignorando cache de 24 h
python3 gravel_tracker.py audit --tienda "Mammoth"
python3 gravel_tracker.py re-score               # Recalcular rúbrica calibrada C1..C6 + garantía
python3 gravel_tracker.py re-score --dry-run
python3 gravel_tracker.py ficha "Conor Kalima"   # Ficha técnica detallada
python3 gravel_tracker.py vs kalima jakar        # Comparativa 1v1
python3 gravel_tracker.py desarrollo 2x          # Simulador de desarrollos
```

Además, `list` (ranking filtrable por tier, `list "Tier S+"`) y `deals --min-discount 20` (mayores descuentos).

---

## Worker Cloud (ejecución 24/7 en GitHub Actions)

```bash
python3 gravel_tracker.py cloud-sync          # Copia .env → GitHub Secrets (gh secret set)
python3 gravel_tracker.py cloud-sync --trigger  # Además dispara una ejecución de prueba del workflow
```

El workflow `.github/workflows/gravel_cloud_worker.yml` corre **cada 3 h** (06/09/12/15/18/21 UTC) con: tests → `audit` → `re-score` → `scan` con alertas Telegram → auto-commit del catálogo. **No hace falta tener el ordenador encendido**: las alertas de chollos llegan al móvil desde GitHub Actions (plan gratuito, ~2.000 min/mes).

### Automatización con GitHub Actions

| Workflow      | Fichero                              | Frecuencia                  | Qué hace                                  |
|---------------|--------------------------------------|-----------------------------|-------------------------------------------|
| Scraper       | `.github/workflows/gravel_scraper.yml`   | 3 h (06/09/12/15/18/21 UTC) | Tests + `--validate --sync-doc` + `--scan` + auto-commit |
| Bot cloud     | `.github/workflows/telegram_bot_cloud.yml` | Cada 30 min             | 25 min de polling del bot con secrets     |
| Worker 24/7   | `.github/workflows/gravel_cloud_worker.yml` | 3 h (mismas horas) + manual | Tests → audit → re-score → scan → auto-commit |

Todos los workflows commitean `gravel_madrid.db`, `directorio_bicicletas.md` y `catalog_snapshot.json` al finalizar.
