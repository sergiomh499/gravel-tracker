/**
 * Gravel Tracker — Client-Side Reactive Single Page Application
 * Maneja el filtrado a 60fps en memoria, el podio ejecutivo y el duelo 1v1.
 */

// Estado global reactivo en memoria del cliente
const state = {
  allBikes: [],
  filteredBikes: [],
  activeBudget: 1000,
  activeSize: "all",
  activeDrivetrain: "all",
  activeBrakes: "all",
  activeChannel: "all",
  searchQuery: "",
  sortBy: "vfm",
  compareSelection: [] // IDs seleccionados (máx 2)
};

// Elementos del DOM
const el = {
  headerStats: document.getElementById("header-stats"),
  podiumGrid: document.getElementById("podium-grid"),
  podiumSubtitle: document.getElementById("podium-subtitle"),
  budgetSlider: document.getElementById("budget-slider"),
  budgetVal: document.getElementById("budget-val"),
  presetBtns: document.querySelectorAll(".preset-btn"),
  searchInput: document.getElementById("search-input"),
  sortSelect: document.getElementById("sort-select"),
  catalogCountText: document.getElementById("catalog-count-text"),
  bikeGrid: document.getElementById("bike-grid"),
  compareBtn: document.getElementById("compare-btn"),
  compareCount: document.getElementById("compare-count"),
  clearCompareBtn: document.getElementById("clear-compare-btn"),
  compareModal: document.getElementById("compare-modal"),
  compareModalBody: document.getElementById("compare-modal-body"),
  modalCloseBtn: document.getElementById("modal-close-btn")
};

// Inicialización de la aplicación
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  fetchStats();
  fetchBikes();
  fetchPodium(state.activeBudget);
});

// Configuración de listeners de eventos reactivos
function setupEventListeners() {
  // Slider de presupuesto
  el.budgetSlider.addEventListener("input", (e) => {
    state.activeBudget = parseFloat(e.target.value);
    el.budgetVal.textContent = state.activeBudget.toLocaleString("es-ES");
    updateActivePresetBtn(state.activeBudget);
    applyFilters();
    debounceFetchPodium(state.activeBudget);
  });

  // Botones rápidos de presupuesto
  el.presetBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const b = parseFloat(btn.dataset.budget);
      state.activeBudget = b;
      el.budgetSlider.value = b;
      el.budgetVal.textContent = b.toLocaleString("es-ES");
      updateActivePresetBtn(b);
      applyFilters();
      fetchPodium(b);
    });
  });

  // Píldoras de filtrado (Talla, Transmisión, Frenos, Canal)
  setupPillGroup("filter-size", (val) => { state.activeSize = val; applyFilters(); });
  setupPillGroup("filter-drivetrain", (val) => { state.activeDrivetrain = val; applyFilters(); });
  setupPillGroup("filter-brakes", (val) => { state.activeBrakes = val; applyFilters(); });
  setupPillGroup("filter-channel", (val) => { state.activeChannel = val; applyFilters(); });

  // Búsqueda en tiempo real
  el.searchInput.addEventListener("input", (e) => {
    state.searchQuery = e.target.value.trim().toLowerCase();
    applyFilters();
  });

  // Ordenación
  el.sortSelect.addEventListener("change", (e) => {
    state.sortBy = e.target.value;
    applyFilters();
  });

  // Duelo comparativo 1v1
  el.compareBtn.addEventListener("click", openCompareModal);
  el.clearCompareBtn.addEventListener("click", clearCompareSelection);
  el.modalCloseBtn.addEventListener("click", closeCompareModal);
  el.compareModal.addEventListener("click", (e) => {
    if (e.target === el.compareModal) closeCompareModal();
  });
}

function setupPillGroup(groupId, callback) {
  const group = document.getElementById(groupId);
  if (!group) return;
  const buttons = group.querySelectorAll(".pill-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      callback(btn.dataset.val);
    });
  });
}

function updateActivePresetBtn(budget) {
  el.presetBtns.forEach((btn) => {
    btn.classList.toggle("active", parseFloat(btn.dataset.budget) === budget);
  });
}

// Carga de datos desde la API REST
async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    if (data.status === "success") {
      el.headerStats.innerHTML = `
        <span class="stat-badge">🚲 ${data.total_active_gravel} Gravels Verificadas</span>
        <span class="stat-badge">💰 Media: ${Math.round(data.avg_price)} €</span>
      `;
    }
  } catch (err) {
    console.error("Error al cargar estadísticas:", err);
  }
}

