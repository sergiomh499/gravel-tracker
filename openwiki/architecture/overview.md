---
type: architecture
title: Visión General del Sistema
description: Pipeline de extracción multi-fuente, persistencia SQLite, Podio Ejecutivo y notificaciones Telegram del sistema Gravel Bot.
tags: [arquitectura, pipeline, scrapers, sqlite, telegram, github-actions, podio]
---

# Visión General de la Arquitectura

El sistema rastrea ofertas de bicicletas gravel en España, las evalúa mediante una rúbrica calibrada, genera un podio de recomendaciones por presupuesto y notifica los mejores chollos al propietario vía Telegram. Está diseñado para correr como proceso automatizado en GitHub Actions o en local.

```
┌─────────────────────────────────────────────┐
│            gravel_tracker.py                │  ← CLI unificada (punto de entrada)
│  init_db() → run_pipeline() / run_bot()     │
│  presupuesto → optimize_for_budget()        │
└────────────────┬────────────────────────────┘
                 │
     ┌───────────▼───────────┐
     │   gravel_bot/pipeline │  pipeline.py
     │   run_pipeline()      │  → purga de ruido antes y después del rastreo
     └───┬───────────────────┘
         │ get_all_scrapers()
         ▼
┌──────────────────────────────────────────────┐
│              Scrapers activos (16)           │
│  Tiendas online: Mammoth, Sanferbike,        │
│    Buhobike, CiclosCorredor, Bikestocks,     │
│    Alltricks, Fabregues, Bicimarket,         │
│    BikeDiscount, Decathlon, Escapa           │
│  Outlets: CanyonOutlet, OutletAggregator,    │
│    MultiStoreAggregator                      │
│  Segunda mano: Buycycle (certificada),       │
│    Wallapop (particular Madrid)              │
│  Agregador: Chollometro, Bicispasaje         │
└───────────────────────┬──────────────────────┘
                        │ items: {title, description, price, url, sizes, ...}
                        ▼
           ┌─────────────────────────────┐
           │  gravel_bot/evaluator       │  evaluator.py
           │  detect_bike_specs()        │  → marca (frontera de palabra), specs, talla dinámica
           │  calcular_rubrica()/...     │  → rúbrica calibrada C1..C6 + factor garantía
           │  calcular_rubrica_personalizada() → VfM para perfil del usuario
           └────────────┬────────────────┘
                        │ bike_data dict con puntuacion_total, nota, tier
                        ▼
           ┌────────────────────────┐
           │   gravel_bot/db        │  db.py
           │   upsert_bike()        │  → limpia el nombre; upsert en `bicicletas`
           │   record_price_*()     │  → historial_precios
           │   check_price_drop()   │  → caída de precio significativa
           │   purge_obsolete_and_junior_models()  → elimina ruido (junior/Desconocida/test)
           │   get_candidate_bikes_for_budget()    → filas para el optimizador
           └────────────┬───────────┘
                        │ según criterios (nota, tier, precio, URL válida)
                        ▼
    ┌─────────────────────────────────┐  + ┌────────────────────────────────────┐
    │  gravel_bot/budget_optimizer    │    │  gravel_bot/notifier               │
    │  optimize_for_budget()          │    │  send_telegram_alert()             │
    │  → Podio Ejecutivo por canales  │    │  → Telegram Bot API (HTML estricto │
    │  format_budget_recommendation   │    │    + inline_keyboard)              │
    │  format_budget_podio_html()     │    │  gate: is_valid_purchase_url       │
    └─────────────────────────────────┘    └────────────────────────────────────┘
```

---

## Scrapers (`gravel_bot/scrapers/`)

### Base común (`base.py`)
Todos los scrapers heredan de `BaseScraper`. Cada uno implementa el método `scrape() -> List[dict]`.

### Anti-ban (`anti_ban.py`)
Protección centralizada con delays aleatorios, rotación de User-Agent y headers realistas definidos en `config.py` (`DEFAULT_HEADERS`).

### Fuentes activas (`scrapers/__init__.py → ACTIVE_SCRAPERS`, 16)

