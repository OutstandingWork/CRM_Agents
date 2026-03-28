import { Bot, CheckCheck, LoaderCircle, Radar, Sparkles, Workflow } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "../lib/api";
import type { AgentInsight, AgentTimelineStep, AgentToolCall } from "../lib/types";
import { Badge, Button } from "./ui";

const AGENTS = [
  { id: "deal_intelligence", label: "Deal Intelligence", path: "/agents/deal-intelligence/analyze" },
  { id: "prospecting", label: "Prospecting", path: "/agents/prospect" },
  { id: "retention", label: "Retention", path: "/agents/retention/analyze" },
  { id: "competitive_intel", label: "Competitive Intel", path: "/agents/competitive-intel/analyze" },
] as const;

const FLOW_LABELS: Record<(typeof AGENTS)[number]["id"], string[]> = {
  deal_intelligence: ["CRM context loaded", "Risk signals inspected", "Narrative refined", "Actions staged"],
  prospecting: ["Account fit loaded", "Buying signals inspected", "Messaging refined", "Actions staged"],
  retention: ["Renewal context loaded", "Usage risk inspected", "Narrative refined", "Actions staged"],
  competitive_intel: ["Deal context loaded", "Competitive signals inspected", "Narrative refined", "Actions staged"],
};

const scoreLabel: Record<AgentInsight["agent_type"], string> = {
  deal_intelligence: "Risk severity",
  prospecting: "Fit score",
  retention: "Churn pressure",
  competitive_intel: "Competitive pressure",
};

function buildPendingFlow(agentId: keyof typeof FLOW_LABELS, progressIndex: number): AgentTimelineStep[] {
  return FLOW_LABELS[agentId].map((label, index) => ({
    id: `${agentId}-${index}`,
    label,
    status: index < progressIndex ? "completed" : index === progressIndex ? "active" : "pending",
    detail:
      index < progressIndex
        ? "Completed in the current run."
        : index === progressIndex
          ? "Agent is working through this phase now."
          : "Waiting for the previous phase to finish.",
    tool_call_ids: [],
  }));
}

function toolCallTone(status: AgentToolCall["status"]): "positive" | "warning" | "negative" | "neutral" {
  if (status === "completed") return "positive";
  if (status === "active") return "warning";
  return "neutral";
}

