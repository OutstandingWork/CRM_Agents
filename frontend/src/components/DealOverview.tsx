import { Building2, Mail, Radar, ShieldAlert, UserRound } from "lucide-react";

import { Badge, Button } from "./ui";
import type { DealDetail } from "../lib/types";

export function DealOverview({
  detail,
  onRunHeroAgent,
  runtimeLabel,
}: {
  detail: DealDetail;
  onRunHeroAgent: () => void;
  runtimeLabel: string;
}) {
  const { company, contact, deal, signals, activities } = detail;

  return (
    <section className="pane workspace-pane">
      <div className="workspace-header">
        <div>
          <span className="section-kicker">Selected Deal</span>
          <h2>{deal.name}</h2>
          <p>{deal.recommended_next_action}</p>
        </div>
        <div className="workspace-actions">
          <Badge tone={deal.health_score < 50 ? "negative" : "positive"}>Health {deal.health_score}</Badge>
          <Badge tone="neutral">{runtimeLabel}</Badge>
          <Button onClick={onRunHeroAgent}>Run Deal Intelligence</Button>
        </div>
      </div>

      <div className="workspace-grid">
        <section className="workspace-section">
          <div className="data-row">
            <Building2 size={16} />
            <span>{company.name}</span>
            <Badge tone="neutral">{company.industry}</Badge>
          </div>
          <div className="data-row">
            <UserRound size={16} />
            <span>{contact.name}</span>
            <span className="muted-copy">{contact.title}</span>
          </div>
          <div className="data-row">
            <Mail size={16} />
            <span>{contact.email}</span>
          </div>
          <div className="data-row">
            <Radar size={16} />
            <span>
              {deal.stage} • {deal.stage_probability}% win probability • {deal.days_in_stage} days in stage
            </span>
          </div>
          <p className="support-copy">{deal.agent_summary}</p>
        </section>

        <section className="workspace-section">
          <div className="section-header-inline">
            <h3>Latest signals</h3>
            <Badge tone="warning">{signals.length} tracked</Badge>
          </div>
          <div className="signal-list">
            {signals.map((signal) => (
              <div className="signal-row" key={signal.id}>
                <div className="signal-icon">
                  <ShieldAlert size={16} />
                </div>
                <div className="signal-copy">
                  <strong>{signal.title}</strong>
                  <p>{signal.detail}</p>
                </div>
                <Badge tone={signal.severity === "high" ? "negative" : "warning"}>
                  {signal.severity}
                </Badge>
              </div>
            ))}
          </div>
        </section>

        <section className="workspace-section">
          <div className="section-header-inline">
            <h3>Recent activity</h3>
            <Badge tone="neutral">{activities.length} events</Badge>
          </div>
          <div className="timeline-list">
            {activities.map((activity) => (
              <div className="timeline-row" key={activity.id}>
                <strong>{activity.title}</strong>
                <span>{activity.owner}</span>
                <p>{activity.outcome}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}
