---
type: architecture
title: Visión General del Sistema
description: Pipeline de extracción multi-fuente, persistencia SQLite y notificaciones Telegram del sistema Gravel Bot.
tags: [arquitectura, pipeline, scrapers, sqlite, telegram, github-actions]
---

# Visión General de la Arquitectura

El sistema rastrea ofertas de bicicletas gravel en España, las evalúa mediante una rúbrica ponderada y notifica las mejores al propietario vía Telegram. Está diseñado para correr como proceso automatizado en GitHub Actions o en local.

```
┌─────────────────────────────────────────────┐
│            gravel_tracker.py                │  ← CLI unificada (punto de entrada)
│  init_db() → run_pipeline() / run_bot()     │
└────────────────┬────────────────────────────┘
                 │
     ┌───────────▼───────────┐
     │   gravel_bot/pipeline │  pipeline.py
     │   run_pipeline()      │
     └───┬───────────────────┘
         │ get_all_scrapers()
         ▼
┌────────────────────────────────────────────────────────┐
│                   Scrapers activos (17)                │
│  Tiendas online:  Mammoth, Sanferbike, Buhobike,       │
│    CiclosCorreder, Bikestocks, Alltricks, Fabregues,   │
│    Bicimarket, BikeDiscount, Decathlon, Escapa         │
│  Outlets / Segunda mano:  BuycycleScraper,             │
│    CanyonOutletScraper, TuvalumScraper,                │
│    WallapopMadridScraper, BicispasajeScraper           │
│  Agregadores: ChollometroScraper,                      │
│    MultiStoreAggregatorScraper, OutletAggregatorScraper│
└───────────────────────┬────────────────────────────────┘
                        │ items: {title, description, price, url, sizes, ...}
                        ▼
           ┌────────────────────────┐
           │  gravel_bot/evaluator  │  evaluator.py
           │  detect_bike_specs()   │  → extrae specs heurísticas del texto
           │  calcular_rubrica()    │  → puntuación ponderada 0-100
           └────────────┬───────────┘
                        │ bike_data dict con puntuacion_total, nota, tier
                        ▼
           ┌────────────────────────┐
           │   gravel_bot/db        │  db.py
           │   upsert_bike()        │  → inserta/actualiza en `bicicletas`
           │   record_price_*()     │  → historial_precios
           │   check_price_drop()   │  → caída de precio significativa
           └────────────┬───────────┘
                        │ si nota ≥ 8.5 y tier S/S+ y precio ≤ 1.450 €
                        ▼
           ┌────────────────────────┐
           │  gravel_bot/notifier   │  notifier.py
           │  send_telegram_alert() │  → Telegram Bot API (HTML)
           └────────────────────────┘
```

---

## Scrapers (`gravel_bot/scrapers/`)

### Base común (`base.py`)
Todos los scrapers heredan de `BaseScraper`. Cada uno implementa el método `scrape() -> List[dict]`.

### Anti-ban (`anti_ban.py`)
Módulo de protección centralizado con delays aleatorios, rotación de User-Agent y headers realistas definidos en `config.py` (`DEFAULT_HEADERS`).

### Fuentes activas

| Categoría | Scrapers |
|---|---|
| Tiendas especializadas | MammothScraper, SanferbikeScraper, BuhobikeScraper, CiclosCorredorScraper, BikestocksScraper, AlltricksScraper, FabreguesScraper, BicispasajeScraper |
| Grandes superficies | DecathlonScraper |
| Outlets directos de marca | CanyonOutletScraper |
| Segunda mano certificada | BuycycleScraper, TuvalumScraper |
| Segunda mano particular | WallapopMadridScraper |
| Agregadores/alertas | ChollometroScraper, MultiStoreAggregatorScraper, OutletAggregatorScraper |
| Descuentos | BikeDiscountScraper, EscapaScraper, BicimarketScraper |

La lista de scrapers activos se declara en `gravel_bot/scrapers/__init__.py` como `ACTIVE_SCRAPERS`.

---

## Motor de Evaluación (`gravel_bot/evaluator.py`)

### `detect_bike_specs(title, description, price, sizes)`
Analiza el texto libre de un anuncio/producto mediante regex y la `KnowledgeBase` dinámica. Extrae:
- Marca (de `KNOWN_BRANDS`, ~35 marcas)
- Disciplina (gravel, carretera, mtb, ebike, ciclocross…)
- Transmisión y tipo (`2x10`, `2x11`, `2x12`, `1x10`, `1x11`, `1x12`…)
- Frenos y tipo (`hidraulico`, `semihidraulico`, `mecanico_doble`…)
- Material de cuadro y horquilla
- Patilla UDH
- Compatibilidad de talla para 1,69 m

### `calcular_rubrica(...)` — Fórmula ponderada

```
Puntuación total (0–100) = C1 + C2 + C3 + C4 + C5

C1 — Frenos       (25 pts): hidráulico=25, semihidráulico=15, mecánico doble=10
C2 — Transmisión  (25 pts): 2x10/11/12=25, 1x11/12=18, 1x10=17, 1x9=14
C3 — Cuadro       (20 pts): carbono+carbono=20, aluminio+horquilla carbono=17~20, solo aluminio=6
C4 — Precio       (20 pts): ≤1.150€=20, 1.151–1.300€=15~18, 1.301–1.450€=14, >1.450€=10
C5 — Talla        (10 pts): compatible 1,69m=10, incompatible=2
```

