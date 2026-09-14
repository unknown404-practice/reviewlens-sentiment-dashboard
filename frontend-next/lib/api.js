// ReviewLens Next.js Centralized API & LocalStorage Client
// ========================================================
// Fully dynamic, secure, resilient client for FastAPI backend integration.

/**
 * Safely resolves the API Base URL.
 * - Reads strictly from NEXT_PUBLIC_API_BASE_URL.
 * - In development, falls back to http://127.0.0.1:8000 if not set.
 * - In production, throws a clear configuration error if unset.
 * - Trims trailing slashes safely.
 */
export function getApiBaseUrl() {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl && typeof envUrl === "string" && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, "");
  }

  // Local development fallback
  const isDev = process.env.NODE_ENV === "development" || !process.env.NODE_ENV;
  if (isDev) {
    return "http://127.0.0.1:8000";
  }

  throw new Error(
    "Configuration Error: NEXT_PUBLIC_API_BASE_URL is not configured. " +
    "Please configure NEXT_PUBLIC_API_BASE_URL in your hosting platform (e.g., Vercel)."
  );
}

export const API_BASE = (function () {
  try {
    return getApiBaseUrl();
  } catch (e) {
    return "";
  }
})();

const LOCAL_STORAGE_KEY = "reviewlens_saved_reviews_v1";

/**
 * Sanitizes and cleans customer review text by stripping automated scraping artifacts,
 * inline button remnants ("Brief content visible", "double tap to read full content",
 * "Read moreRead less", "Helpful", "Report"), and repeated whitespace.
 */
export function cleanReviewDisplay(text) {
  if (!text || typeof text !== "string") return "";
  let cleaned = text;

  // 1. Remove Amazon reporting / vote confirmation boilerplate
  cleaned = cleaned.replace(
    /(?:Helpful)?\s*Sending feedback\.\.\..*?(?:CancelReport|Report|investigate in the next few days\.)/gis,
    ""
  );
  cleaned = cleaned.replace(
    /Sorry,\s*We failed to report this review.*?(?:CancelReport|Report)/gis,
    ""
  );
  cleaned = cleaned.replace(
    /We'll check if this review meets our community guidelines.*?CancelReport/gis,
    ""
  );
  cleaned = cleaned.replace(
    /Opens in a new tab\.\s*If it doesn't, we'll remove it\.\s*CancelReport/gis,
    ""
  );

  // 2. Remove "X people found this helpful" / "Helpful" / "Report"
  cleaned = cleaned.replace(/\b\d+\s+(?:people|person)\s+found\s+this\s+helpful\b/gi, "");
  cleaned = cleaned.replace(/\bOne person found this helpful\b/gi, "");
  cleaned = cleaned.replace(/\bHelpful\b\s*\bReport\b/gi, "");

  // 3. Remove "Brief content visible, double tap to read full content"
  cleaned = cleaned.replace(/Brief content visible,\s*double tap to read full content\.?/gi, "");
  cleaned = cleaned.replace(/Full content visible,\s*double tap to read brief content\.?/gi, "");
  cleaned = cleaned.replace(/\bRead more\s*Read less\b/gi, "");
  cleaned = cleaned.replace(/\bRead more\b|\bRead less\b/gi, "");

  // 4. Remove inline metadata prefixes if glued to text:
  cleaned = cleaned.replace(/\bSize:\s*[^V\n]+Verified Purchase/gi, "");
  cleaned = cleaned.replace(/\bVerified Purchase\b/gi, "");
  cleaned = cleaned.replace(/Reviewed in [a-zA-Z\s]+ on \d{1,2}\s+[a-zA-Z]+\s+\d{4}/gi, "");

  // 5. Remove author/stars prefix if glued
  cleaned = cleaned.replace(/^[^a-zA-Z0-9]*[A-Za-z0-9\s._-]*\d(?:\.\d)?\s*out of 5 stars\s*/i, "");

  // 6. Normalize multiple spaces and trim
  cleaned = cleaned.replace(/\s{2,}/g, " ").trim();

  return cleaned || text;
}

