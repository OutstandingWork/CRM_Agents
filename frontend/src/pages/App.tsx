import { AlertTriangle, DatabaseZap, RefreshCcw, Zap } from "lucide-react";
import { useEffect, useState } from "react";

import { AgentPanel } from "../components/AgentPanel";
import { DealList } from "../components/DealList";
import { DealOverview } from "../components/DealOverview";
import { MetricCard } from "../components/MetricCard";
import { Button } from "../components/ui";
import { api } from "../lib/api";
import type {
  AgentInsight,
  DashboardResponse,
  Deal,
  DealDetail,
  RuntimeContext,
} from "../lib/types";

export function App() {
  const [runtime, setRuntime] = useState<RuntimeContext | null>(null);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DealDetail | null>(null);
  const [heroInsight, setHeroInsight] = useState<AgentInsight | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState("");
  const [detailError, setDetailError] = useState("");
  const [heroAgentError, setHeroAgentError] = useState("");

  async function loadOverview(signal?: AbortSignal) {
    setDashboardLoading(true);
    setDashboardError("");
    try {
      const [runtimeResponse, dashboardResponse, dealsResponse] = await Promise.all([
        api.runtime(signal),
        api.dashboard(signal),
        api.deals(signal),
      ]);
      setRuntime(runtimeResponse);
      setDashboard(dashboardResponse);
      setDeals(dealsResponse);
      setSelectedDealId((current) => current ?? dashboardResponse.hero_deal_id);
    } catch (error) {
      if (signal?.aborted) return;
      setDashboardError(error instanceof Error ? error.message : "Failed to load dashboard.");
    } finally {
      if (!signal?.aborted) {
        setDashboardLoading(false);
      }
    }
  }

  async function loadDeal(dealId: string, signal?: AbortSignal) {
    setDetailLoading(true);
    setDetailError("");
    try {
      const dealDetail = await api.dealDetail(dealId, signal);
      setDetail(dealDetail);
      setHeroInsight(null);
      setHeroAgentError("");
    } catch (error) {
      if (signal?.aborted) return;
      setDetailError(error instanceof Error ? error.message : "Failed to load deal detail.");
    } finally {
      if (!signal?.aborted) {
        setDetailLoading(false);
      }
    }
  }

  async function refreshAll() {
    await Promise.all([
      loadOverview(),
      selectedDealId ? loadDeal(selectedDealId) : Promise.resolve(),
    ]);
  }

  async function runHeroAgent() {
    if (!selectedDealId) return;
    setHeroAgentError("");
    try {
      const insight = await api.runAgent("/agents/deal-intelligence/analyze", selectedDealId);
      setHeroInsight(insight);
    } catch (error) {
      setHeroAgentError(error instanceof Error ? error.message : "Failed to run deal intelligence.");
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    void loadOverview(controller.signal);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedDealId) return;
    const controller = new AbortController();
    void loadDeal(selectedDealId, controller.signal);
    return () => controller.abort();
  }, [selectedDealId]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <span className="section-kicker">Revenue Ops Agent Cockpit</span>
          <h1>Operate the pipeline, not the slideshow.</h1>
          <p className="support-copy">
            Review CRM context, inspect risk signals, run agent analysis, and write approved actions back into the system of record.
          </p>
        </div>
        <div className="topbar-side">
          <div className="runtime-chip">
            <DatabaseZap size={16} />
            <span>{runtime?.crm_mode_label ?? "Loading runtime"}</span>
          </div>
          <Button variant="secondary" onClick={() => void refreshAll()}>
            <RefreshCcw size={16} /> Refresh
          </Button>
        </div>
      </header>

      {dashboardError ? (
        <section className="status-banner error workspace-status">
          <AlertTriangle size={16} />
          <span>{dashboardError}</span>
        </section>
      ) : null}

      <section className="metric-strip">
        {dashboardLoading
          ? Array.from({ length: 4 }, (_, index) => <div className="metric-skeleton" key={index} />)
          : dashboard?.metrics.map((metric) => <MetricCard key={metric.label} metric={metric} />)}
      </section>

      <section className="workspace">
        <DealList deals={deals} selectedDealId={selectedDealId} onSelect={setSelectedDealId} />

        <div className="workspace-main">
          {detailError ? (
            <section className="pane">
              <div className="status-banner error">
                <AlertTriangle size={16} />
                <span>{detailError}</span>
              </div>
            </section>
          ) : null}

          {heroAgentError ? (
            <section className="pane">
              <div className="status-banner error">
                <AlertTriangle size={16} />
                <span>{heroAgentError}</span>
              </div>
            </section>
          ) : null}

          {detailLoading && !detail ? (
            <section className="pane loading-pane">Loading selected deal context...</section>
          ) : null}

          {detail ? (
            <>
              <DealOverview
                detail={detail}
                onRunHeroAgent={() => void runHeroAgent()}
                runtimeLabel={runtime?.crm_mode_label ?? "Unknown CRM"}
              />
              <AgentPanel
                dealId={detail.deal.id}
                initialInsight={heroInsight}
                onApplied={async () => {
                  await Promise.all([loadOverview(), loadDeal(detail.deal.id)]);
                }}
              />
            </>
          ) : null}
        </div>

        <aside className="pane rail-pane">
          <div className="pane-header">
            <div>
              <h2>Live Signal Rail</h2>
              <p>Cross-deal activity and freshness indicators.</p>
            </div>
            <div className="runtime-mini">
              <Zap size={14} />
              <span>{runtime?.live_crm_connected ? "Live" : "Demo"}</span>
            </div>
          </div>

          <div className="rail-block">
            <h3>Freshness</h3>
            <p className="support-copy">
              Metrics and signals are seeded but mutable. Applied actions refresh both the selected deal and dashboard summary.
            </p>
          </div>

          <div className="rail-block">
            <div className="section-header-inline">
              <h3>Latest signals</h3>
              <span className="muted-copy">{dashboard?.active_signals.length ?? 0} items</span>
            </div>
            <div className="signal-list">
              {dashboard?.active_signals.map((signal) => (
                <div className="rail-signal" key={signal.id}>
                  <strong>{signal.title}</strong>
                  <p>{signal.detail}</p>
                  <span className={`weight ${signal.weight > 0 ? "up" : "down"}`}>
                    {signal.weight > 0 ? "+" : ""}
                    {signal.weight}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}