**Tiers:**
- **Tier S+**: ≥ 90 pts
- **Tier S**: ≥ 80 pts
- **Tier A**: ≥ 65 pts
- **Tier B**: ≥ 50 pts
- **Tier C**: < 50 pts (o disciplina ≠ gravel)

Módulos auxiliares del evaluador:
- `knowledge_base.py` — base de conocimiento de grupos de transmisión (`KnowledgeBase.match_drivetrain()`)
- `geometry_sizing.py` — compatibilidad de talla dinámica por estatura y marca
- `biomechanics.py` — evaluación biomecánica de platos/cassette

---

## Persistencia SQLite (`gravel_bot/db.py`)

Base de datos: `gravel_madrid.db` (ruta configurable con `GRAVEL_DB_PATH`).

### Tablas principales

| Tabla | Propósito |
|---|---|
| `bicicletas` | Catálogo de modelos con specs y puntuación. Clave única: `slug` (`marca_modelo_año`). |
| `tiendas` | Registro de tiendas físicas y online con distancia desde Méndez Álvaro. |
| `historial_precios` | Serie temporal de precios por bicicleta y tienda. |
| `alertas_notificadas` | Deduplicación de alertas Telegram (evita spam). |
| `usuarios` | Usuarios Telegram registrados (multiusuario). |
| `perfiles_ciclista` | Preferencias por usuario (estatura, presupuesto, talla, terreno). |
| `alertas_por_usuario` | Alertas enviadas por usuario (sin duplicados). |
| `alertas_talla_usuario` | Watchlist de reposición de talla específica. |
| `sesiones_wizard` | Estado persistente del asistente interactivo paso a paso. |

### Funciones clave

```python
init_db()                         # Crea tablas (idempotente, con migraciones ALTER TABLE)
upsert_bike(bike_data)            # INSERT OR REPLACE en bicicletas
record_price_if_changed(...)      # Registra precio solo si cambió respecto al último
check_price_drop(bike_id)         # Detecta caída de precio significativa
was_alert_sent(bike_id, precio)   # Comprueba deduplicación
mark_alert_sent(bike_id, ...)     # Registra alerta enviada
```

---

## Notificaciones Telegram (`gravel_bot/notifier.py`)

Usa `urllib.request` directamente (sin dependencias externas) contra la Telegram Bot API.

**Criterios de alerta** (definidos en `config.py → ALERT_CRITERIA`):
- `nota_minima`: 8.5 / 10
- `tiers_permitidos`: `["Tier S+", "Tier S"]`
- `max_precio`: 1.450 €
- `exigir_talla_compatible`: True

Dos formatos de mensaje:
- `format_alert_message()` — oferta nueva que supera los criterios
- `format_price_drop_message()` — caída de precio en modelo ya conocido

---

## Detector de Gangas (`gravel_bot/deal_detector.py`)

`get_pure_deals()` — filtra por diferencia de precio pura (independientemente de componentes):
- `min_discount_pct`: descuento mínimo sobre PVP (por defecto 20 %)
- `min_savings_eur`: ahorro mínimo en € (por defecto 100 €)
- Filtros opcionales: `solo_talla_compatible`, `zona_fisica` (tiendas físicas locales), `max_price`

---

## Automatización GitHub Actions

### `gravel_scraper.yml` — Scraper diario
- **Trigger**: cron `0 6 * * *` y `0 7 * * *` UTC (cubre cambio horario CET/CEST), `push`/`PR` a `main`, y `workflow_dispatch`.
- **Pasos**: checkout → Python 3.11 → tests → `--validate --sync-doc` → `--scan` (solo en cron/dispatch) → commit automático de `gravel_madrid.db`, `directorio_bicicletas.md`, `catalog_snapshot.json`.
- Resuelve conflictos binarios en la DB con `git checkout --theirs gravel_madrid.db`.

### `telegram_bot_cloud.yml` — Bot en la nube
- **Trigger**: cron `*/30 * * * *` (cada 30 min), `workflow_dispatch`.
- **Timeout**: 35 minutos por job.
- Ejecuta `python3 gravel_tracker.py --bot 1500` (25 min de polling).
- Persiste cambios en `gravel_madrid.db` y `catalog_snapshot.json` al finalizar.

---

## Flujos de Datos Auxiliares

| Componente | Archivo | Función |
|---|---|---|
| CLI interactiva | `gravel_bot/cli.py` | `cmd_list`, `cmd_deals`, `cmd_daemon` |
| Bot service | `gravel_bot/bot_service.py` | `run_bot_polling()` — procesa comandos Telegram |
| Inspector de bicis | `gravel_bot/bike_inspector.py` | Fichas, comparativas, catálogo |
| Tiendas | `gravel_bot/store_recommender.py` | Recomendaciones por zona |
| URL Ingestor | `gravel_bot/url_ingestor.py` | Scraping puntual de URL de producto |
| Geocoder | `gravel_bot/geocoder.py` | Distancia desde Méndez Álvaro |
| Gear Calculator | `gravel_bot/gear_calculator.py` | Simulador de desarrollos |
| Validator | `gravel_bot/validator.py` | Validación y auto-reparación del catálogo |

---

## Perfil del Ciclista (hardcoded en `config.py`)

```python
RIDER_PROFILE = {
    "estatura_cm": 169,
    "talla_estricta": "S",
    "tallas_admisibles": ["S", "SM", "50", "51", "52"],
    "tallas_especiales": {"canyon": ["XS", "48"], "focus": ["XS", "48"]},
    "zona": "Madrid",
    "presupuesto_objetivo": 1000.0,
    "presupuesto_max_justificado": 1350.0,
}
```