// ----------------------------------------------------------------------------
// LocalStorage Persistence Helpers
// ----------------------------------------------------------------------------
export function getLocalReviews() {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

export function saveReviewToLocal(review) {
  if (typeof window === "undefined" || !review) return;
  try {
    const existing = getLocalReviews();
    const filtered = existing.filter((r) => r.id !== review.id);
    const updated = [review, ...filtered];
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updated.slice(0, 500)));
  } catch (e) {
    // Silently ignore quota exceeded
  }
}

export function saveReviewsBatchToLocal(reviews) {
  if (typeof window === "undefined" || !reviews || !reviews.length) return;
  try {
    const existing = getLocalReviews();
    const newIds = new Set(reviews.map((r) => r.id));
    const filtered = existing.filter((r) => !newIds.has(r.id));
    const updated = [...reviews, ...filtered];
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updated.slice(0, 500)));
  } catch (e) {
    // Silently ignore quota exceeded
  }
}

export function deleteReviewFromLocal(id) {
  if (typeof window === "undefined") return;
  try {
    const existing = getLocalReviews();
    const updated = existing.filter((r) => r.id !== id);
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updated));
  } catch (e) {
    // Silently ignore
  }
}

export function clearAllLocalReviews() {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(LOCAL_STORAGE_KEY);
  } catch (e) {
    // Silently ignore
  }
}

