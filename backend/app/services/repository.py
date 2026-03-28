from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import UTC, datetime

from app.core.models import (
    Activity,
    AgentInsight,
    Company,
    Contact,
    DashboardMetric,
    DashboardResponse,
    Deal,
    DealDetail,
    Note,
    NoteCreate,
    Signal,
    SignalCreate,
    Task,
    TaskCreate,
)
from app.data.mock_seed import ACTIVITIES, COMPANIES, CONTACTS, DEALS, NOTES, SIGNALS, TASKS


class CRMRepository(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def live_crm_connected(self) -> bool: ...

    @property
    @abstractmethod
    def crm_mode_label(self) -> str: ...

    @abstractmethod
    def get_dashboard(self) -> DashboardResponse: ...

    @abstractmethod
    def list_deals(self) -> list[Deal]: ...

    @abstractmethod
    def get_deal_detail(self, deal_id: str) -> DealDetail: ...

    @abstractmethod
    def get_company(self, company_id: str) -> Company: ...

    @abstractmethod
    def get_contact(self, contact_id: str) -> Contact: ...

    @abstractmethod
    def create_task(self, payload: TaskCreate) -> Task: ...

    @abstractmethod
    def append_note(self, payload: NoteCreate) -> Note: ...

    @abstractmethod
    def ingest_signal(self, payload: SignalCreate) -> Signal: ...

    @abstractmethod
    def update_deal(self, deal_id: str, updates: dict) -> Deal: ...

    @abstractmethod
    def persist_agent_insight(self, deal_id: str, insight: AgentInsight) -> AgentInsight: ...


class MockCRMRepository(CRMRepository):
    def __init__(self) -> None:
        self.companies = {company.id: deepcopy(company) for company in COMPANIES}
        self.contacts = {contact.id: deepcopy(contact) for contact in CONTACTS}
        self.deals = {deal.id: deepcopy(deal) for deal in DEALS}
        self.activities = [deepcopy(activity) for activity in ACTIVITIES]
        self.tasks = [deepcopy(task) for task in TASKS]
        self.notes = [deepcopy(note) for note in NOTES]
        self.signals = [deepcopy(signal) for signal in SIGNALS]

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def live_crm_connected(self) -> bool:
        return False

    @property
    def crm_mode_label(self) -> str:
        return "Mock CRM Demo"

    def get_dashboard(self) -> DashboardResponse:
        at_risk = sorted(self.deals.values(), key=lambda deal: deal.health_score)[:3]
        metrics = [
            DashboardMetric(label="Pipeline Coverage", value="$515k", delta="+12%", tone="positive"),
            DashboardMetric(label="Deals Rescued", value="4", delta="+2 this week", tone="positive"),
            DashboardMetric(label="Cycle Time Reduction", value="18%", delta="-6 days", tone="positive"),
            DashboardMetric(label="Action Acceptance", value="79%", delta="+9%", tone="warning"),
        ]
        active_signals = sorted(self.signals, key=lambda signal: signal.created_at, reverse=True)[:5]
        return DashboardResponse(
            metrics=metrics,
            hero_deal_id="deal-apex-expansion",
            at_risk_deals=at_risk,
            active_signals=active_signals,
        )

    def list_deals(self) -> list[Deal]:
        return sorted(
            self.deals.values(),
            key=lambda deal: (deal.stage_probability, -deal.amount),
        )

    def get_deal_detail(self, deal_id: str) -> DealDetail:
        deal = self.deals[deal_id]
        company = self.companies[deal.company_id]
        contact = self.contacts[deal.primary_contact_id]
        activities = [item for item in self.activities if item.deal_id == deal_id]
        tasks = [item for item in self.tasks if item.deal_id == deal_id]
        notes = [item for item in self.notes if item.entity_id == deal_id]
        signals = [item for item in self.signals if item.deal_id == deal_id]
        return DealDetail(
            deal=deal,
            company=company,
            contact=contact,
            activities=sorted(activities, key=lambda item: item.timestamp, reverse=True),
            tasks=tasks,
            notes=sorted(notes, key=lambda item: item.created_at, reverse=True),
            signals=sorted(signals, key=lambda item: item.created_at, reverse=True),
        )

    def get_company(self, company_id: str) -> Company:
        return self.companies[company_id]

    def get_contact(self, contact_id: str) -> Contact:
        return self.contacts[contact_id]

    def create_task(self, payload: TaskCreate) -> Task:
        task = Task(
            id=f"tsk-{len(self.tasks) + 1}",
            deal_id=payload.deal_id,
            title=payload.title,
            owner=payload.owner,
            due_date=payload.due_date,
            source=payload.source,
        )
        self.tasks.append(task)
        return task

    def append_note(self, payload: NoteCreate) -> Note:
        note = Note(
            id=f"note-{len(self.notes) + 1}",
            entity_id=payload.entity_id,
            entity_type=payload.entity_type,
            content=payload.content,
            created_at=datetime.now(UTC),
            author=payload.author,
        )
        self.notes.append(note)
        return note

    def ingest_signal(self, payload: SignalCreate) -> Signal:
        signal = Signal(
            id=f"sig-{len(self.signals) + 1}",
            deal_id=payload.deal_id,
            type=payload.type,
            title=payload.title,
            detail=payload.detail,
            severity=payload.severity,
            weight=payload.weight,
            created_at=datetime.now(UTC),
        )
        self.signals.append(signal)
        self._recalculate_deal(signal.deal_id)
        return signal

    def update_deal(self, deal_id: str, updates: dict) -> Deal:
        deal = self.deals[deal_id]
        updated = deal.model_copy(update=updates)
        self.deals[deal_id] = updated
        return updated

    def persist_agent_insight(self, deal_id: str, insight: AgentInsight) -> AgentInsight:
        deal = self.deals[deal_id]
        self.deals[deal_id] = deal.model_copy(
            update={
                "agent_summary": insight.summary,
                "recommended_next_action": insight.actions[0].label if insight.actions else deal.recommended_next_action,
            }
        )
        return insight

    def _recalculate_deal(self, deal_id: str) -> None:
        detail = self.get_deal_detail(deal_id)
        delta = sum(signal.weight for signal in detail.signals)
        next_score = max(1, min(100, 70 + delta))
        trend = "down" if delta < -5 else "flat" if delta < 5 else "up"
        flags = [signal.title for signal in detail.signals[:3]]
        self.update_deal(
            deal_id,
            {
                "health_score": next_score,
                "engagement_trend": trend,
                "risk_flags": flags,
                "recommended_next_action": "Re-run agent recommendations after signal refresh.",
            },
        )