| Categoría | Scrapers |
|---|---|
| Tiendas especializadas | MammothScraper, SanferbikeScraper, BuhobikeScraper, CiclosCorredorScraper, BikestocksScraper, AlltricksScraper, FabreguesScraper, BicispasajeScraper |
| Grandes superficies | DecathlonScraper |
| Grandes superficies online | BikeDiscountScraper, BicimarketScraper, EscapaScraper |
| Outlets directos | CanyonOutletScraper, OutletAggregatorScraper |
| Segunda mano certificada | BuycycleScraper |
| Segunda mano particular | WallapopMadridScraper |
| Agregadores | ChollometroScraper, MultiStoreAggregatorScraper |

> El scraper de Tuvalum fue eliminado (tienda cerrada / descartada como fuente en 004-prune-codebase-bloat).

---

## Motor de Evaluación (`gravel_bot/evaluator.py`)

### `detect_bike_specs(title, description, price, sizes)`
Analiza el texto libre del anuncio:
- **Marca**: regex por *frontera de palabra* sobre `KNOWN_BRANDS` (~50 marcas, incluyendo `Whyte`, `Centurion`, `Bergamont`, `Sunpeed`, `Liv`, `CBK`…) con mapeo canónico; evita falsos positivos por subcadena (`liv` ≠ `delivery`). Sin evidencia ⇒ `"Desconocida"` (tratada como ruido río abajo).
- **Disciplina**: gravel, carretera, mtb, ebike, ciclocross, junior, no_bicicleta (filtra TVs, llantas, rodillos…).
- **Transmisión** via `KnowledgeBase` dinámica; `transmision` describe el grupo **sin duplicar el tipo** (nunca `1x11 (1x11)`).
- **Frenos**: `hidraulico` / `semihidraulico` / `mecanico_doble` / `mecanico`.
- **Talla** para 1,69 m vía `geometry_sizing.evaluate_size_compatibility_dynamic`.
- **Saneamiento autoritativo** (`components_authority.sanitize_bike_specs`) y recomputo de rúbrica si cambian frenos/cuadro/PVP.

### `calcular_rubrica(...)` / `calcular_rubrica_personalizada(...)` — Rúbrica C1..C6 (calibrada)

```
C1 — Frenos        (25): hidráulico 25 · sem.hidráulico 15 · mecánico doble 10 · mono 6-8
C2 — Transmisión   (25): 2x11/2x12 25 · 2x10 23 · 1x12 20 · 1x11 18 · 1x10 16-17 …
C3 — Cuadro/Material (20): carbono 20 · alu+horquilla carbono 17 · alu pelado 6
C4 — Precio VfM    (20): decresiente según tramos (contacto <950€: 20 …)
C5 — Talla 1,69 m  (10): compatible 10 · "Dudosa/No compatible" 2
C6 — Factor garantía: recarga/penalización por canal (certificada vs particular)
```

**Tiers:** Tier S+ (≥90), Tier S (≥80), Tier A (≥65), Tier B (≥50), Tier C (<50 o no-gravel).

---

## Podio Ejecutivo (`gravel_bot/budget_optimizer.py`)

`optimize_for_budget(budget, height_cm=169, size=None, channel="all", include_stretch=True)`:

