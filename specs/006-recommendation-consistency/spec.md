# Feature Specification: Consistencia de Recomendaciones de Cara al Cliente

**Feature Branch**: `006-recommendation-consistency`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "trata de arreglar todas las inconsistencies, de cara al cliente las recomendaciones no son buenas" + "en algunas ocasiones algunos modelos aparecen con el nombre de desconocido"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Podio con solo candidatos de talla verificable (Priority: P1)

Un ciclista de 1,69 m pide una recomendación con presupuesto X. Hoy el podio puede coronar como "Mejor Compra Absoluta" una bici cuya talla es `Dudosa / No compatible` (ej.: Van Rysel GRVL AF de Wallapop a 1200 €). El podio debe excluir cualquier candidato cuya compatibilidad de talla no esté verificada por el motor de tallas, aunque el campo almacenado diga lo contrario.

**Why this priority**: Recomendar una bici que no cabe al usuario es el fallo más grave posible de cara al cliente.

**Independent Test**: Pedir podio a 1200 €; ninguna entrada de los 3 huecos ni del Smart Stretch puede llevar talla "Dudosa", "No compatible" o "incompatible".

### User Story 2 - Cero marcas o modelos "Desconocidos" en salidas de cliente (Priority: P1)

A veces artículos con marca no reconocida se guardan con `marca = "Desconocida"` y aparecen en snapshot, directorio markdown y recomendaciones con nombres basura ("de Gravel", "Cuadro de Bicicleta Gravel de Acero"). Ninguna superficie de cliente (CLI, Telegram, Web, snapshot, markdown) debe mostrar never "Desconocida/Desconocido" como marca ni modelos no identificables.

**Why this priority**: "Desconocido" destruye la confianza del cliente y contamina el ranking con nombres sin sentido.

**Independent Test**: Regenerar snapshot/directorio y lanzar podio: 0 apariciones de "Desconocid" en cualquier salida visible.

### User Story 3 - Separación explícita de canal en el podio (Priority: P1)

Hoy el podio mezcla en un único ranking bicicletas nuevas de tienda y segunda mano de particulares (Wallapop), pudiendo coronar una oferta de particular sin garantía como "Mejor Compra Absoluta" frente a tiendas físicas y online. El podio ejecutivo queda reservado a bicicletas nuevas de tienda (física u online, incluida ocasión certificada con garantía), y los chollos de segunda mano/particulares del presupuesto se presentan en un bloque separado claramente etiquetado "♻️ Ocasión a destacar" (con mención explícita de que no incluye garantía de tienda), para no perder su valor sin engañar al cliente sobre el riesgo.

**Why this priority**: Comprar una bici de particular y una nueva no es comparable en garantía y riesgo; el cliente actualmente recibe la mezcla sin aviso, lo que devalúa toda recomendación.

**Independent Test**: Lanzar podio a 1200 €; ningún hueco de decisiones del podio ejecutivo corresponde a canal particular/segunda mano, y la mejor ganga de segunda mano aparece en su propio bloque etiquetado con mención explícita de ausencia de garantía.

### User Story 4 - Etiquetas legibles y consistentes en todos los canales (Priority: P2)