// ----------------------------------------------------------------------------
// Core HTTP Fetch Wrapper with 15s Timeout and Resilient Error Handling
// ----------------------------------------------------------------------------
async function request(endpoint, options = {}) {
  let baseUrl;
  try {
    baseUrl = getApiBaseUrl();
  } catch (configErr) {
    const err = new Error(configErr.message);
    err.status = 500;
    err.code = "CONFIG_ERROR";
    throw err;
  }

  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${cleanEndpoint}`;

  const timeoutMs = options.timeout || 15000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const config = {
      ...options,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
    };

    const res = await fetch(url, config);
    clearTimeout(timeoutId);

    let data = {};
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      try {
        data = await res.json();
      } catch {
        data = { message: "Invalid JSON response from server." };
      }
    } else {
      const txt = await res.text().catch(() => "");
      data = { message: txt || `HTTP Error ${res.status}` };
    }

    if (!res.ok) {
      let friendlyMessage = "An unexpected error occurred.";
      if (res.status === 400) {
        friendlyMessage = data.detail || data.message || "Invalid request parameter or URL format.";
      } else if (res.status === 422) {
        friendlyMessage = data.detail || data.message || "Validation error: please check your input.";
      } else if (res.status === 429) {
        friendlyMessage = "API rate limit reached (30 requests/min). Please wait a moment before trying again.";
      } else if (res.status === 503) {
        friendlyMessage = data.message || "Service temporarily unavailable.";
      } else if (res.status === 502 || res.status === 504) {
        friendlyMessage = "Backend gateway or proxy timeout. Please retry shortly.";
      } else {
        friendlyMessage = data.detail || data.message || `Request failed (Status ${res.status}).`;
      }

      const err = new Error(friendlyMessage);
      err.status = res.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (fetchErr) {
    clearTimeout(timeoutId);

    if (fetchErr.name === "AbortError") {
      const err = new Error("Request timed out after 15 seconds. Please try again.");
      err.status = 408;
      err.code = "TIMEOUT";
      throw err;
    }

    if (fetchErr.status) {
      throw fetchErr;
    }

    const err = new Error("Unable to connect to the ReviewLens API server. Please check your connection.");
    err.status = 0;
    err.code = "NETWORK_ERROR";
    throw err;
  }
}

// ----------------------------------------------------------------------------
// API Endpoints
// ----------------------------------------------------------------------------
export async function checkApiHealth() {
  return request("/health");
}

export async function analyzeText(text) {
  const result = await request("/api/v1/analyze/text", {
    method: "POST",
    body: JSON.stringify({ text }),
  });

  if (result && result.saved_id) {
    saveReviewToLocal({
      id: result.saved_id,
      source_type: "text",
      source_url: null,
      page_title: null,
      product_name: "Text Analysis Input",
      product_category: "Custom Text",
      review_text: result.text,
      rating: null,
      sentiment_label: result.sentiment_label,
      sentiment_strength: result.sentiment_strength,
      compound_score: result.scores?.compound ?? 0,
      scores: result.scores,
      created_at: new Date().toISOString(),
    });
  }

  return result;
}

export async function analyzeUrl(url, maxReviews = 20) {
  const result = await request("/api/v1/analyze/url", {
    method: "POST",
    body: JSON.stringify({ url, max_reviews: maxReviews, preview: false }),
  });

  if (result && result.saved_to_db && result.reviews && result.reviews.length) {
    const mapped = result.reviews.map((r, idx) => ({
      id: Date.now() + idx,
      source_type: "url",
      source_url: result.source_url,
      page_title: result.page_title,
      product_name: result.page_title || "Extracted URL Product",
      product_category: "Web & E-Commerce",
      review_text: r.text,
      rating: r.rating || 4.0,
      sentiment_label: r.sentiment_label,
      sentiment_strength: r.sentiment_strength,
      compound_score: r.scores?.compound ?? 0,
      scores: r.scores,
      created_at: new Date().toISOString(),
    }));
    saveReviewsBatchToLocal(mapped);
  }

  return result;
}

export async function fetchSavedHistory({ sourceType, sentiment, search, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (sourceType && sourceType !== "all") params.append("source_type", sourceType);
  if (sentiment && sentiment !== "all") params.append("sentiment", sentiment);
  if (search && search.trim()) params.append("search", search.trim());
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  try {
    const res = await request(`/api/v1/history?${params.toString()}`);
    if (res && res.reviews) {
      saveReviewsBatchToLocal(res.reviews);
    }
    return res;
  } catch (e) {
    // Fallback to local storage if network is offline
    const local = getLocalReviews();
    let filtered = [...local];
    if (sourceType && sourceType !== "all") {
      filtered = filtered.filter((r) => r.source_type === sourceType);
    }
    if (sentiment && sentiment !== "all") {
      filtered = filtered.filter((r) => r.sentiment_label.toLowerCase() === sentiment.toLowerCase());
    }
    if (search && search.trim()) {
      const q = search.trim().toLowerCase();
      filtered = filtered.filter(
        (r) =>
          (r.review_text && r.review_text.toLowerCase().includes(q)) ||
          (r.product_name && r.product_name.toLowerCase().includes(q))
      );
    }
    return {
      status: "fallback_local",
      total: filtered.length,
      limit,
      offset,
      reviews: filtered.slice(offset, offset + limit),
    };
  }
}

export async function fetchHistoryStats() {
  try {
    return await request("/api/v1/history/stats");
  } catch (e) {
    const local = getLocalReviews();
    const textCount = local.filter((r) => r.source_type === "text").length;
    const urlCount = local.filter((r) => r.source_type === "url").length;
    const posCount = local.filter((r) => r.sentiment_label === "Positive").length;
    const neuCount = local.filter((r) => r.sentiment_label === "Neutral").length;
    const negCount = local.filter((r) => r.sentiment_label === "Negative").length;
    const avgCompound = local.length
      ? local.reduce((acc, r) => acc + (r.compound_score || 0), 0) / local.length
      : 0;

    return {
      status: "fallback_local",
      total_reviews: local.length,
      text_count: textCount,
      url_count: urlCount,
      positive_count: posCount,
      neutral_count: neuCount,
      negative_count: negCount,
      average_compound_score: Math.round(avgCompound * 10000) / 10000,
    };
  }
}

export async function deleteSavedReview(id) {
  deleteReviewFromLocal(id);
  try {
    return await request(`/api/v1/history/${id}`, { method: "DELETE" });
  } catch {
    return { status: "local_only", message: "Deleted from client storage." };
  }
}

export async function clearAllSavedReviews() {
  clearAllLocalReviews();
  try {
    return await request("/api/v1/history", { method: "DELETE" });
  } catch {
    return { status: "local_only", message: "Cleared client storage." };
  }
}

export async function fetchDemoSummary() {
  return request("/api/v1/demo/summary");
}

export async function fetchDemoReviews({ sentiment, category, product, limit = 20, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (sentiment && sentiment !== "All") params.append("sentiment", sentiment);
  if (category && category !== "All") params.append("category", category);
  if (product && product !== "All") params.append("product", product);
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  return request(`/api/v1/demo/reviews?${params.toString()}`);
}

export async function fetchProductAnalytics() {
  return request("/api/v1/analytics/products");
}

export async function fetchCategoryAnalytics() {
  return request("/api/v1/analytics/categories");
}
