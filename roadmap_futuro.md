# Hoja de Ruta y Arquitectura de Futuro: Gravel Bot Ecosystem

Este documento recoge las propuestas de mejora, evolución funcional y arquitectura técnica para convertir el rastreador de ofertas en una plataforma multiusuario personalizada, escalable y con base de conocimiento dinámico sobre componentes ciclistas.

---

## 🗺️ Visión General: Fases de Evolución

```
Fase 1: Motor Multi-Perfil en Telegram (Configuración Dinámica de Usuario)
       ↳ Creación interactiva de perfiles (/setprofile: altura, presupuesto, 1x/2x, zona)
       ↳ Alertas personalizadas en tiempo real según el perfil de cada usuario

Fase 2: Base de Conocimiento Dinámica de Componentes (Knowledge Base v2)
       ↳ Matriz desacoplada de grupos, frenos y ruedas
       ↳ Puntuación ponderada actualizable sin tocar el código central

Fase 3: Infraestructura de Rastreo Avanzado y Segunda Mano
       ↳ Bypass de protecciones Cloudflare/Akamai mediante navegadores headless ligeros
       ↳ Integración con marketplaces de ocasión (Wallapop, Buycycle, Tuvalum API)

Fase 4: Motor Biomecánico y Simulador de Desarrollos
       ↳ Cálculo automático de ratio Stack/Reach por talla
       ↳ Simulador de desarrollos (Gear Inches, cadencia a 30 km/h y ratio subida)
```

---

## 🛠️ Fase 1: Personalización Multiusuario vía Telegram Bot

Actualmente el sistema está optimizado para un único perfil prefijado (Sergio, 1,69 m, Méndez Álvaro, 50/50). La evolución natural es convertir el bot en **multiusuario**, permitiendo a cualquier ciclista darse de alta y recibir alertas a su medida.

### 1.1 Modelo de Datos Relacional Multiusuario (`sqlite3`)

Se añadirán las tablas `usuarios` y `preferencias_usuario`:

```sql
-- Gestión de usuarios de Telegram
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_chat_id INTEGER UNIQUE NOT NULL,
    telegram_username TEXT,
    fecha_registro TEXT NOT NULL,
    activo INTEGER DEFAULT 1
);

-- Perfil biomecánico y de uso de cada usuario
CREATE TABLE IF NOT EXISTS perfiles_ciclista (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    estatura_cm INTEGER NOT NULL,            -- ej. 169
    entrepiurna_cm INTEGER,                  -- opcional para afinar talla
    talla_calculada TEXT NOT NULL,           -- S, M, L, etc.
    presupuesto_max REAL NOT NULL,           -- ej. 1200.0
    preferencia_transmision TEXT DEFAULT '2x', -- '2x', '1x' o 'indiferente'
    terreno_asfalto_pct INTEGER DEFAULT 50,  -- ej. 50 (50% asfalto, 50% grava)
    codigo_postal TEXT,                      -- ej. 28045 (Méndez Álvaro)
    alertas_activas INTEGER DEFAULT 1,
    nota_minima_alerta REAL DEFAULT 8.5
);

-- Alertas individualizadas para evitar repetir envíos por usuario
CREATE TABLE IF NOT EXISTS alertas_por_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    bicicleta_id INTEGER REFERENCES bicicletas(id),
    precio_notificado REAL NOT NULL,
    fecha_envio TEXT NOT NULL
);
```

### 1.2 Flujo de Conversación Interactivo en Telegram (`/perfil`)

Mediante botones en línea (*Inline Keyboards*), el bot guiará al usuario en un cuestionario de 4 pasos:

1. **Estatura:** Selección rápida en tramos (`<1,65m`, `1,65-1,72m (Talla S)`, `1,73-1,80m (Talla M)`, `>1,80m (Talla L)`).
2. **Uso Previsto:** 
   * *50% Carretera / 50% Pista* $\to$ Prioriza doble plato (2x10, 2x11, 2x12).
   * *80% Senderos / 20% Asfalto* $\to$ Prioriza monoplato con gran rango (1x11, 1x12) y pasos de rueda >45 mm.
3. **Presupuesto Máximo:** Selector de tope (ej. 1.000 €, 1.300 €, 2.000 € o flexible).
4. **Frecuencia de Notificaciones:** Instantánea por cada ganga vs. Resumen matinal diario.

---

## 🧠 Fase 2: Matriz Dinámica de Componentes (Component Knowledge Base)

Conforme Shimano, SRAM o Microshift lanzan nuevos grupos (por ejemplo, el nuevo *Shimano CUES Drop-Bar*, *SRAM Transmission Gravel* o *Campagnolo Ekar GT*), las puntuaciones no deben estar hardcodeadas en funciones `if/elif`, sino en una **matriz de componentes versionada en base de datos o JSON**.

### 2.1 Estructura de la Base de Componentes

