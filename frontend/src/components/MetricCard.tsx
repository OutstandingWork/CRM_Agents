import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import type { DashboardMetric } from "../lib/types";

export function MetricCard({ metric }: { metric: DashboardMetric }) {
  const Icon =
    metric.tone === "positive" ? ArrowUpRight : metric.tone === "warning" ? ArrowDownRight : Minus;

  return (
    <div className="metric-card">
      <div className="metric-meta">
        <span>{metric.label}</span>
        <Icon size={16} />
      </div>
      <strong>{metric.value}</strong>
      <p>{metric.delta}</p>
    </div>
  );
}
