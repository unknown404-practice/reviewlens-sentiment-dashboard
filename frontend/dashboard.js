/**
 * ReviewLens Dashboard - Vanilla JavaScript Client
 * =================================================
 * High-performance, zero-dependency, safe DOM manipulation logic.
 * Integrates with FastAPI REST backend endpoints.
 * Strictly uses textContent and document.createElement for all API and user data.
 */

(function () {
  "use strict";

  // Injected by app.py via JSON-safe replacement
  const API_BASE_URL = "__API_BASE_URL__";

  // Application State
  const state = {
    apiOnline: false,
    activeTab: "overview",
    summary: null,
    categories: [],
    products: [],
    topPositive: [],
    topNegative: [],
    // Review Explorer state
    reviewsTotal: 0,
    reviews: [],
    currentPage: 1,
    pageSize: 20,
    filters: {
      search: "",
      sentiment: "",
      category: "",
      product: "",
      sort: "newest",
    },
    isLoadingReviews: false,
  };

  // Preset Sample Review Texts for Instant Testing
  const SAMPLE_PRESETS = {
    positive: "Excellent quality, fast delivery, and I absolutely love it. Will definitely purchase again!",
    neutral: "The product arrived as described in a cardboard box on Tuesday. It is okay for the price.",
    negative: "Terrible product. It stopped working after one day and customer support was completely unhelpful.",
  };

  // ============================================================================
  // Utility & Formatting Helpers
  // ============================================================================

  function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return "0";
    return Number(num).toLocaleString();
  }

  function formatPercentage(num) {
    if (num === null || num === undefined || isNaN(num)) return "0.0%";
    return Number(num).toFixed(1) + "%";
  }

  function formatScore(score) {
    if (score === null || score === undefined || isNaN(score)) return "0.0000";
    const val = Number(score);
    const sign = val > 0 ? "+" : "";
    return sign + val.toFixed(4);
  }

  function formatDate(dateStr) {
    if (!dateStr) return "N/A";
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return String(dateStr);
      return d.toISOString().split("T")[0];
    } catch {
      return String(dateStr);
    }
  }

  function debounce(fn, delayMs = 300) {
    let timer = null;
    return function (...args) {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delayMs);
    };
  }

  function createTextElement(tag, text, className = "") {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = text !== null && text !== undefined ? String(text) : "";
    return el;
  }

  function renderStars(rating) {
    const r = Math.round(Number(rating) || 0);
    const stars = "★".repeat(Math.max(0, Math.min(5, r))) + "☆".repeat(Math.max(0, 5 - Math.max(0, Math.min(5, r))));
    return stars;
  }

  // ============================================================================
  // Network / API Client Helper
  // ============================================================================

  async function apiRequest(path, options = {}, timeoutMs = 15000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const fullUrl = `${API_BASE_URL}${path}`;
    const headers = {
      Accept: "application/json",
      ...(options.headers || {}),
    };

    if (options.body && typeof options.body === "string" && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    try {
      const response = await fetch(fullUrl, {
        ...options,
        headers,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      let data = null;
      const text = await response.text();
      if (text) {
        try {
          data = JSON.parse(text);
        } catch {
          data = { message: text };
        }
      }

      if (!response.ok) {
        const errorMsg = (data && (data.message || data.detail)) || `Server returned HTTP ${response.status}`;
        const err = new Error(typeof errorMsg === "object" ? JSON.stringify(errorMsg) : String(errorMsg));
        err.status = response.status;
        err.data = data;
        throw err;
      }

      return data;
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === "AbortError") {
        const timeoutErr = new Error("Request timed out. Please verify that the API is running.");
        timeoutErr.status = 408;
        throw timeoutErr;
      }
      throw err;
    }
  }

  // ============================================================================
  // API Health Check & Indicator
  // ============================================================================

  async function checkApiHealth() {
    const statusBox = document.getElementById("api-status-container");
    const statusText = document.getElementById("api-status-text");
    const errorBanner = document.getElementById("overview-error-banner");

    statusBox.className = "rl-status-indicator checking";
    statusText.textContent = "Checking API…";

    try {
      const data = await apiRequest("/health", { method: "GET" }, 5000);
      if (data && (data.status === "healthy" || data.status === "success")) {
        state.apiOnline = true;
        statusBox.className = "rl-status-indicator online";
        statusText.textContent = "API Connected";
        if (errorBanner) errorBanner.style.display = "none";
        return true;
      }
      throw new Error("Invalid health response");
    } catch {
      state.apiOnline = false;
      statusBox.className = "rl-status-indicator offline";
      statusText.textContent = "API Offline";
      if (errorBanner) errorBanner.style.display = "flex";
      return false;
    }
  }

  // ============================================================================
  // Tab Switching Logic
  // ============================================================================

  function switchTab(tabId) {
    state.activeTab = tabId;

    // Update Tab Buttons
    const buttons = document.querySelectorAll(".rl-tab-btn");
    buttons.forEach((btn) => {
      const isActive = btn.id === `tab-btn-${tabId}`;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    // Update Tab Panels
    const panels = document.querySelectorAll(".rl-tab-panel");
    panels.forEach((panel) => {
      const isActive = panel.id === `panel-${tabId}`;
      panel.classList.toggle("active", isActive);
      if (isActive) {
        panel.removeAttribute("hidden");
      } else {
        panel.setAttribute("hidden", "true");
      }
    });

    // Lazy load tab contents if needed
    if (tabId === "explore" && state.reviews.length === 0) {
      loadReviews();
    } else if (tabId === "insights" && state.categories.length === 0) {
      loadInsights();
    }
  }

  // ============================================================================
  // Overview Tab: Data Loading & Rendering
  // ============================================================================

  async function loadOverview() {
    const isOnline = await checkApiHealth();
    if (!isOnline) return;

    try {
      const summary = await apiRequest("/api/v1/demo/summary");
      state.summary = summary;
      renderKPIs(summary);
      renderDistributionBar(summary);
    } catch (err) {
      console.error("Failed to load demo summary:", err);
    }

    try {
      const categories = await apiRequest("/api/v1/analytics/categories");
      state.categories = categories || [];
      const products = await apiRequest("/api/v1/analytics/products");
      state.products = products || [];
      renderQuickInsights(categories, products);
      populateFilterDropdowns(categories, products);
    } catch (err) {
      console.error("Failed to load analytics for overview:", err);
    }
  }

  function renderKPIs(summary) {
    if (!summary) return;

    const setCard = (id, val, sub) => {
      const card = document.getElementById(id);
      if (!card) return;
      card.classList.remove("loading");
      const valEl = card.querySelector(".rl-kpi-value");
      const subEl = card.querySelector(".rl-kpi-subtext");
      if (valEl) valEl.textContent = val;
      if (subEl && sub !== undefined) subEl.textContent = sub;
    };

    setCard("kpi-total", formatNumber(summary.total_reviews), "Processed dataset records");
    setCard("kpi-pos", formatNumber(summary.positive_count), `${formatPercentage(summary.positive_percentage)} of total`);
    setCard("kpi-neu", formatNumber(summary.neutral_count), `${formatPercentage(summary.neutral_percentage)} of total`);
    setCard("kpi-neg", formatNumber(summary.negative_count), `${formatPercentage(summary.negative_percentage)} of total`);
    setCard("kpi-compound", formatScore(summary.average_compound_score), `Median: ${formatScore(summary.median_compound_score)}`);
    setCard("kpi-rating", `${Number(summary.average_rating || 0).toFixed(2)} ★`, "Out of 5.0 stars");

    const matchVal = summary.sentiment_match_percentage !== null && summary.sentiment_match_percentage !== undefined
      ? formatPercentage(summary.sentiment_match_percentage)
      : "N/A";
    setCard("kpi-match", matchVal, "Star rating matches VADER");
  }

  function renderDistributionBar(summary) {
    if (!summary) return;
    const posPct = Number(summary.positive_percentage || 0);
    const neuPct = Number(summary.neutral_percentage || 0);
    const negPct = Number(summary.negative_percentage || 0);

    const posBar = document.getElementById("dist-bar-pos");
    const neuBar = document.getElementById("dist-bar-neu");
    const negBar = document.getElementById("dist-bar-neg");

    if (posBar) {
      posBar.style.width = `${Math.max(posPct, 2)}%`;
      posBar.title = `Positive: ${posPct}%`;
      posBar.textContent = posPct > 8 ? `${posPct.toFixed(1)}%` : "";
    }
    if (neuBar) {
      neuBar.style.width = `${Math.max(neuPct, 2)}%`;
      neuBar.title = `Neutral: ${neuPct}%`;
      neuBar.textContent = neuPct > 8 ? `${neuPct.toFixed(1)}%` : "";
    }
    if (negBar) {
      negBar.style.width = `${Math.max(negPct, 2)}%`;
      negBar.title = `Negative: ${negPct}%`;
      negBar.textContent = negPct > 8 ? `${negPct.toFixed(1)}%` : "";
    }

    const posLeg = document.getElementById("legend-pos-val");
    const neuLeg = document.getElementById("legend-neu-val");
    const negLeg = document.getElementById("legend-neg-val");

    if (posLeg) posLeg.textContent = `${formatNumber(summary.positive_count)} (${formatPercentage(posPct)})`;
    if (neuLeg) neuLeg.textContent = `${formatNumber(summary.neutral_count)} (${formatPercentage(neuPct)})`;
    if (negLeg) negLeg.textContent = `${formatNumber(summary.negative_count)} (${formatPercentage(negPct)})`;
  }

  function renderQuickInsights(categories, products) {
    if (categories && categories.length > 0) {
      // Sort copy by average_compound_score
      const sortedByScore = [...categories].sort((a, b) => (b.average_compound_score || 0) - (a.average_compound_score || 0));
      const best = sortedByScore[0];
      const lowest = sortedByScore[sortedByScore.length - 1];

      const bestVal = document.getElementById("qi-best-cat-val");
      const bestSub = document.getElementById("qi-best-cat-sub");
      if (bestVal && best) bestVal.textContent = best.product_category || "—";
      if (bestSub && best) bestSub.textContent = `Avg. Compound: ${formatScore(best.average_compound_score)} (${best.review_count} reviews)`;

      const lowVal = document.getElementById("qi-lowest-cat-val");
      const lowSub = document.getElementById("qi-lowest-cat-sub");
      if (lowVal && lowest) lowVal.textContent = lowest.product_category || "—";
      if (lowSub && lowest) lowSub.textContent = `Avg. Compound: ${formatScore(lowest.average_compound_score)} (${lowest.review_count} reviews)`;
    }

    if (products && products.length > 0) {
      const sortedByCount = [...products].sort((a, b) => (b.review_count || 0) - (a.review_count || 0));
      const topProd = sortedByCount[0];
      const prodVal = document.getElementById("qi-top-product-val");
      const prodSub = document.getElementById("qi-top-product-sub");
      if (prodVal && topProd) prodVal.textContent = topProd.product_name || "—";
      if (prodSub && topProd) prodSub.textContent = `${topProd.review_count} reviews | ${Number(topProd.average_rating || 0).toFixed(1)} ★ avg`;
    }
  }

  // ============================================================================
  // Analyze Text Tab: Real-Time Sentiment Scoring
  // ============================================================================

  function initAnalyzeText() {
    const textarea = document.getElementById("analyze-text-input");
    const counter = document.getElementById("char-counter");
    const submitBtn = document.getElementById("btn-analyze-submit");
    const clearBtn = document.getElementById("btn-analyze-clear");
    const errorBox = document.getElementById("analyze-error-container");
    const resultCard = document.getElementById("analyze-result-card");

    if (!textarea) return;

    // Character counter
    textarea.addEventListener("input", () => {
      const len = textarea.value.length;
      if (counter) counter.textContent = `${len} / 5000`;
    });

    // Preset buttons
    const presetBtns = document.querySelectorAll(".rl-preset-btn");
    presetBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const presetKey = btn.getAttribute("data-preset");
        if (SAMPLE_PRESETS[presetKey]) {
          textarea.value = SAMPLE_PRESETS[presetKey];
          textarea.dispatchEvent(new Event("input"));
        }
      });
    });

    // Clear button
    clearBtn.addEventListener("click", () => {
      textarea.value = "";
      textarea.dispatchEvent(new Event("input"));
      errorBox.style.display = "none";
      resultCard.style.display = "none";
      textarea.focus();
    });

    // Submit Action
    submitBtn.addEventListener("click", async () => {
      const rawText = textarea.value;
      const stripped = rawText.trim();

      errorBox.style.display = "none";
      resultCard.style.display = "none";

      // Client-side empty validation
      if (!stripped) {
        errorBox.textContent = "Please enter review text before submitting analysis.";
        errorBox.style.display = "block";
        return;
      }

      submitBtn.disabled = true;
      const originalText = submitBtn.innerHTML;
      submitBtn.textContent = "Analyzing…";

      try {
        const result = await apiRequest("/api/v1/analyze/text", {
          method: "POST",
          body: JSON.stringify({ text: stripped }),
        });
        renderAnalysisResult(result);
      } catch (err) {
        errorBox.style.display = "block";
        if (err.status === 503 || !state.apiOnline) {
          errorBox.textContent = "The ReviewLens API is not reachable. Start the FastAPI service and try again.";
        } else if (err.status === 408) {
          errorBox.textContent = "The request took too long. Please try again.";
        } else {
          errorBox.textContent = err.message || "Failed to analyze review text.";
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }

  function renderAnalysisResult(result) {
    const card = document.getElementById("analyze-result-card");
    if (!card || !result) return;

    const labelBadge = document.getElementById("result-label-badge");
    const strengthBadge = document.getElementById("result-strength-badge");
    const compoundVal = document.getElementById("result-compound-val");
    const posNum = document.getElementById("val-pos-num");
    const neuNum = document.getElementById("val-neu-num");
    const negNum = document.getElementById("val-neg-num");
    const posMeter = document.getElementById("val-pos-meter");
    const neuMeter = document.getElementById("val-neu-meter");
    const negMeter = document.getElementById("val-neg-meter");
    const interpText = document.getElementById("result-interpretation");

    const label = result.sentiment_label || "Neutral";
    const strength = result.sentiment_strength || "Neutral";
    const scores = result.scores || {};
    const compound = Number(scores.compound || 0);
    const pos = Number(scores.pos || 0);
    const neu = Number(scores.neu || 0);
    const neg = Number(scores.neg || 0);

    // Label Badge Styling
    labelBadge.textContent = label;
    labelBadge.className = "rl-badge rl-badge-lg";
    if (label === "Positive") labelBadge.classList.add("rl-badge-pos");
    else if (label === "Negative") labelBadge.classList.add("rl-badge-neg");
    else labelBadge.classList.add("rl-badge-neu");

    strengthBadge.textContent = strength;
    compoundVal.textContent = formatScore(compound);

    // Meters & Numbers
    posNum.textContent = pos.toFixed(3);
    neuNum.textContent = neu.toFixed(3);
    negNum.textContent = neg.toFixed(3);

    posMeter.style.width = `${Math.round(pos * 100)}%`;
    neuMeter.style.width = `${Math.round(neu * 100)}%`;
    negMeter.style.width = `${Math.round(neg * 100)}%`;

    // Interpretation strictly based on returned scores
    let interpretation = "";
    if (compound >= 0.60) {
      interpretation = `Classified as Strong Positive (compound: ${formatScore(compound)}). Text features robust positive emotional markers (${(pos * 100).toFixed(1)}% positive valence) with minimal hesitation.`;
    } else if (compound >= 0.05) {
      interpretation = `Classified as Positive (compound: ${formatScore(compound)}). Positive sentiment exceeds the +0.05 threshold with ${(pos * 100).toFixed(1)}% positive valence.`;
    } else if (compound <= -0.60) {
      interpretation = `Classified as Strong Negative (compound: ${formatScore(compound)}). Pronounced negative markers (${(neg * 100).toFixed(1)}% negative valence) indicating critical dissatisfaction.`;
    } else if (compound <= -0.05) {
      interpretation = `Classified as Negative (compound: ${formatScore(compound)}). Compound score fell below the -0.05 threshold with ${(neg * 100).toFixed(1)}% negative valence.`;
    } else {
      interpretation = `Classified as Neutral (compound: ${formatScore(compound)}). Neutral descriptive language dominates (${(neu * 100).toFixed(1)}% neutral valence) without crossing positive or negative thresholds.`;
    }

    interpText.textContent = interpretation;
    card.style.display = "block";
  }

  // ============================================================================
  // Explore Reviews Tab: Filter, Search, Pagination
  // ============================================================================

  function populateFilterDropdowns(categories, products) {
    const catSelect = document.getElementById("filter-category-select");
    const prodSelect = document.getElementById("filter-product-select");

    if (catSelect && categories) {
      // Keep existing selection
      const currentVal = catSelect.value;
      catSelect.replaceChildren(createTextElement("option", "All Categories"));
      catSelect.firstChild.value = "";

      categories.forEach((c) => {
        const opt = createTextElement("option", c.product_category || c);
        opt.value = c.product_category || c;
        catSelect.appendChild(opt);
      });
      catSelect.value = currentVal;
    }

    if (prodSelect && products) {
      const currentVal = prodSelect.value;
      prodSelect.replaceChildren(createTextElement("option", "All Products"));
      prodSelect.firstChild.value = "";

      products.forEach((p) => {
        const opt = createTextElement("option", p.product_name || p);
        opt.value = p.product_name || p;
        prodSelect.appendChild(opt);
      });
      prodSelect.value = currentVal;
    }
  }

  async function loadReviews() {
    if (state.isLoadingReviews) return;
    state.isLoadingReviews = true;

    const loadingEl = document.getElementById("reviews-loading");
    const emptyEl = document.getElementById("reviews-empty-state");
    const container = document.getElementById("reviews-list-container");
    const totalBadge = document.getElementById("explore-total-badge");

    if (loadingEl) loadingEl.style.display = "flex";
    if (emptyEl) emptyEl.style.display = "none";
    if (container) container.replaceChildren();

    const limit = state.pageSize;
    const offset = (state.currentPage - 1) * limit;

    const params = new URLSearchParams();
    params.set("limit", String(limit));
    params.set("offset", String(offset));

    if (state.filters.sentiment) params.set("sentiment", state.filters.sentiment);
    if (state.filters.category) params.set("category", state.filters.category);
    if (state.filters.product) params.set("product", state.filters.product);

    try {
      const data = await apiRequest(`/api/v1/demo/reviews?${params.toString()}`);
      state.reviewsTotal = data.total || 0;
      state.reviews = data.reviews || [];

      if (totalBadge) totalBadge.textContent = `Total: ${formatNumber(state.reviewsTotal)}`;

      // Apply client-side search query over returned page if search is present
      let displayReviews = [...state.reviews];
      if (state.filters.search) {
        const q = state.filters.search.toLowerCase();
        displayReviews = displayReviews.filter((r) => {
          return (
            (r.review_text && r.review_text.toLowerCase().includes(q)) ||
            (r.review_title && r.review_title.toLowerCase().includes(q)) ||
            (r.product_name && r.product_name.toLowerCase().includes(q)) ||
            (r.product_category && r.product_category.toLowerCase().includes(q))
          );
        });
      }

      // Client sort on currently loaded items
      sortReviewsList(displayReviews, state.filters.sort);

      renderReviews(displayReviews);
      updatePaginationControls();
    } catch (err) {
      console.error("Failed to load reviews:", err);
      if (container) {
        const errNode = document.createElement("div");
        errNode.className = "rl-alert rl-alert-error";
        errNode.textContent = "Failed to load reviews from API. Please ensure the backend is running.";
        container.appendChild(errNode);
      }
    } finally {
      state.isLoadingReviews = false;
      if (loadingEl) loadingEl.style.display = "none";
    }
  }

  function sortReviewsList(list, sortKey) {
    if (sortKey === "highest_sentiment") {
      list.sort((a, b) => (b.compound_score || 0) - (a.compound_score || 0));
    } else if (sortKey === "lowest_sentiment") {
      list.sort((a, b) => (a.compound_score || 0) - (b.compound_score || 0));
    } else if (sortKey === "highest_rating") {
      list.sort((a, b) => (b.rating || 0) - (a.rating || 0));
    } else if (sortKey === "helpful") {
      list.sort((a, b) => (b.helpful_votes || 0) - (a.helpful_votes || 0));
    }
  }

  function renderReviews(reviews) {
    const container = document.getElementById("reviews-list-container");
    const emptyEl = document.getElementById("reviews-empty-state");
    if (!container) return;

    container.replaceChildren();

    if (!reviews || reviews.length === 0) {
      if (emptyEl) emptyEl.style.display = "flex";
      return;
    }

    if (emptyEl) emptyEl.style.display = "none";

    reviews.forEach((review) => {
      const card = createReviewCard(review);
      container.appendChild(card);
    });
  }

  function createReviewCard(review) {
    const card = document.createElement("div");
    card.className = "rl-review-card";

    // Header
    const header = document.createElement("div");
    header.className = "rl-review-card-header";

    const prodMeta = document.createElement("div");
    const prodName = createTextElement("div", review.product_name || "Product", "rl-review-product");
    const prodCat = createTextElement("span", review.product_category || "General", "rl-review-cat");
    prodMeta.appendChild(prodName);
    prodMeta.appendChild(prodCat);

    const scoreBadge = createTextElement("span", formatScore(review.compound_score), "rl-review-score");
    const label = review.sentiment_label || "Neutral";
    if (label === "Positive") scoreBadge.classList.add("rl-badge-pos");
    else if (label === "Negative") scoreBadge.classList.add("rl-badge-neg");
    else scoreBadge.classList.add("rl-badge-neu");

    header.appendChild(prodMeta);
    header.appendChild(scoreBadge);
    card.appendChild(header);

    // Title
    if (review.review_title) {
      const title = createTextElement("h4", review.review_title, "rl-review-title");
      card.appendChild(title);
    }

    // Body text (Strictly using textContent!)
    const body = createTextElement("p", review.review_text || "", "rl-review-body");
    card.appendChild(body);

    // Footer
    const footer = document.createElement("div");
    footer.className = "rl-review-footer";

    const stars = createTextElement("span", `${renderStars(review.rating)} (${Number(review.rating || 0).toFixed(1)})`, "rl-stars");
    footer.appendChild(stars);

    if (review.verified_purchase) {
      const vp = createTextElement("span", "✓ Verified", "rl-badge rl-badge-muted");
      footer.appendChild(vp);
    }

    if (review.helpful_votes !== undefined && review.helpful_votes > 0) {
      const votes = createTextElement("span", `👍 ${review.helpful_votes} votes`);
      footer.appendChild(votes);
    }

    if (review.review_date) {
      const date = createTextElement("span", formatDate(review.review_date));
      footer.appendChild(date);
    }

    card.appendChild(footer);
    return card;
  }

  function updatePaginationControls() {
    const prevBtn = document.getElementById("btn-page-prev");
    const nextBtn = document.getElementById("btn-page-next");
    const pageInfo = document.getElementById("pagination-info");

    const totalPages = Math.max(1, Math.ceil(state.reviewsTotal / state.pageSize));
    if (pageInfo) {
      pageInfo.textContent = `Page ${state.currentPage} of ${totalPages} (${formatNumber(state.reviewsTotal)} reviews)`;
    }

    if (prevBtn) prevBtn.disabled = state.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = state.currentPage >= totalPages;
  }

  function initExploreFilters() {
    const searchInput = document.getElementById("filter-search-input");
    const sentSelect = document.getElementById("filter-sentiment-select");
    const catSelect = document.getElementById("filter-category-select");
    const prodSelect = document.getElementById("filter-product-select");
    const sortSelect = document.getElementById("filter-sort-select");
    const limitSelect = document.getElementById("filter-limit-select");
    const prevBtn = document.getElementById("btn-page-prev");
    const nextBtn = document.getElementById("btn-page-next");
    const clearBtn = document.getElementById("btn-clear-filters");

    if (searchInput) {
      searchInput.addEventListener("input", debounce(() => {
        state.filters.search = searchInput.value.trim();
        state.currentPage = 1;
        loadReviews();
      }, 300));
    }

    if (sentSelect) {
      sentSelect.addEventListener("change", () => {
        state.filters.sentiment = sentSelect.value;
        state.currentPage = 1;
        loadReviews();
      });
    }

    if (catSelect) {
      catSelect.addEventListener("change", () => {
        state.filters.category = catSelect.value;
        state.currentPage = 1;
        loadReviews();
      });
    }

    if (prodSelect) {
      prodSelect.addEventListener("change", () => {
        state.filters.product = prodSelect.value;
        state.currentPage = 1;
        loadReviews();
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener("change", () => {
        state.filters.sort = sortSelect.value;
        loadReviews();
      });
    }

    if (limitSelect) {
      limitSelect.addEventListener("change", () => {
        state.pageSize = Number(limitSelect.value) || 20;
        state.currentPage = 1;
        loadReviews();
      });
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        if (state.currentPage > 1) {
          state.currentPage--;
          loadReviews();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        const totalPages = Math.ceil(state.reviewsTotal / state.pageSize);
        if (state.currentPage < totalPages) {
          state.currentPage++;
          loadReviews();
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        if (searchInput) searchInput.value = "";
        if (sentSelect) sentSelect.value = "";
        if (catSelect) catSelect.value = "";
        if (prodSelect) prodSelect.value = "";
        if (sortSelect) sortSelect.value = "newest";
        state.filters = { search: "", sentiment: "", category: "", product: "", sort: "newest" };
        state.currentPage = 1;
        loadReviews();
      });
    }
  }

  // ============================================================================
  // Insights Tab: Analytics Tables, Ranking Chart, Top Reviews
  // ============================================================================

  async function loadInsights() {
    try {
      const [cats, prods, topPos, topNeg] = await Promise.allSettled([
        apiRequest("/api/v1/analytics/categories"),
        apiRequest("/api/v1/analytics/products"),
        apiRequest("/api/v1/demo/top-reviews/Positive?limit=5"),
        apiRequest("/api/v1/demo/top-reviews/Negative?limit=5"),
      ]);

      if (cats.status === "fulfilled" && cats.value) {
        state.categories = cats.value;
        renderCategoryTable(cats.value);
        renderCategoryRankingChart(cats.value);
      }

      if (prods.status === "fulfilled" && prods.value) {
        state.products = prods.value;
        renderProductTable(prods.value);
      }

      if (topPos.status === "fulfilled" && topPos.value) {
        state.topPositive = topPos.value;
        renderTopReviewsList("top-positive-container", topPos.value, true);
      }

      if (topNeg.status === "fulfilled" && topNeg.value) {
        state.topNegative = topNeg.value;
        renderTopReviewsList("top-negative-container", topNeg.value, false);
      }
    } catch (err) {
      console.error("Error loading insights:", err);
    }
  }

  function renderCategoryRankingChart(categories) {
    const container = document.getElementById("category-ranking-chart");
    if (!container || !categories) return;

    container.replaceChildren();

    // Sort by average_compound_score descending
    const sorted = [...categories].sort((a, b) => (b.average_compound_score || 0) - (a.average_compound_score || 0));

    sorted.forEach((cat) => {
      const row = document.createElement("div");
      row.className = "rl-bar-row";

      const label = createTextElement("span", cat.product_category || "Category", "rl-bar-label");
      const track = document.createElement("div");
      track.className = "rl-bar-track";

      const score = Number(cat.average_compound_score || 0);
      // Map [-1.0, 1.0] to [0%, 100%]
      const pct = Math.max(5, Math.min(100, Math.round(((score + 1.0) / 2.0) * 100)));

      const fill = document.createElement("div");
      fill.className = "rl-bar-fill";
      fill.style.width = `${pct}%`;
      if (score >= 0.5) fill.style.background = "var(--color-pos)";
      else if (score >= 0.05) fill.style.background = "var(--color-primary)";
      else if (score <= -0.05) fill.style.background = "var(--color-neg)";
      else fill.style.background = "var(--color-neu)";

      track.appendChild(fill);

      const val = createTextElement("span", formatScore(score), "rl-bar-val");

      row.appendChild(label);
      row.appendChild(track);
      row.appendChild(val);
      container.appendChild(row);
    });
  }

  function renderCategoryTable(categories) {
    const tbody = document.getElementById("tbody-category-analytics");
    if (!tbody || !categories) return;

    tbody.replaceChildren();

    categories.forEach((c) => {
      const tr = document.createElement("tr");

      tr.appendChild(createTextElement("td", c.product_category || "—"));
      tr.appendChild(createTextElement("td", formatNumber(c.review_count)));
      tr.appendChild(createTextElement("td", `${Number(c.average_rating || 0).toFixed(2)} ★`));

      const scoreTd = createTextElement("td", formatScore(c.average_compound_score));
      scoreTd.style.fontWeight = "600";
      tr.appendChild(scoreTd);

      tr.appendChild(createTextElement("td", formatPercentage(c.positive_percentage)));
      tr.appendChild(createTextElement("td", formatPercentage(c.negative_percentage)));

      tbody.appendChild(tr);
    });
  }

  function renderProductTable(products) {
    const tbody = document.getElementById("tbody-product-analytics");
    if (!tbody || !products) return;

    tbody.replaceChildren();

    products.forEach((p) => {
      const tr = document.createElement("tr");

      const nameTd = createTextElement("td", p.product_name || "—");
      nameTd.style.fontWeight = "600";
      tr.appendChild(nameTd);

      tr.appendChild(createTextElement("td", p.product_category || "—"));
      tr.appendChild(createTextElement("td", formatNumber(p.review_count)));
      tr.appendChild(createTextElement("td", `${Number(p.average_rating || 0).toFixed(2)} ★`));

      const scoreTd = createTextElement("td", formatScore(p.average_compound_score));
      scoreTd.style.fontWeight = "600";
      tr.appendChild(scoreTd);

      tr.appendChild(createTextElement("td", formatPercentage(p.positive_percentage)));
      tr.appendChild(createTextElement("td", formatPercentage(p.negative_percentage)));

      tbody.appendChild(tr);
    });
  }

  function renderTopReviewsList(containerId, reviews, isPositive) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.replaceChildren();

    if (!reviews || reviews.length === 0) {
      container.appendChild(createTextElement("span", "No reviews available in this tier.", "rl-hint"));
      return;
    }

    reviews.forEach((r) => {
      const item = document.createElement("div");
      item.className = "rl-top-review-item";

      const topRow = document.createElement("div");
      topRow.style.display = "flex";
      topRow.style.justifyContent = "space-between";
      topRow.style.alignItems = "center";
      topRow.style.marginBottom = "0.35rem";

      const prod = createTextElement("strong", r.product_name || "Product", "rl-review-product");
      const badge = createTextElement(
        "span",
        formatScore(r.compound_score),
        `rl-badge rl-badge-sm ${isPositive ? "rl-badge-pos" : "rl-badge-neg"}`
      );
      topRow.appendChild(prod);
      topRow.appendChild(badge);
      item.appendChild(topRow);

      if (r.review_title) {
        const title = createTextElement("div", r.review_title, "rl-review-title");
        title.style.fontSize = "0.85rem";
        item.appendChild(title);
      }

      const body = createTextElement("p", r.review_text || "", "rl-hint");
      body.style.lineHeight = "1.4";
      body.style.color = "var(--text-muted)";
      item.appendChild(body);

      container.appendChild(item);
    });
  }

  // ============================================================================
  // URL Analysis Tab: Controlled Extraction Interface
  // ============================================================================

  function initUrlAnalysis() {
    const urlInput = document.getElementById("url-target-input");
    const maxSelect = document.getElementById("url-max-reviews");
    const submitBtn = document.getElementById("btn-submit-url");
    const statusArea = document.getElementById("url-status-area");
    const statusMsg = document.getElementById("url-status-message");
    const resultsContainer = document.getElementById("url-results-container");
    const switchDemoBtn = document.getElementById("btn-switch-to-demo");

    if (switchDemoBtn) {
      switchDemoBtn.addEventListener("click", () => switchTab("explore"));
    }

    if (!submitBtn) return;

    submitBtn.addEventListener("click", async () => {
      const urlVal = urlInput.value.trim();
      const maxVal = Number(maxSelect.value) || 20;

      statusArea.style.display = "none";
      resultsContainer.style.display = "none";
      resultsContainer.replaceChildren();

      // Client-side empty validation
      if (!urlVal) {
        statusArea.className = "rl-alert rl-alert-error";
        statusMsg.textContent = "Please provide a valid public review page URL (http/https).";
        statusArea.style.display = "block";
        return;
      }

      submitBtn.disabled = true;
      const originalText = submitBtn.innerHTML;
      submitBtn.textContent = "Submitting…";

      try {
        const result = await apiRequest("/api/v1/analyze/url", {
          method: "POST",
          body: JSON.stringify({ url: urlVal, max_reviews: maxVal, preview: true }),
        });

        if (result && result.status === "auth_required") {
          statusArea.className = "rl-alert rl-alert-warning";
          statusArea.style.display = "block";
          statusMsg.replaceChildren();

          const authHeader = createTextElement("div", "🔒 Amazon Login Restricted: Standalone Review Permalink", "rl-font-bold");
          authHeader.style.color = "#f59e0b";
          authHeader.style.marginBottom = "6px";
          statusMsg.appendChild(authHeader);

          const authDesc = createTextElement("div", result.message || "Amazon restricts individual review permalinks behind account login.", "rl-text-xs");
          authDesc.style.lineHeight = "1.5";
          statusMsg.appendChild(authDesc);

          const tipBox = document.createElement("div");
          tipBox.style.marginTop = "10px";
          tipBox.style.padding = "8px 12px";
          tipBox.style.background = "rgba(0, 0, 0, 0.25)";
          tipBox.style.borderRadius = "6px";
          tipBox.style.border = "1px solid rgba(245, 158, 11, 0.35)";

          const tipTitle = createTextElement("strong", "💡 Next Step / Guidance:", "rl-text-xs");
          tipTitle.style.color = "#38bdf8";
          tipTitle.style.display = "block";
          tipTitle.style.marginBottom = "4px";
          tipBox.appendChild(tipTitle);

          const tipText = createTextElement(
            "p",
            "Amazon restricts single review permalinks (/portal/customer-reviews/srp/-/ or /gp/customer-reviews/) behind account login. To extract and score all customer reviews for this product without login barriers, paste the main product URL (e.g. https://www.amazon.in/dp/<ASIN>).",
            "rl-hint"
          );
          tipText.style.margin = "0";
          tipBox.appendChild(tipText);
          statusMsg.appendChild(tipBox);

          resultsContainer.style.display = "none";
          return;
        }

        if (result && result.reviews && result.reviews.length > 0) {
          statusArea.className = "rl-alert rl-alert-info";
          statusArea.style.display = "block";
          statusMsg.replaceChildren();

          const isSaved = result.saved_to_db !== false;
          const statusHeader = createTextElement(
            "div",
            `✓ Extracted & Scored ${result.reviews.length} Opinions from ${result.hostname || "Source"} (${isSaved ? "Saved to SQLite & LocalStorage" : "Preview Mode - Not Saved to Database"})`,
            "rl-font-bold"
          );
          statusMsg.appendChild(statusHeader);

          if (result.page_title) {
            const pageTitleEl = createTextElement("div", `Target: ${result.page_title}`, "rl-text-xs rl-opacity-80");
            pageTitleEl.style.marginTop = "4px";
            statusMsg.appendChild(pageTitleEl);
          }

          if (result.average_compound_score !== undefined) {
            const profileEl = createTextElement("div", `Webpage Sentiment Profile: Avg Score: ${result.average_compound_score > 0 ? '+' : ''}${result.average_compound_score} | 🟢 ${result.positive_percentage}% Pos | 🟡 ${result.neutral_percentage}% Neu | 🔴 ${result.negative_percentage}% Neg`, "rl-text-xs");
            profileEl.style.marginTop = "4px";
            profileEl.style.fontFamily = "monospace";
            statusMsg.appendChild(profileEl);
          }

          resultsContainer.style.display = "grid";
          result.reviews.forEach((r, idx) => {
            const card = document.createElement("div");
            card.className = "rl-review-card";

            const header = document.createElement("div");
            header.className = "rl-review-card-header";
            const badge = createTextElement("span", r.sentiment_label, `rl-badge ${r.sentiment_label === "Positive" ? "rl-badge-pos" : r.sentiment_label === "Negative" ? "rl-badge-neg" : "rl-badge-neu"}`);
            
            const rightHeader = document.createElement("div");
            rightHeader.style.display = "flex";
            rightHeader.style.alignItems = "center";
            rightHeader.style.gap = "8px";

            if (r.rating) {
              const ratingEl = createTextElement("span", `★ ${r.rating}`, "rl-text-xs");
              ratingEl.style.color = "#f59e0b";
              ratingEl.style.fontWeight = "bold";
              rightHeader.appendChild(ratingEl);
            }

            const score = createTextElement("span", formatScore(r.scores ? r.scores.compound : 0), "rl-review-score");
            rightHeader.appendChild(score);

            header.appendChild(badge);
            header.appendChild(rightHeader);
            card.appendChild(header);

            const body = createTextElement("p", r.text || "", "rl-review-body");
            card.appendChild(body);

            const footer = document.createElement("div");
            footer.style.display = "flex";
            footer.style.justifyContent = "space-between";
            footer.style.marginTop = "8px";
            footer.style.paddingTop = "6px";
            footer.style.borderTop = "1px solid rgba(255,255,255,0.05)";
            footer.style.fontSize = "11px";
            footer.style.color = "#64748b";

            const authorEl = createTextElement("span", r.author || `Opinion #${idx + 1}`, "");
            const savedEl = createTextElement("span", isSaved ? "✓ Saved to SQLite" : "Preview Mode", "");
            footer.appendChild(authorEl);
            footer.appendChild(savedEl);
            card.appendChild(footer);

            resultsContainer.appendChild(card);
          });
        } else {
          statusArea.className = "rl-alert rl-alert-info";
          statusMsg.textContent = "No review items were extracted from the specified URL using configured selectors.";
          statusArea.style.display = "block";
        }
      } catch (err) {
        statusArea.style.display = "block";
        if (err.status === 503) {
          statusArea.className = "rl-alert rl-alert-info";
          statusMsg.textContent = "Live URL analysis is disabled in this local environment. You can still use Text Analysis and Demo Insights. To enable a permitted source, configure the backend responsibly.";
        } else if (err.status === 400 || err.status === 422) {
          statusArea.className = "rl-alert rl-alert-error";
          statusMsg.textContent = err.message || "Invalid target URL or disallowed network address.";
        } else {
          statusArea.className = "rl-alert rl-alert-error";
          statusMsg.textContent = err.message || "Failed to process URL extraction request.";
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }

  // ============================================================================
  // Global Event Listeners & Bootstrapping
  // ============================================================================

  function initEvents() {
    // Navigation Tabs
    const tabButtons = document.querySelectorAll(".rl-tab-btn");
    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const tabId = btn.id.replace("tab-btn-", "");
        switchTab(tabId);
      });
    });

    // Refresh Dashboard Button
    const refreshBtn = document.getElementById("btn-refresh-dashboard");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", async () => {
        refreshBtn.disabled = true;
        await checkApiHealth();
        await loadOverview();
        if (state.activeTab === "explore") await loadReviews();
        if (state.activeTab === "insights") await loadInsights();
        refreshBtn.disabled = false;
      });
    }

    // Hero Action Buttons
    const heroAnalyzeBtn = document.getElementById("btn-hero-analyze");
    if (heroAnalyzeBtn) {
      heroAnalyzeBtn.addEventListener("click", () => switchTab("analyze"));
    }

    const heroInsightsBtn = document.getElementById("btn-hero-insights");
    if (heroInsightsBtn) {
      heroInsightsBtn.addEventListener("click", () => switchTab("insights"));
    }

    // Retry Connection Button
    const retryBtn = document.getElementById("btn-retry-connection");
    if (retryBtn) {
      retryBtn.addEventListener("click", async () => {
        await checkApiHealth();
        await loadOverview();
      });
    }

    // Module Initializations
    initAnalyzeText();
    initExploreFilters();
    initUrlAnalysis();
  }

  // DOM Content Loaded Handler
  document.addEventListener("DOMContentLoaded", async () => {
    initEvents();
    await loadOverview();
  });
})();