export function AgentPanel({
  dealId,
  initialInsight,
  onApplied,
}: {
  dealId: string;
  initialInsight: AgentInsight | null;
  onApplied: () => void | Promise<void>;
}) {
  const [activeAgent, setActiveAgent] = useState<string>(initialInsight?.agent_type ?? "deal_intelligence");
  const [insight, setInsight] = useState<AgentInsight | null>(initialInsight);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [progressIndex, setProgressIndex] = useState(0);

  useEffect(() => {
    setInsight(initialInsight);
    setStatus("");
    setError("");
    if (initialInsight) {
      setActiveAgent(initialInsight.agent_type);
    }
  }, [initialInsight, dealId]);

  useEffect(() => {
    if (!loading) {
      setProgressIndex(0);
      return;
    }
    const timer = window.setInterval(() => {
      setProgressIndex((current) => (current >= 3 ? current : current + 1));
    }, 900);
    return () => window.clearInterval(timer);
  }, [loading]);

  const visibleTimeline = useMemo(() => {
    if (loading && activeAgent in FLOW_LABELS) {
      return buildPendingFlow(activeAgent as keyof typeof FLOW_LABELS, progressIndex);
    }
    return insight?.timeline ?? [];
  }, [activeAgent, insight?.timeline, loading, progressIndex]);

  const visibleTools = useMemo(() => {
    if (loading) {
      return [
        {
          id: "active-fetch",
          label: "Live run in progress",
          tool: "Agent workflow",
          status: "active",
          detail: "The agent is assembling context and preparing recommendations.",
        } satisfies AgentToolCall,
      ];
    }
    return insight?.tools_used ?? [];
  }, [insight?.tools_used, loading]);

  async function runAgent(path: string, agentId: string) {
    setLoading(true);
    setActiveAgent(agentId);
    setStatus("");
    setError("");
    try {
      const next = await api.runAgent(path, dealId);
      setInsight(next);
      setActiveAgent(agentId);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Agent run failed.");
    } finally {
      setLoading(false);
    }
  }

  async function applyAction(action: AgentInsight["actions"][number]) {
    setLoading(true);
    setError("");
    try {
      const result = await api.applyAction(action);
      setStatus(`Applied to CRM: ${result.detail}`);
      await onApplied();
    } catch (applyError) {
      setError(applyError instanceof Error ? applyError.message : "Action failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="pane agent-pane">
      <div className="pane-header">
        <div>
          <h2>Agent Actions</h2>
          <p>Run specialized workflows and inspect the exact flow before writing anything back to CRM.</p>
        </div>
        {insight ? <Badge tone="neutral">Last run {new Date(insight.generated_at).toLocaleTimeString()}</Badge> : null}
      </div>

      <div className="agent-tabs">
        {AGENTS.map((agent) => (
          <button
            type="button"
            key={agent.id}
            className={`agent-tab ${activeAgent === agent.id ? "active" : ""}`}
            onClick={() => void runAgent(agent.path, agent.id)}
            disabled={loading}
          >
            {loading && activeAgent === agent.id ? <LoaderCircle size={15} className="spin" /> : null}
            {agent.label}
          </button>
        ))}
      </div>

      {error ? <div className="status-banner error">{error}</div> : null}
      {status ? <div className="status-banner success"><CheckCheck size={16} /> {status}</div> : null}

      <div className="agent-telemetry">
        <section className="agent-hero">
          <div className="agent-score-block">
            <Sparkles size={18} />
            <strong>{insight?.score ?? "--"}</strong>
            <span>{insight ? scoreLabel[insight.agent_type] : "Awaiting analysis"}</span>
          </div>
          <div className="agent-summary-copy">
            <div className="agent-summary-topline">
              <Badge tone={loading ? "warning" : "positive"}>
                {loading ? "Agent live" : "Review-first output"}
              </Badge>
              <Badge tone="neutral">{visibleTimeline.length || 4} stages</Badge>
            </div>
            <h3>{insight?.summary ?? "Select an agent to start a guided revenue workflow."}</h3>
            <p>
              {loading
                ? "The workspace now shows the live execution path so you can see what the agent is doing while it runs."
                : "Each run exposes the data fetch, signal inspection, language pass, and action planning steps behind the recommendation."}
            </p>
          </div>
        </section>

        <div className="agent-columns">
          <section className="workspace-section">
            <div className="section-header-inline">
              <h3>Execution timeline</h3>
              <Badge tone={loading ? "warning" : "neutral"}>{loading ? "Running" : "Completed"}</Badge>
            </div>
            <div className="agent-flow-list">
              {visibleTimeline.map((step, index) => (
                <div className={`agent-flow-step ${step.status}`} key={step.id}>
                  <div className="agent-flow-marker">
                    <span>{index + 1}</span>
                  </div>
                  <div className="agent-flow-copy">
                    <div className="agent-flow-title">
                      <strong>{step.label}</strong>
                      <Badge tone={step.status === "completed" ? "positive" : step.status === "active" ? "warning" : "neutral"}>
                        {step.status}
                      </Badge>
                    </div>
                    <p>{step.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="workspace-section action-section">
            <div className="section-header-inline">
              <h3>Tool calls</h3>
              <Badge tone="neutral">{visibleTools.length} tracked</Badge>
            </div>
            <div className="tool-call-list">
              {visibleTools.map((tool) => (
                <div className="tool-call-row" key={tool.id}>
                  <div className="tool-call-icon">
                    {tool.status === "active" ? <LoaderCircle size={16} className="spin" /> : <Workflow size={16} />}
                  </div>
                  <div className="tool-call-copy">
                    <div className="tool-call-title">
                      <strong>{tool.label}</strong>
                      <Badge tone={toolCallTone(tool.status)}>{tool.status}</Badge>
                    </div>
                    <span>{tool.tool}</span>
                    <p>{tool.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>

      {insight ? (
        <div className="agent-columns">
          <section className="workspace-section">
            <div className="section-header-inline">
              <h3>Why this matters</h3>
              <Badge tone="warning">{insight.rationale.length} signals</Badge>
            </div>
            <div className="bullet-list">
              {insight.rationale.map((item) => (
                <div className="bullet-row" key={item}>
                  <Radar size={14} />
                  <span>{item}</span>
                </div>
              ))}
            </div>

            <div className="section-header-inline">
              <h3>Talking points</h3>
            </div>
            <div className="badge-row">
              {insight.talking_points.map((point) => (
                <Badge key={point} tone="neutral">
                  {point}
                </Badge>
              ))}
            </div>
          </section>

          <section className="workspace-section action-section">
            <div className="section-header-inline">
              <h3>Recommended actions</h3>
              <Badge tone="positive">{insight.actions.length} ready</Badge>
            </div>
            <div className="action-list">
              {insight.actions.map((action) => (
                <div className="action-row" key={action.id}>
                  <div className="action-copy">
                    <strong>{action.label}</strong>
                    <p>{action.rationale}</p>
                  </div>
                  <Button onClick={() => void applyAction(action)} disabled={loading}>
                    <Bot size={15} />
                    Apply
                  </Button>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : (
        <div className="empty-panel">
          <Sparkles size={18} />
          <div>
            <strong>No analysis loaded</strong>
            <p>Run Deal Intelligence first to generate recovery actions for the selected record.</p>
          </div>
        </div>
      )}
    </section>
  );
}
