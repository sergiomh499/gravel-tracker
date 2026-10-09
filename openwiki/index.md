---
type: concept
title: Índice de Documentación
description: Mapa de páginas de la base de conocimiento del sistema Gravel Bot.
tags: [index, documentacion]
---

# Documentación — Gravel Bot (valoracion_bicicleta)

Sistema de rastreo automático de ofertas de bicicletas gravel en España, con evaluación ponderada y notificaciones Telegram.

## Páginas

| Página | Descripción |
|---|---|
| [Guía de Inicio Rápido](quickstart.md) | Cómo ejecutar el bot, el scraper y las consultas de precios desde la línea de comandos. |
| [Visión General de la Arquitectura](architecture/overview.md) | Pipeline de extracción multi-fuente (17 scrapers), persistencia SQLite y notificaciones Telegram. |

## Estructura del Proyecto

```
valoracion_bicicleta/
├── gravel_tracker.py          # CLI unificada — punto de entrada
├── gravel_madrid.db           # Base de datos SQLite
├── catalog_snapshot.json      # Snapshot del catálogo en JSON
├── directorio_bicicletas.md   # Tier list auto-generada
├── gravel_bot/
│   ├── config.py              # Configuración centralizada y perfil del ciclista
│   ├── pipeline.py            # Motor de automatización principal
│   ├── evaluator.py           # Extracción heurística de specs + rúbrica ponderada
│   ├── db.py                  # Capa de persistencia SQLite
│   ├── notifier.py            # Alertas Telegram
│   ├── deal_detector.py       # Detector de gangas por precio puro
│   ├── bot_service.py         # Servicio de polling Telegram
│   ├── bike_inspector.py      # Fichas y comparativas de modelos
│   ├── knowledge_base.py      # Base de conocimiento de transmisiones
│   ├── anti_ban.py            # Protección anti-bloqueo para scrapers
│   ├── validator.py           # Validación y auto-reparación del catálogo
│   ├── url_ingestor.py        # Ingestión de URLs de productos individuales
│   ├── store_recommender.py   # Recomendador de tiendas por zona
│   ├── gear_calculator.py     # Simulador de desarrollos de transmisión
│   ├── geometry_sizing.py     # Compatibilidad de talla por estatura y marca
│   ├── biomechanics.py        # Evaluación biomecánica de platos/cassette
│   ├── geocoder.py            # Distancia desde Méndez Álvaro
│   ├── cli.py                 # Subcomandos CLI internos
│   └── scrapers/
│       ├── base.py            # Clase base BaseScraper
│       ├── wallapop.py        # Segunda mano particular (Madrid)
│       ├── buycycle.py        # Segunda mano certificada europea
│       ├── tuvalum.py         # Segunda mano certificada española
│       ├── canyon.py          # Outlet directo Canyon
│       ├── alltricks.py       # Tienda online francesa
│       ├── chollometro.py     # Agregador de chollos
│       ├── multi_store.py     # Agregador multi-tienda
│       ├── outlets.py         # Agregador de outlets
│       └── [12 scrapers más de tiendas especializadas]
├── .github/workflows/
│   ├── gravel_scraper.yml     # Scraper diario + alertas (cron 06/07 UTC)
│   └── telegram_bot_cloud.yml # Bot en la nube cada 30 minutos
└── openwiki/                  # Esta documentación
```