1. **Limpieza compartida** (`clean_candidate_from_row`): filtro de ruido (cuadros sueltos, e-bikes, tiendas cerradas, **marca "Desconocida"/vacía**), filtro de talla (el veredicto del motor dinámico es obligatorio; `Consultar tienda` no es talla), dedupe de tokens de transmisión (`_transmision_drivetrain`).
2. **Separación de canal** (FR-08 de 006): el podio admite solo canal `tienda_fisica`, `tienda_online` y `ocasion_certificada` (con garantía). Los particulares (`Wallapop`) se eligen aparte en `best_used_deal` y se renderizan en su propio bloque.
3. **Huecos**: `best_value` (#1, máxima rúbrica, desempate VfM), `top_bargain` (#2, descuento), `smart_stretch` (+15 % máx. +150 € si desbloquea hidráulicos/carbono/Tier S+), `budget_saver` (≤ 85 % del tope con nota cercana), `best_used_deal` (♻️).
4. **Renderers**: `format_budget_recommendation_card` (CLI texto/JSON) y `format_budget_podio_html` (Telegram) comparten helpers (`_frenos_label`, `_channel_suffix`) para garantizar el mismo conjunto de campos y etiquetas.
5. El dashboard web (`gravel_bot/web_server.py`) consume el mismo optimizador.

---

## Persistencia SQLite (`gravel_bot/db.py`)

Base de datos: `gravel_madrid.db` (versión versionada en Git; ruta configurable con `GRAVEL_DB_PATH`).

### Tablas

| Tabla | Propósito |
|---|---|
| `bicicletas` | Catálogo con specs y puntuación. Clave: `slug` (`marca_modelo_año`, invariante al precio). |
| `tiendas` | Tiendas físicas/online con distancia desde Méndez Álvaro. |
| `historial_precios` | Serie temporal de precios por bici/tienda/con stock. |
| `alertas_notificadas` | Deduplicación de alertas Telegram. |
| `usuarios` / `perfiles_ciclista` | Multiusuario y preferencias (estatura, presupuesto, talla, terreno). |
| `alertas_por_usuario` / `alertas_talla_usuario` | Alertas por usuario y watchlist de talla. |
| `sesiones_wizard` | Estado del asistente interactivo de `bot_service`. |

### Funciones clave

```python
init_db()
upsert_bike(bike_data)                  # clean_model_name() elimina marca repetida del modelo
record_price_if_changed(...)            # registra solo si cambia
was_alert_sent / mark_alert_sent        # deduplicación
purge_obsolete_and_junior_models()      # ruido junior/test/Desconocida (se llama desde
                                        # run_pipeline al inicio y al fin del rastreo)
get_candidate_bikes_for_budget()        # candidatos para el optimizador
```

---

## Notificaciones Telegram (`gravel_bot/notifier.py`)

- **Criterios de alerta** (`config.py → ALERT_CRITERIA`): nota mínima 8.5, tiers S/S+, precio máx. 1.450 €, talla compatible obligatoria y de facto **enlace de compra válido** (`is_valid_purchase_url`: http/https absolutos con dominio). Sin URL válida la alerta se suprime y la línea de cálculo registra ⚠️.
- Escapado HTML estricto (`html.escape`) de marca/modelo/tienda/componentes: los `<>&` de los anuncios no rompen `parse_mode=HTML`.
- **Payload con botón inline**: `build_telegram_payload()` genera `reply_markup.inline_keyboard` con `🛒 Ver Oferta en {Tienda}` apuntando al enlace verificado.
- Dos formatos: `format_alert_message()` (nueva oferta) y `format_price_drop_message()` (bajada de precio significativa, con precio anterior tachado).
- Deduplicación con `alertas_notificadas` (alerta solo si el precio de oferta es nuevo para esa bici).

---

## Automatización GitHub Actions

| Workflow | Trigger | Pasos |
|---|---|---|
| `gravel_scraper.yml` | cron `0 6,9,12,15,18,21 * * *`, push/PR a main | Python 3.11 → tests → `--validate --sync-doc` → `--scan` → auto-commit (conflictos binarios en la DB se resuelven con `git checkout --theirs gravel_madrid.db`) |
| `telegram_bot_cloud.yml` | cron `*/30 * * * *` | `--bot 1500` (25 min polling) → auto-commit |
| `gravel_cloud_worker.yml` | cron `0 6,9,12,15,18,21 * * *` + `workflow_dispatch` | tests → `audit --limit 40` → `re-score` → `scan` con `TELEGRAM_*` secrets → auto-commit |

Secrets clonados desde el equipo con `python3 gravel_tracker.py cloud-sync` (CLI `gh secret set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID`).

---

## Perfil del Ciclista (por defecto en `config.py`)

```python
RIDER_PROFILE = {
    "estatura_cm": 169,
    "estatura_m": 1.69,
    "talla_estricta": "S",
    "tallas_admisibles": ["S", "SM", "50", "51", "52"],
    "tallas_especiales": {"canyon": ["XS", "48"], "focus": ["XS", "48"]},
    "zona": "Madrid",
    "presupuesto_objetivo": 1000.0,
    "presupuesto_max_justificado": 1350.0,
}
```