```json
{
  "transmisiones": {
    "shimano_grx_rx820_2x12": {
      "marca": "Shimano",
      "tipo": "2x12",
      "accionamiento": "mecanico",
      "puntuacion_asfalto": 10.0,
      "puntuacion_tierra": 9.5,
      "fiabilidad": 9.8,
      "ano_lanzamiento": 2024
    },
    "sram_apex_xplr_axs_1x12": {
      "marca": "SRAM",
      "tipo": "1x12",
      "accionamiento": "electronico_inalambrico",
      "puntuacion_asfalto": 7.5,
      "puntuacion_tierra": 9.8,
      "fiabilidad": 9.2,
      "ano_lanzamiento": 2024
    },
    "microshift_sword_2x10": {
      "marca": "Microshift",
      "tipo": "2x10",
      "accionamiento": "mecanico",
      "puntuacion_asfalto": 8.0,
      "puntuacion_tierra": 8.5,
      "fiabilidad": 8.8,
      "ano_lanzamiento": 2024
    }
  },
  "frenos": {
    "shimano_grx_hidraulico": { "tipo": "hidraulico", "puntos": 25.0, "mantenimiento_facil": true },
    "sram_rival_hidraulico": { "tipo": "hidraulico", "puntos": 24.0, "mantenimiento_facil": false },
    "trp_hyrd_semihidraulico": { "tipo": "semihidraulico", "puntos": 15.0, "mantenimiento_facil": true },
    "tektro_mecanico_cable": { "tipo": "mecanico", "puntos": 8.0, "mantenimiento_facil": true }
  }
}
```

### 2.2 Beneficio Técnico
* Permite actualizar la valoración de un grupo entero o añadir uno nuevo simplemente editando un archivo o ejecutando un comando del bot (`/admin_update_group`).
* Los cálculos de la rúbrica consumen directamente la matriz, adaptando el peso de cada componente al porcentaje de asfalto/tierra configurado por el usuario.

---

## 🌐 Fase 3: Infraestructura de Rastreo Avanzado y Mercado de Segunda Mano

### 3.1 Superación de Bloqueos Anti-Bot (Cloudflare / Akamai)
* **Problema detectado:** Tiendas como Buhobike o Decathlon devuelven `403 Forbidden` o `503 Service Unavailable` a llamadas automáticas básicas.
* **Solución técnica:** Integrar un micro-servicio de extracción headless (*Playwright*, *Crawl4AI* o *Undetected ChromeDriver*) en un contenedor Docker ligero para renderizar JavaScript en sitios complejos, reservando `urllib` ultrarrápido para PrestaShop y tiendas abiertas.

### 3.2 Integración con Plataformas de Segunda Mano entre Particulares
* **Wallapop:** Conectar un worker que sondee la API interna de búsqueda de Wallapop (`/api/v3/general/search?category_ids=12465&keywords=gravel+talla+s`) filtrando por zona de Madrid, eliminando ofertas fraudulentas o sin fotos verificadas.
* **Buycycle & Tuvalum:** Automatizar el sondeo de bicicletas de gravel inspeccionadas por mecánicos con garantía oficial.

---

## 📐 Fase 4: Motor Biomecánico y Simulador de Ratios de Transmisión

### 4.1 Cálculo Automatizado de Desarrollos (Gear Inches & Climbing Ratio)
Incorporar un calculador de desarrollos real:
$$\text{Ratio Mínimo} = \frac{\text{Dientes Plato Pequeño}}{\text{Dientes Corona Grande}}$$
* **Ratio $\le 0.85$ (ej. 30 / 36 = 0.83):** Apto para subir las rampas duras de tierra del Parque Lineal y la Marañosa sin bajarse de la bici ni forzar rodillas.
* **Ratio $> 1.00$ (ej. 34 / 32 = 1.06 de carretera):** Penalización automática en la rúbrica por desarrollo insuficiente para grava.

### 4.2 Detector de Geometría (Stack to Reach Ratio)
* **$\text{Stack} / \text{Reach} > 1.55$:** Geometría relajada (*Gran Fondo / Resistencia*), posición cómoda, ideal para principiantes y rutas largas.
* **$\text{Stack} / \text{Reach} < 1.45$:** Geometría de competición agresiva (*Aero Gravel*), mayor tensión en cervicales y espalda.

---

## 📅 Calendario de Implementación Recomendado

| Sprint | Hito | Entregables Clave |
| :---: | :--- | :--- |
| **Sprint 1** | **Base Multiusuario en Telegram** | Tablas `usuarios` y `perfiles`, comando `/perfil` interactivo y enrutamiento de alertas por `chat_id`. |
| **Sprint 2** | **Desacople de la Matriz de Componentes** | Archivo `components_db.json`, motor de cálculo dinámico y actualización de componentes sin reiniciar el bot. |
| **Sprint 3** | **Ampliación de Tiendas y Wallapop** | Scraper de Wallapop Madrid (filtro radio 25 km) y módulo Playwright para Buhobike / Decathlon. |
| **Sprint 4** | **Simulador de Desarrollos y Biomecánica** | Inclusión de Gear Inches en los mensajes de alerta de Telegram y cálculo de ratio de subida. |
