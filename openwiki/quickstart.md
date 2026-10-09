---
type: guide
title: Guía de Inicio Rápido
description: Cómo ejecutar el scraper, el bot de Telegram y las consultas de precios desde línea de comandos.
tags: [quickstart, cli, bot, scraper, sqlite]
---

# Guía de Inicio Rápido

El punto de entrada único del sistema es `gravel_tracker.py`. Todas las operaciones pasan por él.

## Requisitos previos

```bash
# Variables de entorno (o definidas en .env)
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat_id>

# Ruta de la base de datos (por defecto: gravel_madrid.db en el mismo directorio)
# Opcional: GRAVEL_DB_PATH=/ruta/alternativa/gravel_madrid.db
```

El archivo `.env` se carga automáticamente en `gravel_bot/config.py` si existe en la raíz del proyecto.

## Inicializar la base de datos

```bash
python3 gravel_tracker.py
```

Al arrancar, `init_db()` crea las tablas SQLite si no existen (`tiendas`, `bicicletas`, `historial_precios`, `alertas_notificadas`, `usuarios`, `perfiles_ciclista`, `sesiones_wizard`, etc.).

---

## Scraper / Pipeline completo

Lanza todos los scrapers activos, persiste resultados en SQLite y envía alertas Telegram para las mejores ofertas:

```bash
python3 gravel_tracker.py --scan
```

Esto ejecuta `run_pipeline(send_alerts=True, verbose=True)` en `gravel_bot/pipeline.py`, que:
1. Instancia los 17 scrapers activos (ver [Architecture Overview](architecture/overview.md)).
2. Por cada bicicleta raspada: extrae specs con `detect_bike_specs()`, calcula la rúbrica, la persiste con `upsert_bike()` y registra precio en `historial_precios`.
3. Si la nota ≥ 8.5 y el tier es `Tier S` o `Tier S+` y el precio ≤ 1.450 €, dispara alerta Telegram (deduplicada con `alertas_notificadas`).
4. Sincroniza `directorio_bicicletas.md` y exporta `catalog_snapshot.json`.

---

## Bot de Telegram (modo polling)

```bash
# Polling indefinido
python3 gravel_tracker.py --bot

# Polling durante N segundos (usado en GitHub Actions: 1500 s = 25 min)
python3 gravel_tracker.py --bot 1500
```

Llama a `run_bot_polling(duration_seconds=N)` en `gravel_bot/bot_service.py`.

---

## Consultas de precios y ranking

### Ver ranking completo (todos los tiers)
```bash
python3 gravel_tracker.py --list
# Filtrar por tier:
python3 gravel_tracker.py --list "Tier S+"
```

### Buscar gangas (descuento ≥ 15 % por defecto)
```bash
python3 gravel_tracker.py --deals
```

### Chollos por precio puro (descuento ≥ 20 % o ahorro ≥ 100 €)
```bash
python3 gravel_tracker.py --chollos
# Solo tallas compatibles con 1,69 m:
python3 gravel_tracker.py --chollos-talla
# Solo tiendas físicas en una zona:
python3 gravel_tracker.py --chollos-zona --zona Madrid
# Con precio máximo y descuento mínimo personalizados:
python3 gravel_tracker.py --pure-deals 1200 25%
```

### Historial de precios de un modelo
```bash
python3 gravel_tracker.py --historial "Conor Kalima"
```

### Ficha detallada de un modelo
```bash
python3 gravel_tracker.py --info "Conor Kalima"
```

### Catálogo de disponibles
```bash
python3 gravel_tracker.py --catalogo
python3 gravel_tracker.py --catalogo "Tier S"
```

### Estadísticas de la base de datos
```bash
python3 gravel_tracker.py --stats
```

### Comparar dos modelos
```bash
python3 gravel_tracker.py --vs kalima jakar
```

### Simulador de desarrollos (transmisión)
```bash
python3 gravel_tracker.py --desarrollo 2x
```

---

## Ingestión manual de URLs y tiendas

```bash
# Añadir una bicicleta por URL de producto
python3 gravel_tracker.py --add-url https://tienda.com/bicicleta-x

# Registrar una tienda nueva
python3 gravel_tracker.py --add-store "Nombre Tienda" https://tienda.com online

# Añadir modelo interactivamente por CLI
python3 gravel_tracker.py --add
```

---

## Mantenimiento

```bash
# Validar integridad del catálogo (con auto-reparación)
python3 gravel_tracker.py --validate

# Sincronizar directorio_bicicletas.md manualmente
python3 gravel_tracker.py --sync-doc

# Eliminar modelos obsoletos/junior
python3 gravel_tracker.py --purge

# Verificar conexión con Telegram
python3 gravel_tracker.py --test-telegram
```

---

## Automatización con GitHub Actions

| Workflow | Fichero | Frecuencia |
|---|---|---|
| Scraper + alertas | `.github/workflows/gravel_scraper.yml` | Diario 06:00 y 07:00 UTC (horario verano/invierno) |
| Bot Telegram cloud | `.github/workflows/telegram_bot_cloud.yml` | Cada 30 minutos |

El workflow del scraper también ejecuta los tests (`test_new_features.py`, `test_bot.py`, `test_intensive.py`) y valida el catálogo antes de lanzar el scan. Los cambios en `gravel_madrid.db`, `directorio_bicicletas.md` y `catalog_snapshot.json` se commiten automáticamente al repositorio.