async function fetchBikes() {
  try {
    const res = await fetch("/api/bikes");
    const data = await res.json();
    if (data.status === "success") {
      state.allBikes = data.bikes;
      applyFilters();
    }
  } catch (err) {
    console.error("Error al cargar catálogo:", err);
    el.bikeGrid.innerHTML = `<div class="error-msg">⚠️ No se pudo cargar el catálogo del servidor.</div>`;
  }
}

let podiumTimeout = null;
function debounceFetchPodium(budget) {
  clearTimeout(podiumTimeout);
  podiumTimeout = setTimeout(() => fetchPodium(budget), 250);
}

async function fetchPodium(budget) {
  try {
    const res = await fetch(`/api/recommend?budget=${budget}&height=169&stretch=true`);
    const data = await res.json();
    if (data.status === "success" || data.status === "no_exact_match") {
      renderPodium(data);
    }
  } catch (err) {
    console.error("Error al cargar podio:", err);
  }
}

// Renderizado del Podio Ejecutivo
function renderPodium(podio) {
  if (!podio.best_value) {
    el.podiumGrid.innerHTML = `
      <div class="podium-card">
        <span class="podium-badge">Sin Opciones Exactas</span>
        <div class="podium-title">Presupuesto inferior a opciones de mercado</div>
        <p class="podium-specs">${podio.stretch_reason || "Prueba a subir el presupuesto a 800€ o 1.000€ para ver opciones completas."}</p>
        ${podio.smart_stretch ? `
          <div class="podium-price-wrap"><span class="podium-price">${podio.smart_stretch.price} €</span></div>
          <a href="${podio.smart_stretch.product_url}" target="_blank" class="podium-btn">Ver Opción Más Cercana</a>
        ` : ""}
      </div>
    `;
    return;
  }

  let html = "";

  // #1 Mejor Compra
  const bv = podio.best_value;
  html += `
    <div class="podium-card winner-card">
      <span class="podium-badge">🥇 #1 Mejor Compra en Presupuesto</span>
      <h3 class="podium-title">${bv.brand} ${bv.model}</h3>
      <div class="podium-price-wrap">
        <span class="podium-price">${Math.round(bv.price)} €</span>
        ${bv.discount_pct > 0 ? `<span class="podium-pvp">${Math.round(bv.pvp)} €</span><span class="podium-discount">-${Math.round(bv.discount_pct)}%</span>` : ""}
      </div>
      <div class="podium-specs">
        <div class="podium-specs-row">⚙️ <b>${bv.drivetrain}</b></div>
        <div class="podium-specs-row">🛑 ${bv.has_hydraulic_brakes ? "Frenos Hidráulicos" : "Frenos Mecánicos"} • ${bv.has_carbon_fork ? "Horquilla Carbono" : "Horquilla Aluminio"}</div>
        <div class="podium-specs-row">🏪 ${bv.store_name} • Talla ${bv.size_compatibility}</div>
      </div>
      <a href="${bv.product_url}" target="_blank" class="podium-btn">Ver Oferta en Tienda →</a>
    </div>
  `;

  // #2 Mejor Ganga
  if (podio.top_bargain) {
    const tb = podio.top_bargain;
    html += `
      <div class="podium-card bargain-card">
        <span class="podium-badge">🥈 #2 Mayor Descuento / Ganga</span>
        <h3 class="podium-title">${tb.brand} ${tb.model}</h3>
        <div class="podium-price-wrap">
          <span class="podium-price">${Math.round(tb.price)} €</span>
          ${tb.discount_pct > 0 ? `<span class="podium-pvp">${Math.round(tb.pvp)} €</span><span class="podium-discount">-${Math.round(tb.discount_pct)}%</span>` : ""}
        </div>
        <div class="podium-specs">
          <div class="podium-specs-row">⚙️ <b>${tb.drivetrain}</b></div>
          <div class="podium-specs-row">🏪 ${tb.store_name} • Talla ${tb.size_compatibility}</div>
          <div class="podium-specs-row">⭐ Nota: ${tb.rubric_nota.toFixed(1)}/10 (${tb.rubric_tier})</div>
        </div>
        <a href="${tb.product_url}" target="_blank" class="podium-btn">Ver Oferta en Tienda →</a>
      </div>
    `;
  }

  // #3 Smart Stretch
  if (podio.smart_stretch) {
    const ss = podio.smart_stretch;
    const diff = Math.round(ss.price - podio.budget);
    html += `
      <div class="podium-card stretch-card">
        <span class="podium-badge">🚀 #3 Smart Stretch (+${diff} €)</span>
        <h3 class="podium-title">${ss.brand} ${ss.model}</h3>
        <div class="podium-price-wrap">
          <span class="podium-price">${Math.round(ss.price)} €</span>
        </div>
        <div class="podium-specs">
          <div class="podium-specs-row">💡 <b>${podio.stretch_reason}</b></div>
          <div class="podium-specs-row">🏪 ${ss.store_name} • Talla ${ss.size_compatibility}</div>
        </div>
        <a href="${ss.product_url}" target="_blank" class="podium-btn">Ver Oferta en Tienda →</a>
      </div>
    `;
  }

  el.podiumGrid.innerHTML = html;
}

