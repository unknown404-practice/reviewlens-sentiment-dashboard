"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  AlertCircle,
  ArrowLeftRight,
  BarChart3,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Database,
  ExternalLink,
  Filter,
  Globe,
  HelpCircle,
  Layers,
  Link2,
  Menu,
  RefreshCw,
  Search,
  ShieldCheck,
  Sliders,
  Sparkles,
  Star,
  Tag,
  Trash2,
  TrendingDown,
  TrendingUp,
  X,
  XCircle,
  Zap,
} from "lucide-react";
import {
  API_BASE,
  analyzeText,
  analyzeUrl,
  checkApiHealth,
  cleanReviewDisplay,
  clearAllSavedReviews,
  deleteSavedReview,
  fetchCategoryAnalytics,
  fetchDemoReviews,
  fetchDemoSummary,
  fetchHistoryStats,
  fetchProductAnalytics,
  fetchSavedHistory,
  getLocalReviews,
} from "../lib/api";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // API Status & Connection
  const [apiStatus, setApiStatus] = useState("checking");
  const [apiVersion, setApiVersion] = useState("1.0.0");
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Overview / Demo Data State
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);

  // Text Analysis State
  const [textInput, setTextInput] = useState("");
  const [textResult, setTextResult] = useState(null);
  const [isAnalyzingText, setIsAnalyzingText] = useState(false);
  const [textError, setTextError] = useState(null);

  // URL Analysis State
  const [urlInput, setUrlInput] = useState("https://www.amazon.in/dp/B0CG29HWSS");
  const [urlMaxReviews, setUrlMaxReviews] = useState(10);
  const [urlResult, setUrlResult] = useState(null);
  const [isAnalyzingUrl, setIsAnalyzingUrl] = useState(false);
  const [urlError, setUrlError] = useState(null);

  // Saved History State (SQLite & LocalStorage)
  const [historyItems, setHistoryItems] = useState([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyStats, setHistoryStats] = useState(null);
  const [historySourceFilter, setHistorySourceFilter] = useState("all");
  const [historySentimentFilter, setHistorySentimentFilter] = useState("all");
  const [historySearch, setHistorySearch] = useState("");
  const [historyPage, setHistoryPage] = useState(1);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Explore Reviews State
  const [demoReviews, setDemoReviews] = useState([]);
  const [demoTotal, setDemoTotal] = useState(0);
  const [exploreSentiment, setExploreSentiment] = useState("All");
  const [exploreCategory, setExploreCategory] = useState("All");
  const [explorePage, setExplorePage] = useState(1);
  const [loadingExplore, setLoadingExplore] = useState(false);

  // Insights State
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loadingInsights, setLoadingInsights] = useState(false);

  // --------------------------------------------------------------------------
  // Check Health on Mount & Refresh
  // --------------------------------------------------------------------------
  useEffect(() => {
    async function initHealth() {
      try {
        const res = await checkApiHealth();
        if (res && res.status === "healthy") {
          setApiStatus("online");
          setApiVersion(res.version || "1.0.0");
        } else {
          setApiStatus("offline");
        }
      } catch {
        setApiStatus("offline");
      }
    }
    initHealth();
  }, [refreshTrigger]);

  // --------------------------------------------------------------------------
  // Fetch Summary & Initial Stats
  // --------------------------------------------------------------------------
  useEffect(() => {
    async function loadSummary() {
      setLoadingSummary(true);
      try {
        const data = await fetchDemoSummary();
        setSummary(data);
      } catch (e) {
        console.error("Summary fetch notice:", e?.message);
      } finally {
        setLoadingSummary(false);
      }
    }
    loadSummary();
  }, [refreshTrigger]);

  // --------------------------------------------------------------------------
  // Fetch History whenever filters or activeTab change
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (activeTab === "history" || activeTab === "overview") {
      loadHistoryData();
    }
  }, [activeTab, historySourceFilter, historySentimentFilter, historySearch, historyPage, refreshTrigger]);

  async function loadHistoryData() {
    setLoadingHistory(true);
    try {
      const stats = await fetchHistoryStats();
      setHistoryStats(stats);

      const limit = 20;
      const offset = (historyPage - 1) * limit;
      const res = await fetchSavedHistory({
        sourceType: historySourceFilter,
        sentiment: historySentimentFilter,
        search: historySearch,
        limit,
        offset,
      });
      setHistoryItems(res.reviews || []);
      setHistoryTotal(res.total || 0);
    } catch (err) {
      console.error("History fetch notice:", err?.message);
    } finally {
      setLoadingHistory(false);
    }
  }

  // --------------------------------------------------------------------------
  // Fetch Explore Reviews
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (activeTab === "explore") {
      loadExploreReviews();
    }
  }, [activeTab, exploreSentiment, exploreCategory, explorePage, refreshTrigger]);

  async function loadExploreReviews() {
    setLoadingExplore(true);
    try {
      const limit = 12;
      const offset = (explorePage - 1) * limit;
      const res = await fetchDemoReviews({
        sentiment: exploreSentiment,
        category: exploreCategory,
        limit,
        offset,
      });
      setDemoReviews(res.reviews || []);
      setDemoTotal(res.total || 0);
    } catch (e) {
      console.error("Explore fetch notice:", e?.message);
    } finally {
      setLoadingExplore(false);
    }
  }

  // --------------------------------------------------------------------------
  // Fetch Insights
  // --------------------------------------------------------------------------
  useEffect(() => {
    if (activeTab === "insights") {
      loadInsights();
    }
  }, [activeTab, refreshTrigger]);

  async function loadInsights() {
    setLoadingInsights(true);
    try {
      const [p, c] = await Promise.all([fetchProductAnalytics(), fetchCategoryAnalytics()]);
      setProducts(p || []);
      setCategories(c || []);
    } catch (e) {
      console.error("Insights fetch notice:", e?.message);
    } finally {
      setLoadingInsights(false);
    }
  }

  // --------------------------------------------------------------------------
  // Handlers
  // --------------------------------------------------------------------------
  const handleAnalyzeText = async (e) => {
    e.preventDefault();
    if (!textInput.trim()) return;

    setIsAnalyzingText(true);
    setTextError(null);
    try {
      const res = await analyzeText(textInput);
      setTextResult(res);
      loadHistoryData();
    } catch (err) {
      setTextError(err.message || "Text sentiment evaluation failed.");
    } finally {
      setIsAnalyzingText(false);
    }
  };

  const handleAnalyzeUrl = async (e) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    setIsAnalyzingUrl(true);
    setUrlError(null);
    try {
      const res = await analyzeUrl(urlInput, urlMaxReviews);
      setUrlResult(res);
      loadHistoryData();
    } catch (err) {
      setUrlError(err.message || "Failed to extract and score reviews from target URL.");
    } finally {
      setIsAnalyzingUrl(false);
    }
  };

  const handleDeleteSavedReview = async (id) => {
    if (!confirm("Remove this review from SQLite and client storage?")) return;
    await deleteSavedReview(id);
    loadHistoryData();
  };

  const handleClearAllSavedReviews = async () => {
    if (!confirm("Are you sure you want to clear ALL saved reviews from SQLite and client storage?")) return;
    await clearAllSavedReviews();
    loadHistoryData();
  };

  const getSentimentBadge = (label, strength) => {
    if (label === "Positive") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <TrendingUp className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>{strength || label}</span>
        </span>
      );
    }
    if (label === "Negative") {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <TrendingDown className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>{strength || label}</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <Activity className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
        <span>{strength || label}</span>
      </span>
    );
  };

  const navTabs = [
    { id: "overview", label: "Executive Overview", icon: BarChart3 },
    { id: "text", label: "Live Text Analyzer", icon: Zap },
    { id: "url", label: "Live URL Review Analyzer", icon: Globe, highlight: true },
    {
      id: "history",
      label: "Saved History (SQLite)",
      icon: Database,
      badge: historyStats?.total_reviews || 0,
    },
    { id: "explore", label: "Explore Reviews", icon: Search },
    { id: "insights", label: "Insights & Rankings", icon: TrendingUp },
    { id: "about", label: "Pipeline & Architecture", icon: Layers },
  ];

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col selection:bg-brand-primary/20 selection:text-brand-primary">
      {/* -------------------------------------------------------------------- */}
      {/* Top Header / App Bar (Fully Responsive)                              */}
      {/* -------------------------------------------------------------------- */}
      <header className="sticky top-0 z-50 glass-card border-b border-white/10 px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 shrink-0 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white font-bold text-lg">
            RL
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-lg sm:text-xl font-bold bg-gradient-to-r from-sky-400 via-blue-400 to-indigo-300 bg-clip-text text-transparent truncate">
                ReviewLens
              </h1>
              <span className="hidden sm:inline-block text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-medium">
                Next.js + FastAPI
              </span>
            </div>
            <p className="text-[11px] sm:text-xs text-slate-400 truncate">
              E-Commerce Sentiment Intelligence & VADER Analytics
            </p>
          </div>
        </div>

        {/* Header Right Controls */}
        <div className="flex items-center gap-2 shrink-0">
          {/* SQLite Badge (Desktop) */}
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-secondary border border-white/5 text-xs text-slate-300">
            <Database className="w-3.5 h-3.5 text-sky-400" aria-hidden="true" />
            <span>SQLite Storage:</span>
            <span className="font-semibold text-emerald-400">
              {historyStats ? `${historyStats.total_reviews} Real Reviews` : "Ready"}
            </span>
          </div>

          {/* FastAPI Health Pill */}
          <button
            type="button"
            onClick={() => setRefreshTrigger((prev) => prev + 1)}
            title="Click to refresh connection status"
            aria-label={`API status: ${apiStatus === "online" ? "Connected" : "Offline"}. Click to refresh.`}
            className={`min-h-[40px] px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors flex items-center gap-1.5 ${
              apiStatus === "online"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25 hover:bg-emerald-500/20"
                : "bg-rose-500/10 text-rose-400 border-rose-500/25 hover:bg-rose-500/20"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                apiStatus === "online" ? "bg-emerald-400 animate-pulse" : "bg-rose-400"
              }`}
              aria-hidden="true"
            />
            <span className="hidden sm:inline">
              {apiStatus === "online" ? `API Online (v${apiVersion})` : "API Offline"}
            </span>
            <span className="sm:hidden text-[11px]">
              {apiStatus === "online" ? "Online" : "Offline"}
            </span>
          </button>

          {/* Refresh Action Button */}
          <button
            type="button"
            onClick={() => setRefreshTrigger((prev) => prev + 1)}
            className="min-h-[40px] min-w-[40px] p-2 rounded-lg bg-surface-secondary hover:bg-surface-tertiary text-slate-300 transition-colors border border-white/5 flex items-center justify-center"
            title="Refresh dashboard data"
            aria-label="Refresh dashboard data"
          >
            <RefreshCw className="w-4 h-4" aria-hidden="true" />
          </button>

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden min-h-[40px] min-w-[40px] p-2 rounded-lg bg-brand-primary/10 text-brand-primary hover:bg-brand-primary/20 border border-brand-primary/20 flex items-center justify-center transition-colors"
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* -------------------------------------------------------------------- */}
      {/* Mobile Navigation Drawer Dropdown                                    */}
      {/* -------------------------------------------------------------------- */}
      {mobileMenuOpen && (
        <nav
          className="md:hidden glass-card border-b border-white/10 px-4 py-3 space-y-1 bg-surface-secondary/95 animate-fadeIn"
          role="navigation"
          aria-label="Mobile navigation"
        >
          {navTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  setActiveTab(tab.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full min-h-[44px] flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand-primary text-slate-950 font-bold shadow-sm"
                    : "text-slate-300 hover:text-white hover:bg-white/5"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? "text-slate-950" : "text-sky-400"}`} />
                  <span>{tab.label}</span>
                </div>
                {tab.badge !== undefined && tab.badge > 0 && (
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      isActive ? "bg-slate-950 text-sky-400" : "bg-sky-500/20 text-sky-300"
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      )}

      {/* -------------------------------------------------------------------- */}
      {/* Desktop Horizontal Tabs Bar                                         */}
      {/* -------------------------------------------------------------------- */}
      <nav
        className="hidden md:flex bg-surface/60 border-b border-white/5 px-6 items-center gap-1.5 overflow-x-auto py-2.5 scroll-smooth"
        role="tablist"
        aria-label="Dashboard navigation tabs"
      >
        {navTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              role="tab"
              type="button"
              aria-selected={isActive}
              aria-controls={`tabpanel-${tab.id}`}
              id={`tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`min-h-[40px] flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${
                isActive
                  ? "bg-brand-primary text-slate-950 shadow-md font-bold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
              } ${tab.highlight && !isActive ? "text-sky-400 border border-sky-500/25 bg-sky-500/5" : ""}`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-slate-950" : ""}`} aria-hidden="true" />
              <span>{tab.label}</span>
              {tab.badge !== undefined && tab.badge > 0 && (
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                    isActive ? "bg-slate-950 text-sky-400" : "bg-sky-500/20 text-sky-300"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* -------------------------------------------------------------------- */}
      {/* Main Content Area (Fluid Container)                                  */}
      {/* -------------------------------------------------------------------- */}
      <main
        className="flex-1 p-3 sm:p-5 md:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6"
        id={`tabpanel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeTab}`}
      >
        {/* ================================================================== */}
        {/* TAB 1: EXECUTIVE OVERVIEW                                          */}
        {/* ================================================================== */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Hero Welcome Banner */}
            <section className="glass-card rounded-2xl p-5 sm:p-7 relative overflow-hidden border border-white/10" aria-label="Hero overview">
              <div className="absolute -right-12 -bottom-12 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 relative z-10">
                <div className="space-y-2 max-w-3xl">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 text-sky-400 text-xs font-semibold border border-sky-500/20">
                    <Sparkles className="w-3.5 h-3.5 shrink-0" aria-hidden="true" /> Next.js Production Architecture
                  </div>
                  <h2 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-white tracking-tight leading-snug">
                    E-Commerce Sentiment Intelligence Platform
                  </h2>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    Powered by deterministic VADER valence analytics, asynchronous FastAPI microservices, and persistent SQLite review storage without synthetic contamination.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
                  <button
                    type="button"
                    onClick={() => setActiveTab("url")}
                    className="min-h-[44px] px-4 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-sky-500/25 transition-all flex items-center justify-center gap-2"
                  >
                    <Globe className="w-4 h-4 shrink-0" aria-hidden="true" /> Live URL Preview
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab("history")}
                    className="min-h-[44px] px-4 py-2.5 rounded-xl bg-surface-secondary hover:bg-surface-tertiary text-slate-200 font-medium text-xs sm:text-sm border border-white/10 transition-all flex items-center justify-center gap-2"
                  >
                    <Database className="w-4 h-4 text-sky-400 shrink-0" aria-hidden="true" /> View SQLite History
                  </button>
                </div>
              </div>
            </section>

            {/* KPI Metric Cards (Responsive Grid: 1 col on < 480px, 2 col on tablet, 4 col on desktop) */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4" aria-label="Key Performance Indicators">
              <div className="glass-card rounded-xl p-4 sm:p-5 border border-white/5 space-y-1">
                <div className="text-xs text-slate-400 font-medium">Dataset Total Reviews</div>
                <div className="text-2xl sm:text-3xl font-extrabold text-white">
                  {summary ? summary.total_reviews : "201"}
                </div>
                <p className="text-[11px] text-slate-500">Processed CSV foundation records</p>
              </div>

              <div className="glass-card rounded-xl p-4 sm:p-5 border border-white/5 space-y-1">
                <div className="text-xs text-slate-400 font-medium">Positive Satisfaction</div>
                <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
                  {summary ? `${summary.positive_percentage}%` : "76.1%"}
                </div>
                <p className="text-[11px] text-slate-500">
                  {summary ? `${summary.positive_count} reviews with compound ≥ 0.05` : "Dominant positive valence"}
                </p>
              </div>

              <div className="glass-card rounded-xl p-4 sm:p-5 border border-white/5 space-y-1">
                <div className="text-xs text-slate-400 font-medium">Average Compound Score</div>
                <div className="text-2xl sm:text-3xl font-extrabold text-sky-400 font-mono">
                  {summary ? `+${summary.average_compound_score}` : "+0.642"}
                </div>
                <p className="text-[11px] text-slate-500">Range: -1.0 (Extreme Neg) to +1.0</p>
              </div>

              <div className="glass-card rounded-xl p-4 sm:p-5 border border-white/5 space-y-1">
                <div className="text-xs text-slate-400 font-medium">SQLite Saved Reviews</div>
                <div className="text-2xl sm:text-3xl font-extrabold text-indigo-400">
                  {historyStats ? historyStats.total_reviews : 0}
                </div>
                <p className="text-[11px] text-slate-500">Persisted real user & URL queries</p>
              </div>
            </section>

            {/* Overall Sentiment Distribution Meter */}
            <section className="glass-card rounded-2xl p-5 sm:p-6 border border-white/10 space-y-3" aria-label="Sentiment distribution summary">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-sky-400" aria-hidden="true" />
                  Dataset Sentiment Valence Distribution
                </h3>
                <span className="text-xs text-slate-400">
                  Total Evaluated: <strong>{summary?.total_reviews || 201}</strong>
                </span>
              </div>

              {/* Accessible Fluid Progress Bar */}
              <div
                className="h-3 w-full rounded-full bg-slate-800 overflow-hidden flex"
                role="img"
                aria-label={`Sentiment breakdown: ${summary?.positive_percentage || 76.1}% Positive, ${summary?.neutral_percentage || 9.5}% Neutral, ${summary?.negative_percentage || 14.4}% Negative`}
              >
                <div
                  style={{ width: `${summary?.positive_percentage || 76.12}%` }}
                  className="bg-emerald-500 transition-all duration-500"
                  title={`Positive: ${summary?.positive_percentage || 76.12}%`}
                />
                <div
                  style={{ width: `${summary?.neutral_percentage || 9.45}%` }}
                  className="bg-amber-400 transition-all duration-500"
                  title={`Neutral: ${summary?.neutral_percentage || 9.45}%`}
                />
                <div
                  style={{ width: `${summary?.negative_percentage || 14.43}%` }}
                  className="bg-rose-500 transition-all duration-500"
                  title={`Negative: ${summary?.negative_percentage || 14.43}%`}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-slate-300 pt-1">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" aria-hidden="true" />
                  Positive: <strong>{summary ? `${summary.positive_percentage}%` : "76.1%"}</strong>
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shrink-0" aria-hidden="true" />
                  Neutral: <strong>{summary ? `${summary.neutral_percentage}%` : "9.5%"}</strong>
                </span>
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0" aria-hidden="true" />
                  Negative: <strong>{summary ? `${summary.negative_percentage}%` : "14.4%"}</strong>
                </span>
              </div>
            </section>

            {/* Quick Action Navigation Cards */}
            <section className="grid grid-cols-1 md:grid-cols-2 gap-4" aria-label="Feature shortcuts">
              <div
                onClick={() => setActiveTab("url")}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setActiveTab("url"); }}
                className="glass-card glass-card-hover rounded-2xl p-5 border border-white/5 cursor-pointer transition-all"
              >
                <div className="flex items-start gap-3.5">
                  <div className="p-3 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20 shrink-0">
                    <Globe className="w-6 h-6" aria-hidden="true" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm sm:text-base font-bold text-white">Amazon & Public URL Review Extraction</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Extract real reviews from Amazon India product pages, compute live VADER valence, and automatically persist results into SQLite.
                    </p>
                  </div>
                </div>
              </div>

              <div
                onClick={() => setActiveTab("text")}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setActiveTab("text"); }}
                className="glass-card glass-card-hover rounded-2xl p-5 border border-white/5 cursor-pointer transition-all"
              >
                <div className="flex items-start gap-3.5">
                  <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
                    <Zap className="w-6 h-6" aria-hidden="true" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm sm:text-base font-bold text-white">Interactive Text Sentiment Arena</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">
                      Type or paste customer feedback to evaluate 5-tier intensity, compound score, and valence proportions in real time.
                    </p>
                  </div>
                </div>
              </div>
            </section>
          </div>
        )}

        {/* ================================================================== */}
        {/* TAB 2: LIVE TEXT ANALYZER                                          */}
        {/* ================================================================== */}
        {activeTab === "text" && (
          <div className="space-y-6 max-w-4xl mx-auto">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-white">Live Text Sentiment Analyzer</h2>
              <p className="text-xs sm:text-sm text-slate-400 mt-1">
                Scores review texts with the rule-based VADER algorithm and automatically stores real reviews in SQLite.
              </p>
            </div>

            <form onSubmit={handleAnalyzeText} className="glass-card rounded-2xl p-4 sm:p-6 border border-white/10 space-y-4">
              <div>
                <div className="flex flex-wrap items-center justify-between mb-2 text-xs gap-2">
                  <label htmlFor="review-text-input" className="font-semibold text-slate-200">
                    Customer Review Text
                  </label>
                  <span className="text-slate-500 font-mono">{textInput.length} / 5000 characters</span>
                </div>
                <textarea
                  id="review-text-input"
                  rows={4}
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Paste or write customer feedback here (e.g. Outstanding build quality, crystal clear display, totally worth every penny!)..."
                  maxLength={5000}
                  className="w-full rounded-xl bg-surface-secondary border border-white/10 px-4 py-3 text-base sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-primary transition-colors"
                />
              </div>

              {/* Sample Quick Fill Buttons */}
              <div className="space-y-1.5">
                <span className="text-xs text-slate-400 font-medium">Quick Test Presets:</span>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() =>
                      setTextInput(
                        "Outstanding quality! The build is solid, battery lasts 2 full days, and customer support was exceptional."
                      )
                    }
                    className="min-h-[36px] px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors"
                  >
                    Positive Sample
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setTextInput(
                        "The product works as advertised, but delivery was delayed and packaging was slightly crumpled."
                      )
                    }
                    className="min-h-[36px] px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-colors"
                  >
                    Mixed / Neutral Sample
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setTextInput(
                        "Defective unit out of the box. Stopped charging after two days. Terribly disappointed with this purchase."
                      )
                    }
                    className="min-h-[36px] px-3 py-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 transition-colors"
                  >
                    Negative Sample
                  </button>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-3 border-t border-white/5">
                <button
                  type="button"
                  onClick={() => {
                    setTextInput("");
                    setTextResult(null);
                    setTextError(null);
                  }}
                  className="min-h-[44px] px-4 py-2 rounded-xl text-xs sm:text-sm text-slate-400 hover:text-slate-200 transition-colors border border-transparent hover:border-white/10"
                >
                  Clear Text
                </button>
                <button
                  type="submit"
                  disabled={isAnalyzingText || !textInput.trim()}
                  className="min-h-[44px] px-6 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-hover text-slate-950 font-bold text-xs sm:text-sm shadow-lg shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                >
                  {isAnalyzingText ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" /> Analyzing Text...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" aria-hidden="true" /> Analyze Sentiment
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Error Message */}
            {textError && (
              <div
                className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs sm:text-sm flex items-center gap-2.5"
                role="alert"
                aria-live="assertive"
              >
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" aria-hidden="true" />
                <span>{textError}</span>
              </div>
            )}

            {/* Analysis Result Card */}
            {textResult && (
              <section
                className="glass-card rounded-2xl p-5 sm:p-6 border border-white/10 space-y-4"
                aria-label="Text analysis result"
                aria-live="polite"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/10">
                  <div className="flex flex-wrap items-center gap-2">
                    {getSentimentBadge(textResult.sentiment_label, textResult.sentiment_strength)}
                    <span className="text-xs text-emerald-400 flex items-center gap-1 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                      Saved to SQLite (ID #{textResult.saved_id || "Live"})
                    </span>
                  </div>
                  <div className="text-left sm:text-right">
                    <span className="text-xs text-slate-400">Compound Valence: </span>
                    <span
                      className={`text-lg font-mono font-bold ${
                        textResult.scores.compound >= 0.05
                          ? "text-emerald-400"
                          : textResult.scores.compound <= -0.05
                          ? "text-rose-400"
                          : "text-amber-400"
                      }`}
                    >
                      {textResult.scores.compound > 0 ? `+${textResult.scores.compound}` : textResult.scores.compound}
                    </span>
                  </div>
                </div>

                <blockquote className="text-xs sm:text-sm text-slate-200 italic leading-relaxed border-l-2 border-brand-primary/40 pl-3">
                  &ldquo;{textResult.text}&rdquo;
                </blockquote>

                {/* Score Breakdown Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                  <div className="p-3.5 rounded-xl bg-surface-secondary border border-white/5 text-center">
                    <div className="text-[11px] text-slate-400 font-medium">Positive Proportion</div>
                    <div className="text-lg font-bold text-emerald-400 mt-0.5">
                      {Math.round(textResult.scores.pos * 100)}%
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-surface-secondary border border-white/5 text-center">
                    <div className="text-[11px] text-slate-400 font-medium">Neutral Proportion</div>
                    <div className="text-lg font-bold text-amber-400 mt-0.5">
                      {Math.round(textResult.scores.neu * 100)}%
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-surface-secondary border border-white/5 text-center">
                    <div className="text-[11px] text-slate-400 font-medium">Negative Proportion</div>
                    <div className="text-lg font-bold text-rose-400 mt-0.5">
                      {Math.round(textResult.scores.neg * 100)}%
                    </div>
                  </div>
                </div>
              </section>
            )}
          </div>
        )}

        {/* ================================================================== */}
        {/* TAB 3: GLOBAL URL INTELLIGENCE & REVIEW ANALYZER                   */}
        {/* ================================================================== */}
        {activeTab === "url" && (
          <div className="space-y-6 max-w-5xl mx-auto">
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20 mb-2">
                <Globe className="w-3.5 h-3.5 shrink-0" aria-hidden="true" /> Global URL Intelligence Engine
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-white">Universal Web Review & Content Extractor</h2>
              <p className="text-xs sm:text-sm text-slate-400 mt-1">
                Analyze reviews, feedback, and sentiment from public e-commerce pages. Automatically scores sentiment and persists real data to SQLite.
              </p>
            </div>

            <form onSubmit={handleAnalyzeUrl} className="glass-card rounded-2xl p-4 sm:p-6 border border-white/10 space-y-4">
              <div>
                <label htmlFor="target-url-input" className="block text-xs font-semibold text-slate-200 mb-2">
                  Target Product or Webpage URL (HTTP/HTTPS)
                </label>
                <div className="relative">
                  <input
                    id="target-url-input"
                    type="url"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://www.amazon.in/dp/B0CG29HWSS"
                    required
                    className="w-full rounded-xl bg-surface-secondary border border-white/10 px-4 py-3 pl-10 text-base sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-primary transition-colors min-h-[44px]"
                  />
                  <Globe className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5 pointer-events-none" aria-hidden="true" />
                </div>
              </div>

              {/* URL Presets */}
              <div className="space-y-1.5">
                <span className="text-xs text-slate-400 font-medium">Quick-Fill Presets:</span>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => setUrlInput("https://www.amazon.in/dp/B0CG29HWSS")}
                    className="min-h-[36px] px-2.5 py-1 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20 hover:bg-sky-500/20 transition-colors"
                  >
                    Amazon India (Gorilla Glass)
                  </button>
                  <button
                    type="button"
                    onClick={() => setUrlInput("https://www.amazon.in/Durex-Condoms-Air-10-Count/dp/B078GG3KVC/")}
                    className="min-h-[36px] px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors"
                  >
                    Amazon India (Durex Condoms)
                  </button>
                  <button
                    type="button"
                    onClick={() => setUrlInput("https://python.org")}
                    className="min-h-[36px] px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors"
                  >
                    Python.org (Editorial Webpage)
                  </button>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-3 border-t border-white/5">
                <div className="flex items-center gap-2 text-xs">
                  <label htmlFor="url-max-select" className="text-slate-400 font-medium shrink-0">
                    Max Reviews:
                  </label>
                  <select
                    id="url-max-select"
                    value={urlMaxReviews}
                    onChange={(e) => setUrlMaxReviews(Number(e.target.value))}
                    className="rounded-lg bg-surface-secondary border border-white/10 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-primary min-h-[40px]"
                  >
                    <option value={5}>5 Reviews</option>
                    <option value={10}>10 Reviews</option>
                    <option value={20}>20 Reviews</option>
                    <option value={30}>30 Reviews</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={isAnalyzingUrl || !urlInput.trim()}
                  className="min-h-[44px] px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold text-xs sm:text-sm shadow-lg shadow-sky-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                >
                  {isAnalyzingUrl ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" /> Fetching & Scoring...
                    </>
                  ) : (
                    <>
                      <Globe className="w-4 h-4" aria-hidden="true" /> Extract & Analyze
                    </>
                  )}
                </button>
              </div>
            </form>

            {urlError && (
              <div
                className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs sm:text-sm flex items-center gap-2.5"
                role="alert"
                aria-live="assertive"
              >
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" aria-hidden="true" />
                <span>{urlError}</span>
              </div>
            )}

            {/* Auth Wall Notice Card (when an individual login-gated review permalink is provided) */}
            {urlResult && urlResult.status === "auth_required" ? (
              <section
                className="glass-card rounded-2xl p-5 sm:p-7 border border-amber-500/40 bg-gradient-to-br from-amber-950/40 via-surface to-surface-secondary space-y-4"
                aria-label="Authentication required notice"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-semibold px-3 py-1 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" aria-hidden="true" />
                    Amazon Account Login Wall Intercepted
                  </span>
                  {urlResult.hostname && (
                    <span className="text-xs font-mono text-slate-400">
                      {urlResult.hostname}
                    </span>
                  )}
                </div>

                <div>
                  <h3 className="text-base sm:text-lg font-bold text-white leading-tight">
                    {urlResult.page_title || "Amazon Sign-In Required"}
                  </h3>
                  <p className="text-xs sm:text-sm text-amber-200/90 mt-2 leading-relaxed">
                    {urlResult.message}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-surface-secondary/90 border border-white/10 space-y-2.5">
                  <div className="text-xs font-bold text-sky-400 flex items-center gap-1.5">
                    <Globe className="w-4 h-4 shrink-0" aria-hidden="true" /> How to Analyze This Product:
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    Amazon restricts individual review permalinks behind user account login. To crawl and score all reviews for this product publicly, use the main product detail URL:
                  </p>
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <code className="text-xs font-mono bg-black/60 text-emerald-300 px-3 py-1.5 rounded-lg border border-emerald-500/30">
                      https://www.amazon.in/dp/&lt;ASIN&gt;
                    </code>
                    <button
                      type="button"
                      onClick={() => setUrlInput("https://www.amazon.in/dp/B0CG29HWSS")}
                      className="min-h-[36px] px-3 py-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/20 text-xs font-medium transition-colors"
                    >
                      Load Sample Product Page
                    </button>
                  </div>
                </div>
              </section>
            ) : urlResult && (
              <section className="space-y-5" aria-label="Extracted URL reviews">
                <div className="glass-card rounded-2xl p-5 sm:p-6 border border-sky-500/30 bg-gradient-to-br from-sky-950/30 via-surface to-surface-secondary space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
                      {urlResult.saved_to_db ? "Extracted & Saved to SQLite" : "Preview Mode"}
                    </span>
                    <span className="text-xs text-sky-400 font-mono font-semibold">
                      {urlResult.total} Reviews Extracted
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-white leading-tight">
                      {urlResult.page_title || "Extracted Reviews"}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono wrap-anywhere mt-2">
                      <ExternalLink className="w-3.5 h-3.5 shrink-0 text-slate-500" aria-hidden="true" />
                      <a
                        href={urlResult.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-sky-400 underline decoration-white/20"
                      >
                        {urlResult.source_url}
                      </a>
                    </div>
                  </div>

                  {urlResult.average_compound_score !== undefined && (
                    <div className="pt-3 border-t border-white/10 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-300 font-semibold">Webpage Sentiment Profile:</span>
                        <span className="font-mono font-bold text-xs text-sky-400">
                          Avg: {urlResult.average_compound_score}
                        </span>
                      </div>
                      <div className="h-2.5 w-full rounded-full bg-slate-800 overflow-hidden flex">
                        <div
                          style={{ width: `${urlResult.positive_percentage || 0}%` }}
                          className="bg-emerald-500"
                          title={`Positive: ${urlResult.positive_percentage}%`}
                        />
                        <div
                          style={{ width: `${urlResult.neutral_percentage || 0}%` }}
                          className="bg-amber-400"
                          title={`Neutral: ${urlResult.neutral_percentage}%`}
                        />
                        <div
                          style={{ width: `${urlResult.negative_percentage || 0}%` }}
                          className="bg-rose-500"
                          title={`Negative: ${urlResult.negative_percentage}%`}
                        />
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-1 text-[11px] text-slate-400">
                        <span>🟢 Positive: {urlResult.positive_percentage}%</span>
                        <span>🟡 Neutral: {urlResult.neutral_percentage}%</span>
                        <span>🔴 Negative: {urlResult.negative_percentage}%</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Individual Review Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {urlResult.reviews.map((r, i) => (
                    <div
                      key={i}
                      className="glass-card rounded-xl p-4 sm:p-5 border border-white/5 space-y-3 flex flex-col justify-between"
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            {getSentimentBadge(r.sentiment_label, r.sentiment_strength)}
                            {r.rating && (
                              <span className="flex items-center gap-0.5 text-xs text-amber-400 font-semibold">
                                <Star className="w-3 h-3 fill-amber-400" aria-hidden="true" />
                                {r.rating}
                              </span>
                            )}
                          </div>
                          <span
                            className={`text-xs font-mono font-bold ${
                              r.scores.compound >= 0.05
                                ? "text-emerald-400"
                                : r.scores.compound <= -0.05
                                ? "text-rose-400"
                                : "text-amber-400"
                            }`}
                          >
                            {r.scores.compound > 0 ? `+${r.scores.compound}` : r.scores.compound}
                          </span>
                        </div>
                        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed wrap-anywhere">
                          {cleanReviewDisplay(r.text)}
                        </p>
                      </div>
                      <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-500">
                        <span>{r.author || `Reviewer #${i + 1}`}</span>
                        <span>VADER Scored · SQLite Saved</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}

        {/* ================================================================== */}
        {/* TAB 4: SAVED HISTORY (SQLITE & CLIENT PERSISTENCE)                  */}
        {/* ================================================================== */}
        {activeTab === "history" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-2">
                  <Database className="w-3.5 h-3.5 shrink-0" aria-hidden="true" /> SQLite & Client Storage
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-white">Saved Real Reviews Explorer</h2>
                <p className="text-xs sm:text-sm text-slate-400 mt-1">
                  Persists authentic user-analyzed feedback and live URL extractions. Zero synthetic dummy records.
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={loadHistoryData}
                  className="min-h-[40px] px-3.5 py-2 rounded-xl bg-surface-secondary hover:bg-surface-tertiary text-slate-300 text-xs border border-white/5 transition-colors flex items-center gap-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingHistory ? "animate-spin" : ""}`} aria-hidden="true" />
                  Refresh
                </button>
                <button
                  type="button"
                  onClick={handleClearAllSavedReviews}
                  disabled={historyTotal === 0}
                  className="min-h-[40px] px-3.5 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs border border-rose-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                >
                  <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                  Clear All
                </button>
              </div>
            </div>

            {/* History Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              <div className="glass-card rounded-xl p-4 border border-white/5">
                <div className="text-xs text-slate-400 font-medium">Total Saved Reviews</div>
                <div className="text-2xl sm:text-3xl font-extrabold text-white mt-1">
                  {historyStats ? historyStats.total_reviews : 0}
                </div>
              </div>
              <div className="glass-card rounded-xl p-4 border border-white/5">
                <div className="text-xs text-slate-400 font-medium">Text Input Analyses</div>
                <div className="text-2xl sm:text-3xl font-extrabold text-sky-400 mt-1">
                  {historyStats ? historyStats.text_count : 0}
                </div>
              </div>
              <div className="glass-card rounded-xl p-4 border border-white/5">
                <div className="text-xs text-slate-400 font-medium">Live URL Extractions</div>
                <div className="text-2xl sm:text-3xl font-extrabold text-indigo-400 mt-1">
                  {historyStats ? historyStats.url_count : 0}
                </div>
              </div>
              <div className="glass-card rounded-xl p-4 border border-white/5">
                <div className="text-xs text-slate-400 font-medium">Avg Saved Valence</div>
                <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 mt-1 font-mono">
                  {historyStats ? historyStats.average_compound_score : "0.00"}
                </div>
              </div>
            </div>

            {/* Filter & Search Bar (Responsive Grid) */}
            <div className="glass-card rounded-xl p-4 border border-white/5 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              <div className="space-y-1">
                <label htmlFor="history-source-filter" className="text-xs text-slate-400 font-medium">
                  Source:
                </label>
                <select
                  id="history-source-filter"
                  value={historySourceFilter}
                  onChange={(e) => {
                    setHistorySourceFilter(e.target.value);
                    setHistoryPage(1);
                  }}
                  className="w-full rounded-lg bg-surface-secondary border border-white/10 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-primary min-h-[40px]"
                >
                  <option value="all">All Sources</option>
                  <option value="text">Text Analyses</option>
                  <option value="url">URL Extractions</option>
                </select>
              </div>

              <div className="space-y-1">
                <label htmlFor="history-sentiment-filter" className="text-xs text-slate-400 font-medium">
                  Sentiment:
                </label>
                <select
                  id="history-sentiment-filter"
                  value={historySentimentFilter}
                  onChange={(e) => {
                    setHistorySentimentFilter(e.target.value);
                    setHistoryPage(1);
                  }}
                  className="w-full rounded-lg bg-surface-secondary border border-white/10 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-primary min-h-[40px]"
                >
                  <option value="all">All Sentiments</option>
                  <option value="Positive">Positive</option>
                  <option value="Neutral">Neutral</option>
                  <option value="Negative">Negative</option>
                </select>
              </div>

              <div className="sm:col-span-2 space-y-1">
                <label htmlFor="history-search-input" className="text-xs text-slate-400 font-medium">
                  Search Keywords:
                </label>
                <div className="relative">
                  <input
                    id="history-search-input"
                    type="text"
                    value={historySearch}
                    onChange={(e) => {
                      setHistorySearch(e.target.value);
                      setHistoryPage(1);
                    }}
                    placeholder="Search by review text or product name..."
                    className="w-full rounded-lg bg-surface-secondary border border-white/10 pl-8 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-primary min-h-[40px]"
                  />
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-3" aria-hidden="true" />
                </div>
              </div>
            </div>

            {/* Mobile Card Stream (< 768px) - 100% Media Responsive, Zero Horizontal Clipping */}
            <div className="md:hidden space-y-3" aria-label="Saved reviews mobile card view">
              {historyItems.length === 0 ? (
                <div className="glass-card rounded-xl p-8 text-center text-slate-500 border border-white/5">
                  {loadingHistory ? "Loading saved history from SQLite..." : "No matching reviews found in database."}
                </div>
              ) : (
                historyItems.map((item) => {
                  const cleanedText = cleanReviewDisplay(item.review_text);
                  const isPositive = (item.compound_score || 0) >= 0.05;
                  const isNegative = (item.compound_score || 0) <= -0.05;

                  return (
                    <div
                      key={item.id}
                      className="glass-card rounded-xl p-4 border border-white/10 space-y-3"
                    >
                      {/* Top Row: Source, Sentiment Badge, Compound Score & Delete Button */}
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                              item.source_type === "url"
                                ? "bg-indigo-500/15 text-indigo-300 border border-indigo-500/30"
                                : "bg-sky-500/15 text-sky-300 border border-sky-500/30"
                            }`}
                          >
                            {item.source_type}
                          </span>
                          {getSentimentBadge(item.sentiment_label, item.sentiment_strength)}
                        </div>

                        <div className="flex items-center gap-2">
                          <span
                            className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                              isPositive
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : isNegative
                                ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            }`}
                          >
                            {item.compound_score !== undefined
                              ? item.compound_score > 0
                                ? `+${item.compound_score}`
                                : item.compound_score
                              : "N/A"}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleDeleteSavedReview(item.id)}
                            className="min-h-[40px] min-w-[40px] p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors flex items-center justify-center"
                            title="Delete review from SQLite"
                            aria-label={`Delete review #${item.id}`}
                          >
                            <Trash2 className="w-4 h-4" aria-hidden="true" />
                          </button>
                        </div>
                      </div>

                      {/* Product or Page Context */}
                      <div className="text-xs text-sky-300 font-medium flex items-center gap-1.5 wrap-anywhere">
                        <Tag className="w-3.5 h-3.5 shrink-0 text-slate-400" aria-hidden="true" />
                        <span className="font-semibold">{item.product_name || item.page_title || "General Analysis"}</span>
                      </div>

                      {/* Cleaned Review Content */}
                      <div className="text-xs text-slate-200 leading-relaxed wrap-anywhere bg-surface-secondary/50 p-3 rounded-lg border border-white/5">
                        {cleanedText}
                      </div>

                      {/* Card Footer: Timestamp & DB ID */}
                      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-500" aria-hidden="true" />
                          {item.created_at ? new Date(item.created_at).toLocaleDateString() : "Saved"}
                        </span>
                        <span>SQLite Record #{item.id}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Desktop Table View (>= 768px) */}
            <div className="hidden md:block glass-card rounded-2xl overflow-hidden border border-white/10">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs" aria-label="Saved review history">
                  <thead>
                    <tr className="border-b border-white/10 bg-surface-secondary/60 text-slate-400">
                      <th scope="col" className="p-3.5 font-semibold w-20">Source</th>
                      <th scope="col" className="p-3.5 font-semibold w-32">Sentiment</th>
                      <th scope="col" className="p-3.5 font-semibold min-w-[280px]">Review Content</th>
                      <th scope="col" className="p-3.5 font-semibold w-24">Compound</th>
                      <th scope="col" className="p-3.5 font-semibold w-44">Product Context</th>
                      <th scope="col" className="p-3.5 font-semibold w-16 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {historyItems.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="p-8 text-center text-slate-500">
                          {loadingHistory ? "Loading saved history from SQLite..." : "No matching reviews found in database."}
                        </td>
                      </tr>
                    ) : (
                      historyItems.map((item) => (
                        <tr key={item.id} className="hover:bg-white/5 transition-colors">
                          <td className="p-3.5 whitespace-nowrap">
                            <span
                              className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                                item.source_type === "url"
                                  ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                                  : "bg-sky-500/10 text-sky-400 border border-sky-500/20"
                              }`}
                            >
                              {item.source_type}
                            </span>
                          </td>
                          <td className="p-3.5 whitespace-nowrap">
                            {getSentimentBadge(item.sentiment_label, item.sentiment_strength)}
                          </td>
                          <td className="p-3.5 text-slate-300 wrap-anywhere max-w-md">
                            {cleanReviewDisplay(item.review_text)}
                          </td>
                          <td className="p-3.5 whitespace-nowrap font-mono font-bold">
                            <span
                              className={
                                (item.compound_score || 0) >= 0.05
                                  ? "text-emerald-400"
                                  : (item.compound_score || 0) <= -0.05
                                  ? "text-rose-400"
                                  : "text-amber-400"
                              }
                            >
                              {item.compound_score !== undefined
                                ? item.compound_score > 0
                                ? `+${item.compound_score}`
                                : item.compound_score
                                : "N/A"}
                            </span>
                          </td>
                          <td className="p-3.5 text-slate-400 text-[11px] max-w-[180px] truncate">
                            {item.product_name || item.page_title || "General"}
                          </td>
                          <td className="p-3.5 text-right whitespace-nowrap">
                            <button
                              type="button"
                              onClick={() => handleDeleteSavedReview(item.id)}
                              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                              title="Delete review from SQLite"
                              aria-label={`Delete review #${item.id}`}
                            >
                              <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Pagination Controls - Shared by both Mobile & Desktop */}
            <div className="p-3.5 glass-card rounded-xl border border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
              <span>
                Showing {historyItems.length} of {historyTotal} saved records
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={historyPage <= 1}
                  onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                  className="min-h-[38px] px-3.5 py-1.5 rounded-lg bg-surface-secondary hover:bg-surface-tertiary border border-white/5 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 transition-colors flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" aria-hidden="true" /> Previous
                </button>
                <span className="px-2 font-mono">Page {historyPage}</span>
                <button
                  type="button"
                  disabled={historyPage * 20 >= historyTotal}
                  onClick={() => setHistoryPage((p) => p + 1)}
                  className="min-h-[38px] px-3.5 py-1.5 rounded-lg bg-surface-secondary hover:bg-surface-tertiary border border-white/5 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 transition-colors flex items-center gap-1"
                >
                  Next <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================== */}
        {/* TAB 5: EXPLORE DATASET REVIEWS                                     */}
        {/* ================================================================== */}
        {activeTab === "explore" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-white">Processed Dataset Review Explorer</h2>
              <p className="text-xs sm:text-sm text-slate-400 mt-1">
                Browse, filter, and analyze the curated baseline dataset of 201 e-commerce customer reviews.
              </p>
            </div>

            {/* Filter Bar */}
            <div className="glass-card rounded-xl p-4 border border-white/5 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              <div className="space-y-1">
                <label htmlFor="explore-sentiment-select" className="text-xs text-slate-400 font-medium">
                  Filter by Sentiment:
                </label>
                <select
                  id="explore-sentiment-select"
                  value={exploreSentiment}
                  onChange={(e) => {
                    setExploreSentiment(e.target.value);
                    setExplorePage(1);
                  }}
                  className="w-full rounded-lg bg-surface-secondary border border-white/10 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-primary min-h-[40px]"
                >
                  <option value="All">All Sentiments</option>
                  <option value="Positive">Positive</option>
                  <option value="Neutral">Neutral</option>
                  <option value="Negative">Negative</option>
                </select>
              </div>

              <div className="space-y-1">
                <label htmlFor="explore-category-select" className="text-xs text-slate-400 font-medium">
                  Filter by Category:
                </label>
                <select
                  id="explore-category-select"
                  value={exploreCategory}
                  onChange={(e) => {
                    setExploreCategory(e.target.value);
                    setExplorePage(1);
                  }}
                  className="w-full rounded-lg bg-surface-secondary border border-white/10 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-primary min-h-[40px]"
                >
                  <option value="All">All Categories</option>
                  <option value="Smartphones">Smartphones</option>
                  <option value="Headphones">Headphones</option>
                  <option value="Laptops">Laptops</option>
                  <option value="Smart Home">Smart Home</option>
                  <option value="Footwear">Footwear</option>
                </select>
              </div>

              <div className="flex items-end">
                <div className="text-xs text-slate-400 p-2">
                  Matching Records: <strong className="text-white">{demoTotal}</strong>
                </div>
              </div>
            </div>

            {/* Reviews Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {demoReviews.map((item, idx) => (
                <div
                  key={idx}
                  className="glass-card rounded-xl p-4 sm:p-5 border border-white/5 flex flex-col justify-between space-y-3"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        {getSentimentBadge(item.sentiment_label, item.sentiment_strength)}
                        {item.rating && (
                          <span className="flex items-center gap-0.5 text-xs text-amber-400 font-semibold">
                            <Star className="w-3 h-3 fill-amber-400" aria-hidden="true" />
                            {item.rating}
                          </span>
                        )}
                      </div>
                      <span className="text-xs font-mono font-bold text-sky-400">
                        {item.compound_score > 0 ? `+${item.compound_score}` : item.compound_score}
                      </span>
                    </div>

                    <div className="text-[11px] font-semibold text-slate-400 truncate">
                      {item.product_name} · <span className="text-slate-500">{item.product_category}</span>
                    </div>

                    <p className="text-xs sm:text-sm text-slate-300 leading-relaxed wrap-anywhere">
                      {cleanReviewDisplay(item.review_text)}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-500">
                    <span>{item.source}</span>
                    <span>Verified Dataset Record</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination Controls */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400 pt-2">
              <span>
                Page {explorePage} of {Math.ceil(demoTotal / 12) || 1}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={explorePage <= 1}
                  onClick={() => setExplorePage((p) => Math.max(1, p - 1))}
                  className="min-h-[36px] px-3.5 py-1.5 rounded-lg bg-surface-secondary hover:bg-surface-tertiary border border-white/5 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 transition-colors flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" aria-hidden="true" /> Prev
                </button>
                <button
                  type="button"
                  disabled={explorePage * 12 >= demoTotal}
                  onClick={() => setExplorePage((p) => p + 1)}
                  className="min-h-[36px] px-3.5 py-1.5 rounded-lg bg-surface-secondary hover:bg-surface-tertiary border border-white/5 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 transition-colors flex items-center gap-1"
                >
                  Next <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================== */}
        {/* TAB 6: INSIGHTS & RANKINGS                                         */}
        {/* ================================================================== */}
        {activeTab === "insights" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-white">Aggregated Sentiment Rankings & Benchmarks</h2>
              <p className="text-xs sm:text-sm text-slate-400 mt-1">
                Comparative performance across product categories and individual products based on VADER valence.
              </p>
            </div>

            {/* Category Performance */}
            <div className="glass-card rounded-2xl p-4 sm:p-6 border border-white/10 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-sky-400 shrink-0" aria-hidden="true" /> Category-Level Sentiment Benchmarks
                </h3>
                <span className="text-xs text-slate-400">
                  {categories.length} Categories Analyzed
                </span>
              </div>

              {/* Mobile Category Cards (< 768px) - Zero Clipping, 100% Media Responsive */}
              <div className="md:hidden grid grid-cols-1 sm:grid-cols-2 gap-3" aria-label="Category benchmarks mobile view">
                {categories.map((c, i) => (
                  <div key={i} className="glass-card rounded-xl p-4 border border-white/5 space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="font-bold text-sm text-white">{c.product_category}</h4>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-surface-secondary text-slate-300 border border-white/10">
                        {c.review_count} reviews
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 rounded-lg bg-surface-secondary/60 border border-white/5">
                        <div className="text-[10px] text-slate-400 font-medium">Avg Rating</div>
                        <div className="font-semibold text-amber-400 mt-0.5">{c.average_rating} ★</div>
                      </div>
                      <div className="p-2 rounded-lg bg-surface-secondary/60 border border-white/5">
                        <div className="text-[10px] text-slate-400 font-medium">Avg Compound</div>
                        <div className="font-mono font-bold text-sky-400 mt-0.5">{c.average_compound_score}</div>
                      </div>
                      <div className="p-2 rounded-lg bg-surface-secondary/60 border border-white/5">
                        <div className="text-[10px] text-slate-400 font-medium">Positive %</div>
                        <div className="font-semibold text-emerald-400 mt-0.5">{c.positive_percentage}%</div>
                      </div>
                      <div className="p-2 rounded-lg bg-surface-secondary/60 border border-white/5">
                        <div className="text-[10px] text-slate-400 font-medium">Negative %</div>
                        <div className="font-semibold text-rose-400 mt-0.5">{c.negative_percentage}%</div>
                      </div>
                    </div>

                    {/* Mini Tri-Color Valence Meter */}
                    <div
                      className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden flex"
                      title={`${c.positive_percentage}% Positive, ${c.negative_percentage}% Negative`}
                    >
                      <div style={{ width: `${c.positive_percentage}%` }} className="bg-emerald-500" />
                      <div
                        style={{ width: `${Math.max(0, 100 - c.positive_percentage - c.negative_percentage)}%` }}
                        className="bg-amber-400"
                      />
                      <div style={{ width: `${c.negative_percentage}%` }} className="bg-rose-500" />
                    </div>
                  </div>
                ))}
              </div>

              {/* Desktop Category Table (>= 768px) */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-left text-xs" aria-label="Category performance benchmarks">
                  <thead>
                    <tr className="border-b border-white/10 text-slate-400">
                      <th scope="col" className="pb-3 font-semibold">Category</th>
                      <th scope="col" className="pb-3 font-semibold">Reviews</th>
                      <th scope="col" className="pb-3 font-semibold">Average Rating</th>
                      <th scope="col" className="pb-3 font-semibold">Avg Compound</th>
                      <th scope="col" className="pb-3 font-semibold">Positive %</th>
                      <th scope="col" className="pb-3 font-semibold">Negative %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {categories.map((c, i) => (
                      <tr key={i} className="hover:bg-white/5 transition-colors">
                        <td className="py-3 font-medium text-white whitespace-nowrap">{c.product_category}</td>
                        <td className="py-3 text-slate-300">{c.review_count}</td>
                        <td className="py-3 text-amber-400 font-semibold">{c.average_rating} ★</td>
                        <td className="py-3 font-mono text-sky-400">{c.average_compound_score}</td>
                        <td className="py-3 text-emerald-400 font-semibold">{c.positive_percentage}%</td>
                        <td className="py-3 text-rose-400 font-semibold">{c.negative_percentage}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Products Table */}
            <div className="glass-card rounded-2xl p-4 sm:p-6 border border-white/10 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                  <Tag className="w-4 h-4 text-indigo-400 shrink-0" aria-hidden="true" /> Top Product Sentiment Rankings
                </h3>
                <span className="text-xs text-slate-400">
                  Top 10 Products by Volume & Valence
                </span>
              </div>

              {/* Mobile Product Cards (< 768px) - Zero Clipping, Full Product Titles */}
              <div className="md:hidden space-y-3" aria-label="Product sentiment rankings mobile view">
                {products.slice(0, 10).map((p, i) => (
                  <div key={i} className="glass-card rounded-xl p-4 border border-white/5 space-y-2.5">
                    <div className="flex items-start gap-2.5">
                      <span className="shrink-0 w-6 h-6 rounded-full bg-sky-500/15 text-sky-300 text-xs font-bold flex items-center justify-center border border-sky-500/20">
                        #{i + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="font-bold text-xs sm:text-sm text-white leading-snug wrap-anywhere">
                          {p.product_name}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          {p.product_category}
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-1.5 text-center text-xs pt-1 border-t border-white/5">
                      <div className="p-1.5 rounded-lg bg-surface-secondary/50">
                        <div className="text-[9px] text-slate-400 font-medium">Volume</div>
                        <div className="font-semibold text-slate-200 mt-0.5">{p.review_count}</div>
                      </div>
                      <div className="p-1.5 rounded-lg bg-surface-secondary/50">
                        <div className="text-[9px] text-slate-400 font-medium">Rating</div>
                        <div className="font-semibold text-amber-400 mt-0.5">{p.average_rating} ★</div>
                      </div>
                      <div className="p-1.5 rounded-lg bg-surface-secondary/50">
                        <div className="text-[9px] text-slate-400 font-medium">Compound</div>
                        <div className="font-mono font-bold text-sky-400 mt-0.5">{p.average_compound_score}</div>
                      </div>
                      <div className="p-1.5 rounded-lg bg-surface-secondary/50">
                        <div className="text-[9px] text-slate-400 font-medium">Positive</div>
                        <div className="font-semibold text-emerald-400 mt-0.5">{p.positive_percentage}%</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Desktop Products Table (>= 768px) */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-left text-xs" aria-label="Product sentiment rankings">
                  <thead>
                    <tr className="border-b border-white/10 text-slate-400">
                      <th scope="col" className="pb-3 font-semibold min-w-[200px]">Product Name</th>
                      <th scope="col" className="pb-3 font-semibold">Category</th>
                      <th scope="col" className="pb-3 font-semibold">Volume</th>
                      <th scope="col" className="pb-3 font-semibold">Avg Rating</th>
                      <th scope="col" className="pb-3 font-semibold">Avg Compound</th>
                      <th scope="col" className="pb-3 font-semibold">Positive %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {products.slice(0, 10).map((p, i) => (
                      <tr key={i} className="hover:bg-white/5 transition-colors">
                        <td className="py-3 font-medium text-white max-w-[240px] truncate">{p.product_name}</td>
                        <td className="py-3 text-slate-400">{p.product_category}</td>
                        <td className="py-3 text-slate-300">{p.review_count}</td>
                        <td className="py-3 text-amber-400 font-semibold">{p.average_rating} ★</td>
                        <td className="py-3 font-mono text-sky-400">{p.average_compound_score}</td>
                        <td className="py-3 text-emerald-400 font-semibold">{p.positive_percentage}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ================================================================== */}
        {/* TAB 7: PIPELINE & ARCHITECTURE                                     */}
        {/* ================================================================== */}
        {activeTab === "about" && (
          <div className="space-y-6 max-w-4xl mx-auto">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-white">System Architecture & Pipeline</h2>
              <p className="text-xs sm:text-sm text-slate-400 mt-1">
                Overview of the multi-phase engineering pipeline, security parameters, and persistence model.
              </p>
            </div>

            <div className="glass-card rounded-2xl p-5 sm:p-7 border border-white/10 space-y-4">
              <h3 className="text-base font-bold text-white">Full-Stack Architecture</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-surface-secondary border border-white/5 space-y-2">
                  <div className="font-bold text-sky-400 flex items-center gap-1.5">
                    <Zap className="w-4 h-4 shrink-0" aria-hidden="true" /> 1. Next.js Frontend
                  </div>
                  <p className="text-slate-300 leading-relaxed">
                    React 18 App Router, mobile-first Tailwind CSS, responsive accessible controls, and dual SQLite/LocalStorage state.
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-surface-secondary border border-white/5 space-y-2">
                  <div className="font-bold text-indigo-400 flex items-center gap-1.5">
                    <Activity className="w-4 h-4 shrink-0" aria-hidden="true" /> 2. FastAPI Backend
                  </div>
                  <p className="text-slate-300 leading-relaxed">
                    Asynchronous REST API, SlowAPI rate limiting, Pydantic type validation, anti-SSRF protections, and rule-based VADER scoring.
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-surface-secondary border border-white/5 space-y-2">
                  <div className="font-bold text-emerald-400 flex items-center gap-1.5">
                    <Database className="w-4 h-4 shrink-0" aria-hidden="true" /> 3. Persistent SQLite
                  </div>
                  <p className="text-slate-300 leading-relaxed">
                    Zero-dependency local database (<code className="text-sky-300">data/reviewlens.db</code>) storing real user-analyzed feedback with zero synthetic contamination.
                  </p>
                </div>
              </div>
            </div>

            <div className="glass-card rounded-2xl p-5 sm:p-6 border border-white/10 space-y-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" aria-hidden="true" />
                VADER Sentiment Classification Thresholds
              </h3>
              <ul className="text-xs text-slate-300 space-y-2 leading-relaxed">
                <li>• <strong>Strong Positive</strong>: Compound score &ge; +0.50</li>
                <li>• <strong>Positive</strong>: +0.05 &le; Compound score &lt; +0.50</li>
                <li>• <strong>Neutral</strong>: -0.05 &lt; Compound score &lt; +0.05</li>
                <li>• <strong>Negative</strong>: -0.50 &lt; Compound score &le; -0.05</li>
                <li>• <strong>Strong Negative</strong>: Compound score &le; -0.50</li>
              </ul>
            </div>
          </div>
        )}
      </main>

      {/* -------------------------------------------------------------------- */}
      {/* Footer (Accessible, Responsive Multi-Column Layout)                  */}
      {/* -------------------------------------------------------------------- */}
      <footer className="border-t border-white/10 bg-surface/80 mt-12 py-8 px-4 sm:px-6 lg:px-8 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-sm">ReviewLens</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                v1.0.0
              </span>
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              E-Commerce Review Sentiment Intelligence Dashboard. Engineered with Next.js App Router, FastAPI, and VADER NLP engine.
            </p>
          </div>

          <div className="space-y-2">
            <span className="font-semibold text-white text-xs uppercase tracking-wider block">
              Responsible Data Policy
            </span>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Baseline insights derive from local curated datasets. URL extraction operates under public domain boundaries without CAPTCHA or authentication bypasses. VADER is lexicon-based and may not capture complex irony.
            </p>
          </div>

          <div className="space-y-2 md:text-right">
            <span className="font-semibold text-white text-xs uppercase tracking-wider block">
              Quick Architecture Links
            </span>
            <div className="flex flex-wrap md:justify-end gap-3 text-[11px]">
              <button
                type="button"
                onClick={() => setActiveTab("overview")}
                className="hover:text-sky-400 transition-colors"
              >
                Overview
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("url")}
                className="hover:text-sky-400 transition-colors"
              >
                URL Extractor
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("history")}
                className="hover:text-sky-400 transition-colors"
              >
                SQLite History
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("about")}
                className="hover:text-sky-400 transition-colors"
              >
                Documentation
              </button>
            </div>
            <p className="text-slate-500 text-[10px] pt-1">
              &copy; {new Date().getFullYear()} ReviewLens Portfolio. Open Source MIT.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
