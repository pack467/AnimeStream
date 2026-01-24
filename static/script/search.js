// static/script/search.js
document.addEventListener("DOMContentLoaded", () => {
  /* ==================================================
     0. CONFIG
  ================================================== */
  const API_URL = window.SEARCH_API_URL || "/api/search/";
  const WATCH_BASE = window.WATCH_URL || "/watch/";
  const IS_AUTHENTICATED = window.IS_AUTHENTICATED || false;
  const DEFAULT_SORT = window.DEFAULT_SORT || "popular";  // ✅ Dynamic dari template
  const SECTION_TITLE = window.SECTION_TITLE || "";      // ✅ Dynamic section title

  console.log('✅ Search initialized with default sort:', DEFAULT_SORT);

  /* ==================================================
     1. STATE
  ================================================== */
  let state = {
    q: "",
    page: 1,
    per_page: 12,
    sort: DEFAULT_SORT,  // ✅ Gunakan default dinamis
    view: "grid",
    min_rating: 0.0,
    filters: {
      genre: [],
      year: [],
      status: [],
      type: [],
      age: [],
    },
    total: 0,
    total_pages: 1,
    lastResults: [],
  };

  /* ==================================================
     2. ELEMENTS
  ================================================== */
  const el = {
    toastContainer: document.getElementById("toastContainer"),
    header: document.getElementById("mainHeader"),
    backToTop: document.getElementById("backToTop"),
    mobileToggle: document.getElementById("mobileToggle"),
    navbar: document.getElementById("navbar"),
    searchTrigger: document.getElementById("searchTrigger"),
    userBtn: document.getElementById("userBtn"),
    userDropdown: document.getElementById("userDropdown"),
    mainSearchInput: document.getElementById("mainSearchInput"),
    mainSearchBtn: document.getElementById("mainSearchBtn"),
    searchSuggestions: document.getElementById("searchSuggestions"),
    resultsGrid: document.getElementById("resultsGrid"),
    resultsCount: document.getElementById("resultsCount"),
    totalResults: document.getElementById("totalResults"),
    noResults: document.getElementById("noResults"),
    resetSearch: document.getElementById("resetSearch"),
    hasilPencarianBtn: document.getElementById("hasilPencarianBtn"),
    activeFilters: document.getElementById("activeFilters"),
    applyFilters: document.getElementById("applyFilters"),
    resetFilters: document.getElementById("resetFilters"),
    ratingSlider: document.getElementById("ratingSlider"),
    ratingValue: document.getElementById("ratingValue"),
    viewOptions: document.querySelectorAll(".view-option"),
    filterToggles: document.querySelectorAll(".filter-toggle"),
    pagination: document.querySelector(".pagination"),
    paginationPrev: document.querySelector(".pagination-btn.prev"),
    paginationNext: document.querySelector(".pagination-btn.next"),
    paginationNumbers: document.querySelector(".pagination-numbers"),
    quickTags: document.querySelectorAll(".quick-search-tags .tag"),
    recommendedRadio: document.querySelector('input[name="sort"][value="recommended"]'),
    ageMatchRadio: document.querySelector('input[name="sort"][value="age-match"]'),
    sortRadios: document.querySelectorAll('input[name="sort"]'),
  };

  /* ==================================================
     3. UTILS
  ================================================== */
  const escapeHtml = (str) =>
    String(str ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const escapeAttr = (str) => escapeHtml(str).replaceAll("`", "&#096;");

  const debounce = (fn, wait = 250) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), wait);
    };
  };

  function showToast(message, detail = "", type = "success") {
    if (!el.toastContainer) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    const icon = type === "success" ? "fa-check-circle" : "fa-exclamation-circle";

    toast.innerHTML = `
      <div class="toast-icon"><i class="fas ${icon}"></i></div>
      <div class="toast-content">
        <div class="toast-message">${escapeHtml(message)}</div>
        ${detail ? `<div class="toast-detail">${escapeHtml(detail)}</div>` : ""}
      </div>
    `;

    el.toastContainer.appendChild(toast);

    setTimeout(() => toast.classList.add("show"), 10);
    setTimeout(() => {
      toast.classList.add("hide");
      setTimeout(() => toast.remove(), 300);
    }, 2500);
  }

  function scrollToResults() {
    document.querySelector(".results-header")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function toQS(params) {
    const u = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v === undefined || v === null) return;
      if (Array.isArray(v)) {
        if (v.length) u.set(k, v.join(","));
      } else if (String(v).trim().length) {
        u.set(k, String(v));
      }
    });
    return u.toString();
  }

  function normalizeSort(val) {
    // ✅ Biarkan semua nilai sort dikirim ke API, gunakan default jika kosong
    return val || DEFAULT_SORT;
  }

  /* ==================================================
     4. API CALL
  ================================================== */
  async function fetchSearch({ forSuggestions = false } = {}) {
    const qs = toQS({
      q: state.q,
      page: state.page,
      per_page: forSuggestions ? 8 : state.per_page,
      sort: state.sort,
      min_rating: state.min_rating,
      genres: state.filters.genre,
      years: state.filters.year,
      status: state.filters.status,
      type: state.filters.type,
      age_ratings: state.filters.age,
    });

    const res = await fetch(`${API_URL}?${qs}`, { 
      headers: { Accept: "application/json" } 
    });
    
    if (!res.ok) throw new Error("Search API error");
    return res.json();
  }

  /* ==================================================
     5. RENDER RESULTS
  ================================================== */
  function buildCard(item) {
    const id = item.id;
    const title = item.title || "-";
    const rating = Number(item.rating || 0).toFixed(2);
    const year = item.year || "-";
    const episodes = item.episodes ? `${item.episodes} EP` : "EP";

    const coverSrc =
      item.cover && item.cover.startsWith("http")
        ? item.cover
        : item.cover
        ? item.cover
        : "https://via.placeholder.com/400x600?text=No+Cover";

    const genres = Array.isArray(item.genres) ? item.genres : [];
    const genreHtml = genres.slice(0, 3).map(g => `<span class="genre-badge">${escapeHtml(g)}</span>`).join("");

    const watchUrl = `${WATCH_BASE}${id}/`;

    return `
      <div class="anime-card" data-id="${escapeAttr(id)}">
        <a href="${escapeAttr(watchUrl)}" class="card-link">
          <div class="card-poster">
            <img src="${escapeAttr(coverSrc)}" alt="${escapeAttr(title)}">
            <div class="card-overlay">
              <div class="play-indicator">
                <i class="fas fa-play"></i>
                <span>Watch Now</span>
              </div>
            </div>
            <div class="card-badges">
              <span class="ep-badge">${escapeHtml(episodes)}</span>
            </div>
          </div>
          <div class="card-detail">
            <h3 class="anime-title">${escapeHtml(title)}</h3>
            <div class="genre-badges-bottom">${genreHtml}</div>
            <div class="anime-meta">
              <span class="meta-rating"><i class="fas fa-star"></i> ${rating}</span>
              <span class="meta-year"><i class="fas fa-calendar"></i> ${escapeHtml(year)}</span>
            </div>
          </div>
        </a>
        <div class="card-actions">
          <button class="action-btn-card add-to-list" title="Add to List" data-anime-id="${escapeAttr(id)}">
            <i class="fas fa-plus"></i>
          </button>
          <button class="action-btn-card add-to-favorite" title="Add to Favorites" data-anime-id="${escapeAttr(id)}">
            <i class="far fa-heart"></i>
          </button>
        </div>
      </div>
    `;
  }

  function applyViewMode() {
    if (!el.resultsGrid) return;
    if (state.view === "list") el.resultsGrid.classList.add("list-view");
    else el.resultsGrid.classList.remove("list-view");

    el.resultsGrid.querySelectorAll(".anime-card").forEach(card => {
      if (state.view === "list") card.classList.add("list-view");
      else card.classList.remove("list-view");
    });
  }

  function renderResults(json) {
    state.total = json.total || 0;
    state.total_pages = json.total_pages || 1;
    state.lastResults = json.results || [];

    console.log(`📊 Rendering ${state.lastResults.length} results for sort: ${state.sort}`);

    if (el.resultsCount) el.resultsCount.textContent = String(state.lastResults.length);
    if (el.totalResults) el.totalResults.textContent = String(state.total);

    if (!el.resultsGrid) return;

    if (state.lastResults.length === 0) {
      if (el.noResults) el.noResults.style.display = "block";
      el.resultsGrid.style.display = "none";
      if (el.pagination) el.pagination.style.display = "none";
      return;
    }

    if (el.noResults) el.noResults.style.display = "none";
    el.resultsGrid.style.display = "";

    // ✅ Update header berdasarkan SECTION_TITLE atau jenis sort
    const header = document.querySelector(".results-header h2");
    if (header) {
      if (SECTION_TITLE) {
        header.textContent = SECTION_TITLE;
        console.log('📌 Header set to section title:', SECTION_TITLE);
      } else if (state.sort === "recommended" && IS_AUTHENTICATED) {
        header.innerHTML = `<i class="fas fa-magic"></i> Recommended for You`;
        console.log('📌 Header set to: Recommended');
      } else if (state.sort === "age-match" && IS_AUTHENTICATED) {
        header.innerHTML = `<i class="fas fa-user-check"></i> Age-Appropriate Anime`;
        console.log('📌 Header set to: Age-Appropriate');
      } else {
        header.innerHTML = `Hasil Pencarian`;
        console.log('📌 Header set to: Hasil Pencarian');
      }
    }

    el.resultsGrid.innerHTML = state.lastResults.map(buildCard).join("");
    applyViewMode();

    renderPagination();
    if (el.pagination) el.pagination.style.display = "flex";
  }

  /* ==================================================
     6. PAGINATION (DINAMIS)
  ================================================== */
  function renderPagination() {
    if (!el.paginationNumbers || !el.paginationPrev || !el.paginationNext) return;

    const cur = state.page;
    const total = state.total_pages;

    el.paginationPrev.disabled = cur <= 1;
    el.paginationNext.disabled = cur >= total;

    el.paginationNumbers.innerHTML = "";

    const max = 7;
    let start = Math.max(1, cur - Math.floor(max / 2));
    let end = Math.min(total, start + max - 1);
    start = Math.max(1, end - max + 1);

    const addEllipsis = () => {
      const span = document.createElement("span");
      span.className = "pagination-ellipsis";
      span.textContent = "...";
      el.paginationNumbers.appendChild(span);
    };

    const addPageBtn = (p) => {
      const btn = document.createElement("button");
      btn.className = "pagination-number" + (p === cur ? " active" : "");
      btn.textContent = String(p);
      btn.addEventListener("click", () => {
        state.page = p;
        doSearch({ scroll: true });
      });
      el.paginationNumbers.appendChild(btn);
    };

    if (start > 1) {
      addPageBtn(1);
      if (start > 2) addEllipsis();
    }

    for (let p = start; p <= end; p++) addPageBtn(p);

    if (end < total) {
      if (end < total - 1) addEllipsis();
      addPageBtn(total);
    }
  }

  /* ==================================================
     7. ACTIVE FILTER CHIPS
  ================================================== */
  function addChip(type, label, value) {
    if (!el.activeFilters) return;

    const chip = document.createElement("div");
    chip.className = "active-filter";
    chip.innerHTML = `
      <span>${escapeHtml(label)}</span>
      <button class="remove" data-type="${escapeAttr(type)}" data-value="${escapeAttr(value)}">
        <i class="fas fa-times"></i>
      </button>
    `;
    chip.querySelector(".remove").addEventListener("click", () => {
      removeFilter(type, value);
    });
    el.activeFilters.appendChild(chip);
  }

  function removeFilter(type, value) {
    if (type === "search") {
      state.q = "";
      if (el.mainSearchInput) el.mainSearchInput.value = "";
    } else if (type === "rating") {
      state.min_rating = 0.0;
      if (el.ratingSlider) el.ratingSlider.value = 0;
      if (el.ratingValue) el.ratingValue.textContent = "0.0";
    } else {
      state.filters[type] = state.filters[type].filter((x) => x !== value);

      const selector =
        type === "age"
          ? `input[name="age-rating"][value="${CSS.escape(value)}"]`
          : `input[name="${CSS.escape(type)}"][value="${CSS.escape(value)}"]`;
      const cb = document.querySelector(selector);
      if (cb) cb.checked = false;
    }

    state.page = 1;
    syncActiveFilters();
    doSearch({ scroll: true });
  }

  function syncActiveFilters() {
    if (!el.activeFilters) return;
    el.activeFilters.innerHTML = "";

    if (state.q) addChip("search", `Search: "${state.q}"`, state.q);

    state.filters.genre.forEach((g) => addChip("genre", `Genre: ${g}`, g));
    state.filters.year.forEach((y) => addChip("year", `Year: ${y}`, y));
    state.filters.status.forEach((s) => addChip("status", `Status: ${s}`, s));
    state.filters.type.forEach((t) => addChip("type", `Type: ${t}`, t));
    state.filters.age.forEach((a) => addChip("age", `Age: ${a}`, a));

    if (state.min_rating > 0) addChip("rating", `Rating: ${state.min_rating.toFixed(1)}+`, String(state.min_rating));
  }

  /* ==================================================
     8. READ FILTERS FROM UI
  ================================================== */
  function readFiltersFromUI() {
    state.filters.genre = Array.from(document.querySelectorAll('input[name="genre"]:checked')).map(cb => cb.value);
    state.filters.year = Array.from(document.querySelectorAll('input[name="year"]:checked')).map(cb => cb.value);
    state.filters.status = Array.from(document.querySelectorAll('input[name="status"]:checked')).map(cb => cb.value);
    state.filters.type = Array.from(document.querySelectorAll('input[name="type"]:checked')).map(cb => cb.value);
    state.filters.age = Array.from(document.querySelectorAll('input[name="age-rating"]:checked')).map(cb => cb.value);

    const selectedSort = document.querySelector('input[name="sort"]:checked');
    state.sort = normalizeSort(selectedSort?.value || DEFAULT_SORT);
  }

  /* ==================================================
     9. SUGGESTIONS (dari API)
  ================================================== */
  let suggestAbort = null;

  async function showSuggestions() {
    if (!el.searchSuggestions || !el.mainSearchInput) return;

    const v = el.mainSearchInput.value.trim();
    if (!v) {
      el.searchSuggestions.classList.remove("active");
      el.searchSuggestions.innerHTML = "";
      return;
    }

    if (suggestAbort) suggestAbort.abort();
    suggestAbort = new AbortController();

    const backupQ = state.q;
    state.q = v;

    try {
      const json = await fetch(`${API_URL}?${toQS({ q: v, page: 1, per_page: 8 })}`, {
        signal: suggestAbort.signal,
        headers: { Accept: "application/json" }
      }).then(r => r.json());

      const items = (json.results || []).slice(0, 8);
      el.searchSuggestions.innerHTML = "";

      if (!items.length) {
        el.searchSuggestions.innerHTML = `<div class="suggestion-item"><span>Tidak ada saran</span></div>`;
        el.searchSuggestions.classList.add("active");
        return;
      }

      items.forEach((it) => {
        const div = document.createElement("div");
        div.className = "suggestion-item";
        div.innerHTML = `<i class="fas fa-search"></i><span>${escapeHtml(it.title || "-")}</span>`;
        div.addEventListener("click", () => {
          el.mainSearchInput.value = it.title || "";
          state.q = (it.title || "").trim();
          state.page = 1;
          el.searchSuggestions.classList.remove("active");
          doSearch({ scroll: true });
        });
        el.searchSuggestions.appendChild(div);
      });

      el.searchSuggestions.classList.add("active");
    } catch (e) {
      // ignore abort
    } finally {
      state.q = backupQ;
    }
  }

  const debouncedSuggestions = debounce(showSuggestions, 200);

  /* ==================================================
     10. MAIN SEARCH
  ================================================== */
  async function doSearch({ scroll = false } = {}) {
    try {
      // ✅ Cek jika user memilih sort yang butuh login tapi belum login
      if (!IS_AUTHENTICATED && (state.sort === "recommended" || state.sort === "age-match")) {
        const sortName = state.sort === "recommended" ? "personalized recommendations" : "age-appropriate recommendations";
        showToast(
          "Login Required", 
          `Please login to see ${sortName}`, 
          "error"
        );
        
        state.sort = DEFAULT_SORT;
        const defaultRadio = document.querySelector(`input[name="sort"][value="${DEFAULT_SORT}"]`);
        if (defaultRadio) defaultRadio.checked = true;
        
        syncActiveFilters();
      }
      
      syncActiveFilters();

      const json = await fetchSearch();
      renderResults(json);
      syncActiveFilters();

      if (scroll) scrollToResults();
    } catch (e) {
      console.error(e);
      if (el.noResults) el.noResults.style.display = "block";
      if (el.resultsGrid) el.resultsGrid.style.display = "none";
      if (el.pagination) el.pagination.style.display = "none";
      showToast("Search error", "Gagal mengambil data dari server", "error");
    }
  }

  /* ==================================================
     11. HEADER / NAV UI
  ================================================== */
  function initHeaderUI() {
    window.addEventListener("scroll", () => {
      if (window.scrollY > 100) {
        el.header?.classList.add("scrolled");
        el.backToTop?.classList.add("show");
      } else {
        el.header?.classList.remove("scrolled");
        el.backToTop?.classList.remove("show");
      }
    });

    if (el.mobileToggle && el.navbar) {
      el.mobileToggle.addEventListener("click", () => {
        el.navbar.classList.toggle("active");
        const spans = el.mobileToggle.querySelectorAll("span");
        if (!spans.length) return;

        if (el.navbar.classList.contains("active")) {
          spans[0].style.transform = "rotate(45deg) translate(5px, 5px)";
          spans[1].style.opacity = "0";
          spans[2].style.transform = "rotate(-45deg) translate(5px, -5px)";
        } else {
          spans[0].style.transform = "none";
          spans[1].style.opacity = "1";
          spans[2].style.transform = "none";
        }
      });
    }

    if (el.searchTrigger && el.mainSearchInput) {
      el.searchTrigger.addEventListener("click", (e) => {
        e.preventDefault();
        el.mainSearchInput.focus();
        document.querySelector(".search-header")?.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    }

    if (el.userBtn && el.userDropdown) {
      el.userBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        el.userDropdown.classList.toggle("active");
      });

      document.addEventListener("click", (e) => {
        if (!el.userBtn.contains(e.target) && !el.userDropdown.contains(e.target)) {
          el.userDropdown.classList.remove("active");
        }
      });

      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") el.userDropdown.classList.remove("active");
      });
    }

    el.backToTop?.addEventListener("click", (e) => {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ==================================================
     12. FILTER UI (collapse + apply/reset + radio auto apply)
  ================================================== */
  function initFilterUI() {
    el.filterToggles?.forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-target");
        const options = document.getElementById(target);
        if (!options) return;

        options.classList.toggle("collapsed");

        const icon = btn.querySelector("i");
        if (icon) {
          icon.classList.toggle("fa-chevron-down");
          icon.classList.toggle("fa-chevron-up");
        }
      });
    });

    if (el.ratingSlider && el.ratingValue) {
      el.ratingSlider.addEventListener("input", function () {
        const v = (Number(this.value) / 10).toFixed(1);
        el.ratingValue.textContent = v;
        state.min_rating = parseFloat(v);
      });
      el.ratingSlider.addEventListener("change", () => {
        state.page = 1;
        syncActiveFilters();
        doSearch({ scroll: true });
      });
    }

    el.applyFilters?.addEventListener("click", () => {
      readFiltersFromUI();
      state.page = 1;
      syncActiveFilters();
      doSearch({ scroll: true });
      showToast("Filters Applied", "Hasil pencarian diperbarui", "success");
    });

    el.resetFilters?.addEventListener("click", () => {
      document.querySelectorAll('.filters-sidebar input[type="checkbox"]').forEach(cb => (cb.checked = false));

      state.min_rating = 0.0;
      if (el.ratingSlider) el.ratingSlider.value = 0;
      if (el.ratingValue) el.ratingValue.textContent = "0.0";

      // ✅ Gunakan DEFAULT_SORT sebagai default
      const defSort = document.querySelector(`input[name="sort"][value="${DEFAULT_SORT}"]`);
      if (defSort) defSort.checked = true;
      state.sort = DEFAULT_SORT;

      state.filters = { genre: [], year: [], status: [], type: [], age: [] };
      state.page = 1;

      syncActiveFilters();
      doSearch({ scroll: true });
      showToast("Filters Reset", "Semua filter dibersihkan", "success");
    });

    // ✅ Radio auto-apply untuk semua sort options
    document.querySelectorAll('input[name="sort"]').forEach(r => {
      r.addEventListener("change", () => {
        readFiltersFromUI();
        state.page = 1;
        syncActiveFilters();
        doSearch({ scroll: true });
      });
    });
  }

  /* ==================================================
     13. AUTO APPLY ON CHANGE
  ================================================== */
  function initAutoApplyOnChange() {
    document.querySelectorAll('.filters-sidebar input[type="checkbox"]').forEach(cb => {
      cb.addEventListener("change", () => {
        readFiltersFromUI();
        state.page = 1;
        syncActiveFilters();
        doSearch({ scroll: true });
      });
    });

    document.querySelectorAll('input[name="sort"]').forEach(r => {
      r.addEventListener("change", () => {
        readFiltersFromUI();
        state.page = 1;
        syncActiveFilters();
        doSearch({ scroll: true });
      });
    });
  }

  /* ==================================================
     14. VIEW (GRID/LIST)
  ================================================== */
  function initViewToggle() {
    el.viewOptions?.forEach((btn) => {
      btn.addEventListener("click", () => {
        const view = btn.getAttribute("data-view") || "grid";
        el.viewOptions.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        state.view = view;
        applyViewMode();
      });
    });
  }

  /* ==================================================
     15. QUICK SEARCH TAGS
  ================================================== */
  function initQuickTags() {
    el.quickTags?.forEach((tag) => {
      tag.addEventListener("click", (e) => {
        e.preventDefault();
        const text = tag.textContent.trim();
        if (!text) return;

        state.q = text;
        if (el.mainSearchInput) el.mainSearchInput.value = text;

        state.page = 1;
        doSearch({ scroll: true });
      });
    });
  }

  /* ==================================================
     16. SEARCH INPUT EVENTS + SUGGESTIONS
  ================================================== */
  function initSearchEvents() {
    const url = new URL(window.location.href);
    const qParam = (url.searchParams.get("q") || "").trim();
    if (qParam) {
      state.q = qParam;
      if (el.mainSearchInput) el.mainSearchInput.value = qParam;
    }

    el.mainSearchInput?.addEventListener("input", () => {
      debouncedSuggestions();
    });

    el.mainSearchInput?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        state.q = el.mainSearchInput.value.trim();
        state.page = 1;
        el.searchSuggestions?.classList.remove("active");
        doSearch({ scroll: true });
      }
      if (e.key === "Escape") {
        el.searchSuggestions?.classList.remove("active");
      }
    });

    el.mainSearchBtn?.addEventListener("click", (e) => {
      e.preventDefault();
      state.q = el.mainSearchInput?.value.trim() || "";
      state.page = 1;
      el.searchSuggestions?.classList.remove("active");
      doSearch({ scroll: true });
    });

    el.hasilPencarianBtn?.addEventListener("click", (e) => {
      e.preventDefault();
      state.q = el.mainSearchInput?.value.trim() || "";
      state.page = 1;
      doSearch({ scroll: true });
    });

    el.resetSearch?.addEventListener("click", (e) => {
      e.preventDefault();
      if (el.mainSearchInput) el.mainSearchInput.value = "";
      state.q = "";
      state.page = 1;

      document.querySelectorAll('.filters-sidebar input[type="checkbox"]').forEach(cb => (cb.checked = false));
      state.filters = { genre: [], year: [], status: [], type: [], age: [] };

      state.min_rating = 0.0;
      if (el.ratingSlider) el.ratingSlider.value = 0;
      if (el.ratingValue) el.ratingValue.textContent = "0.0";

      // ✅ Gunakan DEFAULT_SORT sebagai default
      const defSort = document.querySelector(`input[name="sort"][value="${DEFAULT_SORT}"]`);
      if (defSort) defSort.checked = true;
      state.sort = DEFAULT_SORT;

      syncActiveFilters();
      doSearch({ scroll: true });
      showToast("Reset", "Pencarian direset", "success");
    });

    document.addEventListener("click", (e) => {
      if (!e.target.closest(".main-search-bar")) {
        el.searchSuggestions?.classList.remove("active");
      }
    });
  }

  /* ==================================================
     17. PAGINATION EVENTS
  ================================================== */
  function initPaginationEvents() {
    el.paginationPrev?.addEventListener("click", () => {
      if (state.page <= 1) return;
      state.page -= 1;
      doSearch({ scroll: true });
    });

    el.paginationNext?.addEventListener("click", () => {
      if (state.page >= state.total_pages) return;
      state.page += 1;
      doSearch({ scroll: true });
    });
  }

  /* ==================================================
     18. INIT REKOMENDASI & AGE-MATCH
  ================================================== */
  function initRecommendationUI() {
    // ✅ Set default sort radio PERTAMA sesuai dengan DEFAULT_SORT
    console.log('🔧 Setting default sort radio to:', DEFAULT_SORT);
    const defaultRadio = document.querySelector(`input[name="sort"][value="${DEFAULT_SORT}"]`);
    if (defaultRadio) {
      defaultRadio.checked = true;
      console.log('✅ Radio button set:', defaultRadio.value);
    } else {
      console.warn('⚠️ Radio button not found for:', DEFAULT_SORT);
    }

    // Disable recommended & age-match jika belum login
    if (!IS_AUTHENTICATED && el.recommendedRadio) {
      el.recommendedRadio.disabled = true;
      const label = el.recommendedRadio.closest("label");
      if (label) {
        label.style.opacity = "0.6";
        label.style.cursor = "not-allowed";
        label.title = "Login to see recommendations";
      }
    }

    if (!IS_AUTHENTICATED && el.ageMatchRadio) {
      el.ageMatchRadio.disabled = true;
      const label = el.ageMatchRadio.closest("label");
      if (label) {
        label.style.opacity = "0.6";
        label.style.cursor = "not-allowed";
        label.title = "Login to see age-appropriate recommendations";
      }
    }
  }

  /* ==================================================
     19. FAVORITE & ADD TO LIST HANDLERS
  ================================================== */
  function initCardActions() {
    document.addEventListener('click', function(e) {
      if (e.target.closest('.add-to-list')) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.target.closest('.add-to-list');
        const animeId = btn.getAttribute('data-anime-id');
        
        if (!IS_AUTHENTICATED) {
          showToast("Login Required", "Please login to add anime to your list", "error");
          return;
        }
        
        const icon = btn.querySelector('i');
        if (icon.classList.contains('fa-plus')) {
          icon.classList.remove('fa-plus');
          icon.classList.add('fa-check');
          btn.classList.add('active');
          showToast("Added to List", "Anime berhasil ditambahkan ke list Anda", "success");
        } else {
          icon.classList.remove('fa-check');
          icon.classList.add('fa-plus');
          btn.classList.remove('active');
          showToast("Removed from List", "Anime dihapus dari list Anda", "success");
        }
        
        console.log('Add to list:', animeId);
      }
      
      if (e.target.closest('.add-to-favorite')) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.target.closest('.add-to-favorite');
        const animeId = btn.getAttribute('data-anime-id');
        
        if (!IS_AUTHENTICATED) {
          showToast("Login Required", "Please login to add anime to favorites", "error");
          return;
        }
        
        const icon = btn.querySelector('i');
        if (icon.classList.contains('far')) {
          icon.classList.remove('far');
          icon.classList.add('fas');
          btn.classList.add('active');
          showToast("Added to Favorites", "Anime berhasil ditambahkan ke favorit Anda", "success");
        } else {
          icon.classList.remove('fas');
          icon.classList.add('far');
          btn.classList.remove('active');
          showToast("Removed from Favorites", "Anime dihapus dari favorit Anda", "success");
        }
        
        console.log('Add to favorite:', animeId);
      }
    });
  }

  /* ==================================================
     20. INIT
  ================================================== */
  function init() {
    console.log('🚀 Initializing search page...');
    console.log('   Default Sort:', DEFAULT_SORT);
    
    initHeaderUI();
    initFilterUI();
    initViewToggle();
    initQuickTags();
    initSearchEvents();
    initPaginationEvents();
    
    // ✅ PENTING: Init recommendation UI DULU (set radio button)
    initRecommendationUI();
    
    initCardActions();
    initAutoApplyOnChange();

    // ✅ Baca filters dari UI (termasuk radio yang sudah di-set)
    readFiltersFromUI();
    syncActiveFilters();

    console.log('   State after init:', state.sort);
    
    // Load data
    doSearch();
    console.log("✅ Search page ready with sort:", state.sort);
  }

  init();
});