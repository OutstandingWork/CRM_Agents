import { AlertTriangle, CircleDollarSign, TimerReset } from "lucide-react";

import { Badge } from "./ui";
import type { Deal } from "../lib/types";

export function DealList({
  deals,
  selectedDealId,
  onSelect,
}: {
  deals: Deal[];
  selectedDealId: string | null;
  onSelect: (dealId: string) => void;
}) {
  return (
    <section className="pane sidebar-pane">
      <div className="pane-header">
        <div>
          <h2>Deal Queue</h2>
          <p>Ranked by urgency, stage friction, and recovery upside.</p>
        </div>
        <Badge tone="warning">{deals.length} active</Badge>
      </div>

      <div className="queue-list">
        {deals.map((deal) => (
          <button
            type="button"
            key={deal.id}
            className={`deal-row ${selectedDealId === deal.id ? "selected" : ""}`}
            onClick={() => onSelect(deal.id)}
          >
            <div className="deal-row-main">
              <div>
                <strong>{deal.name}</strong>
                <p>{deal.owner}</p>
              </div>
              <Badge tone={deal.health_score < 50 ? "negative" : "positive"}>{deal.stage}</Badge>
            </div>
            <div className="deal-row-meta">
              <span>
                <CircleDollarSign size={14} /> ${Math.round(deal.amount / 1000)}k
              </span>
              <span>
                <AlertTriangle size={14} /> Health {deal.health_score}
              </span>
              <span>
                <TimerReset size={14} /> {deal.days_in_stage}d
              </span>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
