# Sistema de Selección y Valoración de Bicicleta Gravel (~1.000 € - 1.350 €)
*Base Territorial: Méndez Álvaro, Madrid | Perfil: 50% Asfalto / 50% Tierra | Estatura: 1,69 m (Talla S/SM)*

---

## 📌 Índice de la Documentación del Repositorio

El sistema de decisión y auditoría técnica está estructurado en 5 documentos especializados:

1. **[Guía de Compra Territorial (`guia_compra_gravel_mendez_alvaro.md`)](./guia_compra_gravel_mendez_alvaro.md):**
   * Radiografía de rutas ciclistas reales desde Méndez Álvaro (Parque Lineal del Manzanares, La Marañosa, Anillo Verde, Madrid Río/Casa de Campo).
   * Justificación biomecánica y desarrollos necesarios (doble plato 2x vs monoplato 1x).
   * Checklist mecánico de 5 puntos para inspección de bicicletas de ocasión.

2. **[Directorio de Tiendas (`directorio_tiendas.md`)](./directorio_tiendas.md):**
   * **Tiendas Físicas en Madrid:** Sanferbike M-30 (a 800 m a pie), Calmera Ciclismo (Atocha 98), Buhobike (Delicias / Moratalaz) y Decathlon Usera / Madrid Río.
   * **Plataformas Online de Ocasión Certificada con Garantía:** Tuvalum (certificación 100 puntos y 12 meses de garantía), Canyon Outlet (fábrica alemana con 6 años de garantía) y Buycycle.
   * Enlaces directos, distancias a pie y servicios (plan renove, financiación 0%, taller).

3. **[Directorio y Fichas Técnicas de Modelos (`directorio_bicicletas.md`)](./directorio_bicicletas.md):**
   * Fichas detalladas con cuadro, horquilla, transmisión, frenos y talla exacta para 1,69 m.
   * Clasificación por Tiers: **Tier S+ (Compras Maestras)**, **Tier S (Planes B)**, **Tier A (Económicas funcionales)**, **Tier B (Desfasadas)** y **Tier C (Descartes radicales)**.

4. **[Rúbrica de Valoración Técnica (`rubrica_valoracion.md`)](./rubrica_valoracion.md):**
   * Sistema de cálculo objetivo sobre **100 puntos** (escala 0 a 10) con 5 factores ponderados:
     * C1. Frenos y Seguridad (25%)
     * C2. Transmisión y Polivalencia 50/50 (25%)
     * C3. Cuadro, Horquilla y Estándares UDH (20%)
     * C4. Relación Calidad / Precio / Logística Local (20%)
     * C5. Geometría y Adecuación a Talla para 1,69 m (10%)

5. **[Historial de Precios y Seguimiento de Ofertas (`historial_precios.md`)](./historial_precios.md):**
   * Tabla comparativa con PVP original, precio de oferta actual, porcentaje de rebaja, talla del anuncio y estado de stock en tiempo real.

6. **[Hoja de Ruta y Planes Futuros (`roadmap_futuro.md`)](./roadmap_futuro.md):**
   * Propuestas de arquitectura para soporte multiusuario interactivo vía Telegram (`/perfil`).
   * Base de conocimiento dinámica de nuevos componentes (GRX 12v, CUES Drop-Bar, SRAM Transmission).
   * Superación de bloqueos Cloudflare (Playwright/Crawl4AI) e integración con Wallapop y segunda mano.
   * Simulador biomecánico de desarrollos (Gear Inches, Stack/Reach).
---

## ⚠️ Advertencia Crítica de Disciplina: Orbea Terra vs Orbea Avant

* **ORBEA TERRA = GRAVEL (Apta para tu perfil 50/50):**
  * Neumáticos taqueados 700x38c a 45c.
  * Transmisión Shimano GRX (platos 46/30 gravel con piñón grande 36).
  * Frenos hidráulicos potentes para descensos con arenilla.
  * *Tu talla:* **S (51 cm)**.

* **ORBEA AVANT = CARRETERA PURA (Descarte Radical / Tier C):**
  * Neumáticos lisos de carretera 700x28c (cero agarre y pinchazos seguros en tierra).
  * Transmisión de carretera Shimano Tiagra (platos duros 50/34 con piñón 32 o 34).
  * Frenos mecánicos por cable.
  * *Las ofertas de liquidación encontradas en internet corresponden a tallas gigantescas (55 y 57 para estaturas de 1,80 m a 1,93 m).*

---

## 🤖 Gravel Bot: Sistema Automatizado de Scrapping y Alertas Telegram

El repositorio cuenta con un paquete modular en Python (`gravel_bot/`) que rastrea tiendas sin depender de LLMs, parsea componentes, aplica la rúbrica matemática y notifica ofertas top a tu teléfono:

```
gravel_bot/
├── config.py           # Parámetros del ciclista (1,69 m, Méndez Álvaro) y credenciales
├── db.py               # SQLite (tiendas, bicicletas, historial y alertas enviadas)
├── evaluator.py        # Extractor heurístico de componentes y motor de rúbrica
├── notifier.py         # Cliente Telegram Bot API (alertas enriquecidas con HTML)
├── scrapers/           # Módulos específicos por tienda (Sanferbike, Fabregues, Mammoth)
├── pipeline.py         # Orquestador del ciclo completo de escaneo e ingesta
└── cli.py              # Interfaz de línea de comandos unificada
```

### 🚀 Comandos Principales (CLI)

* **Ejecutar escaneo automático de las 17 tiendas y enviar alertas:**
  ```bash
  python3 gravel_tracker.py --scan
  ```
* **Listar ranking de modelos en la base de datos (con filtro opcional):**
  ```bash
  python3 gravel_tracker.py --list "Tier S+"
  ```
* **Comparativa 1v1 directa frente a frente:**
  ```bash
  python3 gravel_tracker.py --vs kalima jakar
  ```
* **Simulador cinemático de desarrollos y cadencia a 75/90/105 rpm:**
  ```bash
  python3 gravel_tracker.py --desarrollo 2x
  python3 gravel_tracker.py --desarrollo 1x
  ```
* **Ver ficha técnica detallada y estadísticas de precio de un modelo:**
  ```bash
  python3 gravel_tracker.py --ficha "Conor Kalima"
  ```
* **Ver mayores gangas por porcentaje de descuento:**
  ```bash
  python3 gravel_tracker.py --deals
  python3 gravel_tracker.py --chollos 1000  # chollos filtrados por tope
  ```
* **Sincronizar monitor de stock en `directorio_bicicletas.md`:**
  ```bash
  python3 gravel_tracker.py --sync-doc
  ```
* **Auditoría e integridad de datos del catálogo (auto-reparación):**
  ```bash
  python3 gravel_tracker.py --validate
  ```
* **Iniciar el Bot interactivo de Telegram (teclados, callbacks y lenguaje natural):**
  ```bash
  python3 gravel_tracker.py --bot
  ```
* **Ejecutar en modo demonio (escaneo periódico en segundo plano):**
  ```bash
  python3 gravel_tracker.py --daemon
  ```
### 📲 Configuración del Bot de Telegram

Para recibir las alertas instantáneas en tu móvil cuando se detecte una ganga en **Tier S+ o Tier S en talla S para 1,69 m**, define las siguientes variables de entorno:

```bash
export TELEGRAM_BOT_TOKEN="tu_token_de_bot_de_BotFather"
export TELEGRAM_CHAT_ID="tu_chat_id_personal"
```

Para verificar la conexión:
```bash
python3 gravel_tracker.py --test-telegram
```