// Filtrado reactivo en cliente (60fps)
function applyFilters() {
  let list = state.allBikes.filter((b) => {
    // 1. Presupuesto
    if (b.price > state.activeBudget) return false;

    // 2. Talla
    if (state.activeSize !== "all") {
      const matchSizing = b.available_sizes.some((s) => s.toUpperCase().includes(state.activeSize));
      if (!matchSizing) return false;
    }

    // 3. Transmisión (1x / 2x)
    if (state.activeDrivetrain !== "all") {
      if (!b.drivetrain.toLowerCase().includes(state.activeDrivetrain)) return false;
    }

    // 4. Frenos
    if (state.activeBrakes === "hidraulico" && !b.has_hydraulic_brakes) return false;
    if (state.activeBrakes === "mecanico" && b.has_hydraulic_brakes) return false;

    // 5. Canal de compra
    if (state.activeChannel !== "all") {
      if (b.channel_type !== state.activeChannel) return false;
    }

    // 6. Búsqueda de texto
    if (state.searchQuery) {
      const txt = `${b.brand} ${b.model}`.toLowerCase();
      if (!txt.includes(state.searchQuery)) return false;
    }

    return true;
  });

  // Ordenación
  list.sort((a, b) => {
    if (state.sortBy === "vfm") return b.vfm_index - a.vfm_index;
    if (state.sortBy === "score") return b.rubric_score - a.rubric_score;
    if (state.sortBy === "price_asc") return a.price - b.price;
    if (state.sortBy === "discount") return b.discount_pct - a.discount_pct;
    return 0;
  });

  state.filteredBikes = list;
  renderBikeGrid(list);
}

