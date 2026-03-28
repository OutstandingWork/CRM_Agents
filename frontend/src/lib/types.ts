export type Tone = "positive" | "warning" | "neutral";

export type DashboardMetric = {
  label: string;
  value: string;
  delta: string;
  tone: Tone;
};

export type Deal = {
  id: string;
  name: string;
  company_id: string;
  primary_contact_id: string;
  owner: string;
  stage: string;
  amount: number;
  health_score: number;
  engagement_trend: "up" | "flat" | "down";
  risk_flags: string[];
  recommended_next_action: string;
  agent_summary: string;
  last_activity_at: string;
  stage_probability: number;
  days_in_stage: number;
  urgency: "low" | "medium" | "high";
};

export type Company = {
  id: string;
  name: string;
  industry: string;
  employee_band: string;
  region: string;
  fit_score: number;
  competitive_pressure: number;
  churn_risk: number;
  summary: string;
};

export type Contact = {
  id: string;
  name: string;
  title: string;
  email: string;
  company_id: string;
  persona: string;
  influence_score: number;
};

export type Activity = {
  id: string;
  deal_id: string;
  kind: string;
  title: string;
  timestamp: string;
  owner: string;
  outcome: string;
};

export type Task = {
  id: string;
  deal_id: string;
  title: string;
  owner: string;
  due_date: string;
  status: "open" | "done";
  source: string;
};

export type Note = {
  id: string;
  entity_id: string;
  entity_type: string;
  content: string;
  created_at: string;
  author: string;
};

export type Signal = {
  id: string;
  deal_id: string;
  type: string;
  title: string;
  detail: string;
  severity: "low" | "medium" | "high";
  created_at: string;
  weight: number;
};

export type DashboardResponse = {
  metrics: DashboardMetric[];
  hero_deal_id: string;
  at_risk_deals: Deal[];
  active_signals: Signal[];
};

export type RuntimeContext = {
  app_name: string;
  crm_provider: string;
  crm_mode_label: string;
  live_crm_connected: boolean;
};

export type DealDetail = {
  deal: Deal;
  company: Company;
  contact: Contact;
  activities: Activity[];
  tasks: Task[];
  notes: Note[];
  signals: Signal[];
};

export type AgentAction = {
  id: string;
  type: "create_task" | "append_note" | "update_deal" | "send_playbook";
  label: string;
  payload: Record<string, unknown>;
  rationale: string;
};

export type AgentToolCall = {
  id: string;
  label: string;
  tool: string;
  status: "completed" | "active" | "pending" | "skipped";
  detail: string;
};

export type AgentTimelineStep = {
  id: string;
  label: string;
  status: "completed" | "active" | "pending" | "skipped";
  detail: string;
  tool_call_ids: string[];
};

export type AgentInsight = {
  agent_type: "prospecting" | "deal_intelligence" | "retention" | "competitive_intel";
  summary: string;
  score: number;
  rationale: string[];
  talking_points: string[];
  actions: AgentAction[];
  tools_used: AgentToolCall[];
  timeline: AgentTimelineStep[];
  generated_at: string;
};