El podio CLI, el mensaje de Telegram y las fichas muestran token duplicado (`Shimano GRX RX-820 (2x12) 2x12`), calificador de canal duplicado (`Wallapop (Particulares Madrid 25km) (Particular)`), casing mixto (`hidraulico`) y formato asimétrico entre bloques (el #2 muestra menos campos que el #1).

**Why this priority**: Confusa pero no engañosa; afecta percepción de calidad.

**Independent Test**: Renderizar podio en los 3 canales: sin tokens duplicados, sin "(Particular) (Particular)", casing y estructura idénticos entre bloques.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-01**: Todo candidato del podio (incluso Smart Stretch y ganga) DEBE tener verdicto de compatibilidad de talla `True` del motor dinámico antes de entrar (expulsando "Dudosa", "No compatible", placeholders tipo "Consultar tienda").
- **FR-02**: La regla de elegibilidad compartida que alimenta las recomendaciones de presupuesto (CLI, Telegram y Web) DEBE tratar "marca desconocida" como ruido en su único punto de selección de candidatos, de modo que ninguna superficie de cliente reciba bicicletas con marca "Desconocida" o vacía; esto cubre las 3 superficies con una sola regla en lugar de filtros copiados por canal. Además, los registros ya almacenados DEBEN purgarse también en la ruta de rastreo: la rutina de purga existente solo se invoca en auditoría/auto-reparación, nunca durante el pipeline de escaneo, lo que deja una ventana intermedia en la que las superficies de cliente muestran los registros resembrados.
- **FR-03**: Tokens de componentes DEBEN renderizarse una sola vez: si el texto de transmisión ya contiene el tipo (`2x12`, `1x11`) no se añade otra vez.
- **FR-04**: El calificador de canal (`Particular`, `Tienda física`, etc.) DEBE mostrarse una sola vez y con terminología correcta (acentos); no duplicarse cuando el nombre de tienda ya lo indica.
- **FR-05**: Todos los bloques del podio (#1, #2, Smart Stretch, versión Telegram) DEBEN usar el mismo conjunto de campos y casing.
- **FR-06**: Al detectar una marca fallida, el sistema NO DEBE almacenar "Desconocida" como marca en nuevos rastreos; en su lugar DEBE reintentar la identificación con una lista de marcas completa y matching insensible a mayúsculas/apóstrofes contra el texto íntegro del anuncio (título + descripción). Solo si tras ello no hay evidencia de marca alguna, el registro queda excluido de recomendaciones por la regla de ruido (FR-02).
- **FR-07**: Cada cambio de formato DEBE aplicarse en un único punto compartido por CLI, Telegram y Web, no por copia en cada canal.
- **FR-08**: El podio ejecutivo (sus 3 huecos de decisión) DEBE admitir únicamente candidatos con canal tienda física u online nueva (u ocasión certificada con garantía); el canal particular/segunda mano (Wallapop) DEBE figurar, si existe candidato apto del presupuesto, en un bloque separado etiquetado "♻️ Ocasión a destacar" que mencione explícitamente la ausencia de garantía de tienda.

### Assumptions

- Perfil de rider por defecto: 169 cm, Talla S, sin cambio de canal salvo petición.
- El presupuesto es el parámetro de entrada principal; talla objetivo opcional.
- La marca "Desconocida" reaparece tras cada rastreo: el evaluador la usa como valor por defecto cuando no detecta marca, y la rutina de purga existente solo se ejecuta en auditorías/auto-reparación (vía validador), no en cada rastreo. La ausencia actual en la base de datos no garantiza inmunidad futura.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-01**: 100% de entradas de podio llevan una talla con verdicto compatible (0 "Dudosa/No compatible" en #1, #2, stretch) en ejecuciones de aceptación a 500, 1000 y 1200 €.
- **SC-02**: 0 apariciones de "desconocid" (case-insensitive) en snapshot, directorio markdown, podio CLI, mensajes Telegram y fichas.
- **SC-03**: 0 patrones duplicados de tipo `X (Y) Y` en componentes y canales en salidas de aceptación.
- **SC-04**: Suite de tests unitarios refleja las exclusiones anteriores (100% de pruebas en verde).
- **SC-05**: En ejecuciones de aceptación a 500, 1000 y 1200 €, 0 entradas de canal particular/segunda mano ocupan los huecos de decisión del podio ejecutivo, y si existe un chollos de segunda mano apto dentro del presupuesto aparece exactamente una vez en el bloque etiquetado "♻️ Ocasión a destacar" con el aviso de ausencia de garantía de tienda.

## Key Entities *(include if feature involves data)*

- **CleanCandidateBike**: candidato saneado que entra al podio; nuevo veredicto de talla obligatoriamente compatible.
- **VeredictoDeTalla**: salida del motor dinámico `(compatible, talla, motivo)`; es la única fuente de verdad para filtrar.
- **Marca**: etiqueta del fabricante; valor reservado "Desconocida" ya no es válido como marca almacenable.

## Clarifications

### Session 2026-10-12

- Q: ¿Qué hacer con bicis de marca no reconocida ("Desconocida")? → A: Mejorar la detección de marca (lista completa, insensible a mayúsculas, contra el texto íntegro del anuncio); las que sigan sin evidencia de marca quedan excluidas de recomendaciones por la regla de ruido (FR-06 y FR-02 actualizados en consecuencia).
- Q: ¿Cómo deben aparecer los chollos de segunda mano/particulares en el podio de recomendaciones? → A: Podio ejecutivo reservado a bicis nuevas de tienda (o ocasión certificada con garantía) + bloque separado "♻️ Ocasión a destacar" para la mejor oferta de segunda mano/particular del presupuesto, mencionando explícitamente la ausencia de garantía (US3 y FR-08 actualizados en consecuencia).

## Edge Cases

- Modelo extranjero con marca válida pero tallas solo en "cm" numéricos (`54`, `51-52`): DEBE aceptarse como talla válida si el motor la clasifica.
- Anuncio con solo "Consultar tienda" en tallas disponibles pero talla almacenada válida: DEBE conservar la talla almacenada como fuente.
- Bici sin datos de talla verificables ni talla almacenada utilizable: NO debe ocupar el hueco #1 del podio aunque su precio o nota lideren.