// Renderizado de las tarjetas del catálogo
function renderBikeGrid(bikes) {
  el.catalogCountText.textContent = `${bikes.length} Bicicletas Encontradas`;

  if (bikes.length === 0) {
    el.bikeGrid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; color: #94a3b8;">
        <span style="font-size: 2.5rem; display:block; margin-bottom: 0.5rem;">🔍</span>
        <h4>No hay bicicletas que cumplan todos los filtros seleccionados</h4>
        <p style="font-size: 0.85rem; margin-top: 0.25rem;">Prueba a ampliar el presupuesto o quitar filtros de frenos/talla.</p>
      </div>
    `;
    return;
  }

  el.bikeGrid.innerHTML = bikes.map((b) => renderBikeCard(b)).join("");

  // Vincular eventos de selección para comparar
  document.querySelectorAll(".btn-compare-card").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = parseInt(btn.dataset.id);
      toggleCompareBike(id);
    });
  });
}

function renderBikeCard(b) {
  const tierClass = b.rubric_tier === "Tier S+" ? "tier-s-plus" :
                    b.rubric_tier === "Tier S" ? "tier-s" :
                    b.rubric_tier === "Tier A" ? "tier-a" : "tier-b";

  const isSelected = state.compareSelection.includes(b.id);

  return `
    <article class="bike-card">
      <div class="card-top">
        <span class="tier-badge ${tierClass}">${b.rubric_tier}</span>
        <span class="score-badge">⭐ ${b.rubric_nota.toFixed(1)}/10</span>
      </div>

      <h4 class="card-title">${b.brand} ${b.model}</h4>

      <div class="card-price-row">
        <span class="card-price">${Math.round(b.price)} €</span>
        ${b.discount_pct > 0 ? `<span class="card-pvp">${Math.round(b.pvp)} €</span><span class="card-discount">-${Math.round(b.discount_pct)}%</span>` : ""}
      </div>

      <div class="card-chips">
        <span class="chip">${b.drivetrain}</span>
        <span class="chip ${b.has_hydraulic_brakes ? 'chip-hydraulic' : ''}">${b.has_hydraulic_brakes ? '💧 Hidráulicos' : '⚙️ Mecánicos'}</span>
        <span class="chip ${b.has_carbon_fork ? 'chip-carbon' : ''}">${b.has_carbon_fork ? '🌱 Carbono' : 'Aluminio'}</span>
        <span class="chip">📏 ${b.size_compatibility}</span>
      </div>

      <div class="card-store">
        <span>🏪</span>
        <span>${b.store_name}</span>
      </div>

      <div class="card-actions">
        <a href="${b.product_url}" target="_blank" class="btn-buy">Ver Oferta</a>
        <button class="btn-compare-card ${isSelected ? 'selected' : ''}" data-id="${b.id}">
          ${isSelected ? '✓ Seleccionada' : '+ Comparar'}
        </button>
      </div>
    </article>
  `;
}

// Lógica de Comparación 1v1
function toggleCompareBike(id) {
  const idx = state.compareSelection.indexOf(id);
  if (idx >= 0) {
    state.compareSelection.splice(idx, 1);
  } else {
    if (state.compareSelection.length >= 2) {
      state.compareSelection.shift(); // Quitar la primera si ya hay 2
    }
    state.compareSelection.push(id);
  }

  updateCompareUI();
  renderBikeGrid(state.filteredBikes);
}

function updateCompareUI() {
  const count = state.compareSelection.length;
  el.compareCount.textContent = count;
  el.compareBtn.disabled = count !== 2;
  el.clearCompareBtn.style.display = count > 0 ? "block" : "none";
}

function clearCompareSelection() {
  state.compareSelection = [];
  updateCompareUI();
  renderBikeGrid(state.filteredBikes);
}

async function openCompareModal() {
  if (state.compareSelection.length !== 2) return;
  const [b1, b2] = state.compareSelection;

  try {
    const res = await fetch(`/api/compare?b1=${b1}&b2=${b2}`);
    const data = await res.json();
    if (data.status === "success") {
      const c = data.comparison;
      el.compareModalBody.innerHTML = `
        <div class="compare-grid">
          <div class="compare-col">
            <h4>${c.bike_a.brand} ${c.bike_a.model}</h4>
            <div class="podium-price">${Math.round(c.bike_a.price)} €</div>
            <p style="font-size:0.8rem; color:#94a3b8;">${c.bike_a.drivetrain} • ${c.bike_a.has_hydraulic_brakes ? 'Frenos Hidráulicos' : 'Frenos Mecánicos'}</p>
            <h5 style="margin-top:0.75rem; font-size:0.85rem; color:#38bdf8;">Ventajas clave:</h5>
            <ul class="advantage-list">
              ${c.advantages_a.length > 0 ? c.advantages_a.map((a) => `<li>${a}</li>`).join("") : "<li>Sin ventajas técnicas directas sobre la rival</li>"}
            </ul>
            <a href="${c.bike_a.product_url}" target="_blank" class="podium-btn" style="margin-top:1rem; display:block;">Ver en Tienda</a>
          </div>

          <div class="compare-col">
            <h4>${c.bike_b.brand} ${c.bike_b.model}</h4>
            <div class="podium-price">${Math.round(c.bike_b.price)} €</div>
            <p style="font-size:0.8rem; color:#94a3b8;">${c.bike_b.drivetrain} • ${c.bike_b.has_hydraulic_brakes ? 'Frenos Hidráulicos' : 'Frenos Mecánicos'}</p>
            <h5 style="margin-top:0.75rem; font-size:0.85rem; color:#38bdf8;">Ventajas clave:</h5>
            <ul class="advantage-list">
              ${c.advantages_b.length > 0 ? c.advantages_b.map((a) => `<li>${a}</li>`).join("") : "<li>Sin ventajas técnicas directas sobre la rival</li>"}
            </ul>
            <a href="${c.bike_b.product_url}" target="_blank" class="podium-btn" style="margin-top:1rem; display:block;">Ver en Tienda</a>
          </div>
        </div>
      `;
      el.compareModal.style.display = "flex";
    }
  } catch (err) {
    console.error("Error en comparativa 1v1:", err);
  }
}

function closeCompareModal() {
  el.compareModal.style.display = "none";
}
