(function () {
  "use strict";

  var db = window.__DB__ || { productos: [], scoreAxes: [] };
  var brand = window.__BRAND__ || {};

  var $ = function (sel, scope) { return (scope || document).querySelector(sel); };
  var $$ = function (sel, scope) { return Array.from((scope || document).querySelectorAll(sel)); };
  var escHTML = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  function safe(fn, name) { try { fn(); } catch (e) { console.warn("[" + name + "]", e); } }
  var fmtEUR = function (n) {
    if (n == null || isNaN(n)) return "—";
    return Number(n).toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
  };

  var AXIS_LABELS = {
    scoreSharpness: "Nitidez",
    scoreSmoothness: "Fluidez",
    scoreColorHdr: "Color / HDR",
    scoreErgonomics: "Ergonomía",
    scoreGaming: "Gaming",
    scoreValue: "Calidad-precio"
  };
  var SERIES_COLORS = ["#7dd3fc", "#a3e635", "#f472b6", "#fbbf24"];

  // ---------------------------------------------------------------
  // Mobile nav
  // ---------------------------------------------------------------
  function initNav() {
    var toggle = $("[data-nav-toggle]");
    var mobile = $("[data-nav-mobile]");
    if (!toggle || !mobile) return;
    toggle.addEventListener("click", function () {
      var open = mobile.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // ---------------------------------------------------------------
  // Reveal on scroll — low threshold + safety timeout (gotcha A.8)
  // ---------------------------------------------------------------
  function initReveals() {
    var targets = $$(".reveal");
    if (!targets.length) return;
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); }
        });
      }, { threshold: 0.01, rootMargin: "0px 0px -2% 0px" });
      targets.forEach(function (t) { io.observe(t); });
    } else {
      targets.forEach(function (t) { t.classList.add("is-visible"); });
    }
    setTimeout(function () {
      targets.forEach(function (el) {
        if (!el.classList.contains("is-visible") && el.getBoundingClientRect().top < window.innerHeight) {
          el.classList.add("is-visible");
        }
      });
    }, 6000);
  }

  // ---------------------------------------------------------------
  // Ficha gallery — swap main image on thumbnail click
  // ---------------------------------------------------------------
  function initGallery() {
    $$("[data-galeria]").forEach(function (gal) {
      var main = $(".ficha-img-main img", gal);
      var thumbs = $$("[data-thumbs] button", gal);
      if (!main || !thumbs.length) return;
      thumbs.forEach(function (btn) {
        btn.addEventListener("click", function () {
          var src = btn.getAttribute("data-src");
          if (!src) return;
          main.src = src;
          thumbs.forEach(function (b) { b.classList.remove("is-active"); });
          btn.classList.add("is-active");
        });
      });
    });
  }

  // ---------------------------------------------------------------
  // Comparator selection — stored in localStorage, mirrored to URL hash
  // ---------------------------------------------------------------
  var LS_KEY = "screenscope_compare";
  function getCompareIds() {
    try {
      var fromHash = (location.hash || "").replace(/^#/, "");
      var params = new URLSearchParams(fromHash.indexOf("ids=") === 0 ? fromHash : "");
      var fromUrl = params.get("ids");
      if (fromUrl) return fromUrl.split(",").filter(Boolean);
      var raw = localStorage.getItem(LS_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) { return []; }
  }
  function setCompareIds(ids) {
    ids = Array.from(new Set(ids)).slice(0, 4);
    try { localStorage.setItem(LS_KEY, JSON.stringify(ids)); } catch (e) {}
    history.replaceState(null, "", "#ids=" + ids.join(","));
    return ids;
  }
  function addToCompare(id) {
    var ids = getCompareIds();
    if (ids.indexOf(id) === -1) ids.push(id);
    setCompareIds(ids);
    updateCompareCount();
  }
  function removeFromCompare(id) {
    var ids = getCompareIds().filter(function (x) { return x !== id; });
    setCompareIds(ids);
    renderComparator();
    updateCompareCount();
  }
  function updateCompareCount() {
    var n = getCompareIds().length;
    $$("[data-compare-count]").forEach(function (el) { el.textContent = n ? "(" + n + ")" : ""; });
  }

  function initAddToCompareButtons() {
    $$("[data-add-comparador]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        addToCompare(btn.getAttribute("data-add-comparador"));
        btn.textContent = "Añadido ✓";
        setTimeout(function () { btn.textContent = "Añadir al comparador"; }, 1600);
      });
    });
    updateCompareCount();
  }

  // ---------------------------------------------------------------
  // Radar chart — hand-drawn SVG, no dependency
  // ---------------------------------------------------------------
  function buildRadarSVG(seriesList, axes, size) {
    size = size || 320;
    var cx = size / 2, cy = size / 2, r = size * 0.36;
    var n = axes.length;
    var angle = function (i) { return (Math.PI * 2 * i) / n - Math.PI / 2; };
    var pt = function (i, radiusFrac) {
      var a = angle(i);
      return [cx + Math.cos(a) * r * radiusFrac, cy + Math.sin(a) * r * radiusFrac];
    };
    var svg = '<svg viewBox="0 0 ' + size + ' ' + size + '" role="img" aria-label="Gráfico de radar">';
    // grid rings
    [0.25, 0.5, 0.75, 1].forEach(function (frac) {
      var pts = axes.map(function (_, i) { return pt(i, frac).join(","); }).join(" ");
      svg += '<polygon points="' + pts + '" fill="none" stroke="var(--line)" stroke-width="1"></polygon>';
    });
    // axis lines + labels
    axes.forEach(function (axisKey, i) {
      var p = pt(i, 1);
      svg += '<line x1="' + cx + '" y1="' + cy + '" x2="' + p[0] + '" y2="' + p[1] + '" stroke="var(--line)" stroke-width="1"></line>';
      var lp = pt(i, 1.16);
      var anchor = Math.cos(angle(i)) > 0.3 ? "start" : (Math.cos(angle(i)) < -0.3 ? "end" : "middle");
      svg += '<text x="' + lp[0] + '" y="' + lp[1] + '" font-size="10" fill="var(--text-dim)" text-anchor="' + anchor + '" dominant-baseline="middle">' + escHTML(AXIS_LABELS[axisKey] || axisKey) + '</text>';
    });
    // series polygons
    seriesList.forEach(function (s) {
      var pts = axes.map(function (axisKey, i) {
        var v = s.scores[axisKey];
        var frac = v == null ? 0 : Math.max(0, Math.min(10, v)) / 10;
        return pt(i, frac).join(",");
      }).join(" ");
      svg += '<polygon points="' + pts + '" fill="' + s.color + '" fill-opacity="0.22" stroke="' + s.color + '" stroke-width="2"></polygon>';
    });
    svg += "</svg>";
    return svg;
  }
  window.__buildRadarSVG = buildRadarSVG;

  // ---------------------------------------------------------------
  // Comparator page
  // ---------------------------------------------------------------
  function productById(id) {
    return (db.productos || []).find(function (p) { return p.id === id; });
  }

  var SPEC_ROWS = [
    { key: "discountedPrice", label: "Precio", best: "min", format: fmtEUR },
    { key: "panelType", label: "Tipo de panel" },
    { key: "sizeInches", label: "Tamaño", unit: "\"", best: "max" },
    { key: "resolution", label: "Resolución" },
    { key: "refreshRateHz", label: "Tasa de refresco", unit: " Hz", best: "max" },
    { key: "responseTimeMs", label: "Tiempo de respuesta", unit: " ms", best: "min" },
    { key: "brightnessNits", label: "Brillo", unit: " nits", best: "max" },
    { key: "hdr", label: "HDR" },
    { key: "curved", label: "Curvo", bool: true },
    { key: "syncTech", label: "Tecnología de sincronización" },
    { key: "heightAdjustable", label: "Ajuste de altura", bool: true },
    { key: "pivot", label: "Pivote", bool: true },
    { key: "weightKg", label: "Peso", unit: " kg", best: "min" },
    { key: "warrantyYears", label: "Garantía", unit: " años", best: "max" }
  ];

  function renderComparator() {
    var root = $("[data-comparator]");
    if (!root) return;
    var ids = getCompareIds();
    var products = ids.map(productById).filter(Boolean);
    var wrap = $("[data-compare-wrap]", root);
    var empty = $("[data-compare-empty]", root);
    var radarWrap = $("[data-compare-radar]", root);
    if (!products.length) {
      if (wrap) wrap.hidden = true;
      if (radarWrap) radarWrap.hidden = true;
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;
    if (wrap) wrap.hidden = false;
    if (radarWrap) radarWrap.hidden = false;

    var cols = products.length;
    var cardsEl = $("[data-compare-cards]", wrap);
    var specsEl = $("[data-compare-specs]", wrap);
    var verdictEl = $("[data-compare-verdict]", wrap);

    cardsEl.style.setProperty("--cols", cols);
    cardsEl.innerHTML = products.map(function (p) {
      return '<div class="compare-card">' +
        '<img src="' + escHTML(p.images[0]) + '" alt="' + escHTML(p.name) + '">' +
        '<a class="compare-card-name" href="' + productHref(p) + '">' + escHTML(p.name) + "</a>" +
        '<button class="compare-remove" data-remove="' + p.id + '">quitar</button></div>';
    }).join("");

    var winCounts = products.map(function () { return 0; });
    var decided = 0;
    var specsHtml = "";
    SPEC_ROWS.forEach(function (row) {
      var values = products.map(function (p) { return p[row.key]; });
      var best = null;
      if (row.best && values.every(function (v) { return typeof v === "number"; })) {
        best = row.best === "max" ? Math.max.apply(null, values) : Math.min.apply(null, values);
      }
      if (best !== null) {
        var winners = [];
        values.forEach(function (v, i) { if (v === best) winners.push(i); });
        if (winners.length === 1) { decided++; winCounts[winners[0]]++; }
      }
      specsHtml += '<div class="compare-spec-row"><span class="compare-spec-label">' + escHTML(row.label) + '</span>' +
        '<div class="compare-spec-values" style="--cols:' + cols + '">' +
        values.map(function (v) {
          var display;
          if (row.bool) display = v ? "Sí" : "No";
          else if (v == null) display = "—";
          else if (row.format) display = row.format(v);
          else display = String(v).replace(".", ",") + (row.unit || "");
          var cls = best !== null && v === best ? " is-best" : "";
          return '<div class="compare-spec-value' + cls + '">' + escHTML(display) + "</div>";
        }).join("") + "</div></div>";
    });
    specsHtml += '<div class="compare-spec-row"><span class="compare-spec-label">Comprar</span>' +
      '<div class="compare-spec-values" style="--cols:' + cols + '">' +
      products.map(function (p) {
        return '<a class="btn btn-primary btn-sm" href="' + escHTML(p.affiliate_url) + '" target="_blank" rel="sponsored nofollow noopener">Ver en Amazon</a>';
      }).join("") + "</div></div>";
    specsEl.style.setProperty("--cols", cols);
    specsEl.innerHTML = specsHtml;

    if (verdictEl) {
      if (products.length === 2 && decided > 0) {
        var leadIdx = winCounts[0] >= winCounts[1] ? 0 : 1;
        verdictEl.hidden = false;
        verdictEl.innerHTML = '<p class="compare-verdict"><strong>' + escHTML(products[leadIdx].name) +
          "</strong> va por delante en " + winCounts[leadIdx] + " de " + decided + " especificaciones comparables.</p>";
      } else {
        verdictEl.hidden = true;
        verdictEl.innerHTML = "";
      }
    }

    $$("[data-remove]", cardsEl).forEach(function (btn) {
      btn.addEventListener("click", function () { removeFromCompare(btn.getAttribute("data-remove")); });
    });

    var axes = db.scoreAxes || Object.keys(AXIS_LABELS);
    var seriesList = products.map(function (p, i) {
      var scores = {};
      axes.forEach(function (a) { scores[a] = p[a]; });
      return { label: p.name, color: SERIES_COLORS[i % SERIES_COLORS.length], scores: scores };
    });
    var figure = $("[data-radar]", radarWrap);
    if (figure) figure.innerHTML = buildRadarSVG(seriesList, axes, 380);
    var legend = $("[data-radar-legend]", radarWrap);
    if (legend) {
      legend.innerHTML = seriesList.map(function (s) {
        return '<span><span class="dot" style="background:' + s.color + '"></span>' + escHTML(s.label) + "</span>";
      }).join("");
    }
  }

  function productHref(p) { return "monitor-" + p.id + ".html"; }

  function initComparatorPicker() {
    var picker = $("[data-comparator-picker]");
    if (!picker) return;
    var select = $("select", picker);
    if (select) {
      select.innerHTML = '<option value="">Añadir un producto…</option>' + (db.productos || []).map(function (p) {
        return '<option value="' + p.id + '">' + escHTML(p.name) + "</option>";
      }).join("");
      select.addEventListener("change", function () {
        if (select.value) { addToCompare(select.value); renderComparator(); select.value = ""; }
      });
    }
  }

  // ---------------------------------------------------------------
  // Category page filters (client-side, progressive enhancement)
  // ---------------------------------------------------------------
  function initCategoryFilters() {
    var root = $("[data-filterable]");
    if (!root) return;
    var grid = $("[data-products-grid]", root);
    var sortSel = $("[data-sort]", root);
    var syncSel = $("[data-filter-sync]", root);
    if (!grid) return;
    var cards = $$(".card", grid);
    function apply() {
      var syncVal = syncSel ? syncSel.value : "";
      cards.forEach(function (card) {
        var matches = !syncVal || card.getAttribute("data-sync") === syncVal;
        card.style.display = matches ? "" : "none";
      });
      if (sortSel && sortSel.value) {
        var visible = cards.filter(function (c) { return c.style.display !== "none"; });
        var dir = sortSel.value.indexOf("desc") !== -1 ? -1 : 1;
        var key = sortSel.value.replace("-asc", "").replace("-desc", "");
        visible.sort(function (a, b) {
          var av = parseFloat(a.getAttribute("data-" + key)) || 0;
          var bv = parseFloat(b.getAttribute("data-" + key)) || 0;
          return (av - bv) * dir;
        });
        visible.forEach(function (c) { grid.appendChild(c); });
      }
    }
    if (sortSel) sortSel.addEventListener("change", apply);
    if (syncSel) syncSel.addEventListener("change", apply);
  }

  // ---------------------------------------------------------------
  // Cookies de analítica (Google Analytics) — solo se cargan con consentimiento
  // ---------------------------------------------------------------
  var COOKIE_CONSENT_KEY = "cookieConsent";

  function loadGoogleAnalytics() {
    var gaId = brand.gaMeasurementId;
    if (!gaId || window.__gaLoaded) return;
    window.__gaLoaded = true;
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + gaId;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", gaId, { anonymize_ip: true });
  }

  function initCookieConsent() {
    var banner = $("[data-cookie-banner]");
    if (!banner) return;
    var stored = null;
    try { stored = localStorage.getItem(COOKIE_CONSENT_KEY); } catch (e) {}
    if (stored === "accepted") { loadGoogleAnalytics(); return; }
    if (stored === "rejected") { return; }
    banner.hidden = false;
    var acceptBtn = $("[data-cookie-accept]", banner);
    var rejectBtn = $("[data-cookie-reject]", banner);
    if (acceptBtn) {
      acceptBtn.addEventListener("click", function () {
        try { localStorage.setItem(COOKIE_CONSENT_KEY, "accepted"); } catch (e) {}
        banner.hidden = true;
        loadGoogleAnalytics();
      });
    }
    if (rejectBtn) {
      rejectBtn.addEventListener("click", function () {
        try { localStorage.setItem(COOKIE_CONSENT_KEY, "rejected"); } catch (e) {}
        banner.hidden = true;
      });
    }
  }

  // ---------------------------------------------------------------
  // Boot
  // ---------------------------------------------------------------
  function boot() {
    safe(initNav, "initNav");
    safe(initReveals, "initReveals");
    safe(initGallery, "initGallery");
    safe(initAddToCompareButtons, "initAddToCompareButtons");
    safe(initComparatorPicker, "initComparatorPicker");
    safe(renderComparator, "renderComparator");
    safe(initCategoryFilters, "initCategoryFilters");
    safe(initCookieConsent, "initCookieConsent");
    document.documentElement.classList.add("is-ready");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
