from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


SignalType = Literal[
    "engagement_drop",
    "stakeholder_change",
    "competitor_mention",
    "usage_decline",
    "positive_reply",
    "support_escalation",
    "market_news",
]

ActionType = Literal["create_task", "append_note", "update_deal", "send_playbook"]


class Contact(BaseModel):
    id: str
    name: str
    title: str
    email: str
    company_id: str
    persona: str
    influence_score: int = Field(ge=1, le=100)


class Company(BaseModel):
    id: str
    name: str
    industry: str
    employee_band: str
    region: str
    fit_score: int = Field(ge=1, le=100)
    competitive_pressure: int = Field(ge=1, le=100)
    churn_risk: int = Field(ge=1, le=100)
    summary: str


class Activity(BaseModel):
    id: str
    deal_id: str
    kind: Literal["call", "email", "meeting", "note", "task"]
    title: str
    timestamp: datetime
    owner: str
    outcome: str


class Task(BaseModel):
    id: str
    deal_id: str
    title: str
    owner: str
    due_date: str
    status: Literal["open", "done"] = "open"
    source: str = "human"


class Note(BaseModel):
    id: str
    entity_id: str
    entity_type: Literal["deal", "company", "contact"]
    content: str
    created_at: datetime
    author: str


class Signal(BaseModel):
    id: str
    deal_id: str
    type: SignalType
    title: str
    detail: str
    severity: Literal["low", "medium", "high"]
    created_at: datetime
    weight: int = Field(ge=-20, le=20)


class Deal(BaseModel):
    id: str
    name: str
    company_id: str
    primary_contact_id: str
    owner: str
    stage: Literal["Lead", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
    amount: int
    health_score: int = Field(ge=1, le=100)
    engagement_trend: Literal["up", "flat", "down"]
    risk_flags: list[str]
    recommended_next_action: str
    agent_summary: str
    last_activity_at: datetime
    stage_probability: int = Field(ge=1, le=100)
    days_in_stage: int
    urgency: Literal["low", "medium", "high"]


class DashboardMetric(BaseModel):
    label: str
    value: str
    delta: str
    tone: Literal["positive", "warning", "neutral"]


class DealDetail(BaseModel):
    deal: Deal
    company: Company
    contact: Contact
    activities: list[Activity]
    tasks: list[Task]
    notes: list[Note]
    signals: list[Signal]


class DashboardResponse(BaseModel):
    metrics: list[DashboardMetric]
    hero_deal_id: str
    at_risk_deals: list[Deal]
    active_signals: list[Signal]


class RuntimeContext(BaseModel):
    app_name: str
    crm_provider: Literal["mock", "espo", "espocrm"] | str
    crm_mode_label: str
    live_crm_connected: bool


class AgentAction(BaseModel):
    id: str
    type: ActionType
    label: str
    payload: dict[str, Any]
    rationale: str


class AgentToolCall(BaseModel):
    id: str
    label: str
    tool: str
    status: Literal["completed", "active", "pending", "skipped"]
    detail: str


class AgentTimelineStep(BaseModel):
    id: str
    label: str
    status: Literal["completed", "active", "pending", "skipped"]
    detail: str
    tool_call_ids: list[str] = Field(default_factory=list)


class AgentInsight(BaseModel):
    agent_type: Literal["prospecting", "deal_intelligence", "retention", "competitive_intel"]
    summary: str
    score: int = Field(ge=1, le=100)
    rationale: list[str]
    talking_points: list[str]
    actions: list[AgentAction]
    tools_used: list[AgentToolCall] = Field(default_factory=list)
    timeline: list[AgentTimelineStep] = Field(default_factory=list)
    generated_at: datetime


class TaskCreate(BaseModel):
    deal_id: str
    title: str
    owner: str
    due_date: str
    source: str = "agent"


class NoteCreate(BaseModel):
    entity_id: str
    entity_type: Literal["deal", "company", "contact"] = "deal"
    content: str
    author: str = "AI Revenue Copilot"


class SignalCreate(BaseModel):
    deal_id: str
    type: SignalType
    title: str
    detail: str
    severity: Literal["low", "medium", "high"]
    weight: int = Field(ge=-20, le=20)


class AgentRequest(BaseModel):
    deal_id: str | None = None
    company_id: str | None = None
    contact_id: str | None = None
    extra_context: str | None = None


class ExecuteActionRequest(BaseModel):
    action: AgentAction


class ExecuteActionResponse(BaseModel):
    status: Literal["applied"]
    entity_id: str
    detail: str
