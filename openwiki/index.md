---
type: concept
title: Índice de Documentación
description: Mapa de páginas de la base de conocimiento del sistema Gravel Bot.
tags: [index, documentacion]
---

# Documentación — Gravel Tracker (gravel-tracker)

Sistema de rastreo automático de ofertas de bicicletas gravel en España, con evaluación ponderada, optimizador de presupuesto (Podio Ejecutivo) y notificaciones Telegram con botón de compra directo.

## Páginas

| Página | Descripción |
|---|---|
| [Guía de Inicio Rápido](quickstart.md) | Todos los comandos CLI reales (podio de presupuesto, dashboard web, auditoría, cloud worker 24/7, Telegram). |
| [Visión General de la Arquitectura](architecture/overview.md) | Pipeline de extracción multi-fuente (16 scrapers), persistencia SQLite, podio ejecutivo por canales y notificaciones Telegram con inline keyboard. |

## Estructura del Proyecto

```
gravel-tracker/
├── gravel_tracker.py            # CLI unificada — punto de entrada único
├── gravel_madrid.db             # Base de datos SQLite (versionada)
├── catalog_snapshot.json        # Snapshot del catálogo en JSON
├── directorio_bicicletas.md     # Tier list auto-generada
├── gravel_bot/
│   ├── config.py                # Configuración centralizada y perfil del ciclista
│   ├── pipeline.py              # Motor de automatización (purga al inicio y fin del rastreo)
│   ├── budget_optimizer.py      # Podio Ejecutivo: mejor compra, ganga, Smart Stretch, ♻️ Ocasión
│   ├── evaluator.py             # Extracción heurística (marcas por frontera de palabra) + rúbrica C1..C6
│   ├── db.py                    # Capa de persistencia SQLite + purga de ruido
│   ├── notifier.py              # Alertas Telegram: HTML estricto, inline keyboard, gate de URL
│   ├── bot_service.py           # Servicio de polling Telegram (wizard, perfiles multiusuario)
│   ├── web_server.py            # Dashboard web interactivo con slider de presupuesto
│   ├── catalog_auditor.py       # Auditoría de enlaces vivos y disponibilidad
│   ├── components_authority.py  # Saneamiento autoritativo de componentes
│   ├── bike_inspector.py        # Fichas técnicas y comparativas 1v1
│   ├── knowledge_base.py        # Base de conocimiento de transmisiones
│   ├── geometry_sizing.py       # Compatibilidad de talla dinámica por estatura y marca
│   ├── validator.py             # Validación, auto-reparación y purga en auditorías
│   ├── gear_calculator.py       # Simulador de desarrollos de transmisión
│   ├── store_recommender.py     # Recomendador de tiendas por zona
│   ├── geocoder.py              # Distancia desde Méndez Álvaro
│   ├── anti_ban.py              # Protección anti-bloqueo para scrapers
│   ├── biomechanics.py          # Evaluación biomecánica de platos/cassette
│   ├── deal_detector.py         # Detector de gangas por precio puro
│   ├── url_ingestor.py          # Ingestión de URLs de productos individuales
│   ├── cli.py                   # Despachador de subcomandos internos
│   ├── web/                     # Recursos estáticos del dashboard
│   └── scrapers/
│       ├── base.py              # Clase base BaseScraper
│       ├── wallapop.py          # Segunda mano particular (Madrid)
│       ├── buycycle.py          # Segunda mano certificada europea
│       ├── canyon.py            # Outlet directo Canyon
│       └── [14 scrapers más; lista activa en scrapers/__init__.py]
├── .github/workflows/
│   ├── gravel_scraper.yml       # Scraper cada 3 horas (06/09/12/15/18/21 UTC)
│   ├── telegram_bot_cloud.yml   # Bot en la nube cada 30 minutos
│   └── gravel_cloud_worker.yml  # Worker autónomo 24/7 (tests + audit + scan + auto-commit)
└── openwiki/                    # Esta documentación
```
