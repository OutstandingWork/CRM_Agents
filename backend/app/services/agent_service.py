from __future__ import annotations

from app.core.config import get_settings
from app.agents.engine import AgentEngine
from app.core.models import (
    AgentInsight,
    AgentRequest,
    ExecuteActionRequest,
    ExecuteActionResponse,
    NoteCreate,
    TaskCreate,
)
from app.services.repository import CRMRepository


class AgentService:
    def __init__(self, repository: CRMRepository) -> None:
        self.repository = repository
        self.engine = AgentEngine(get_settings())

    def prospect(self, request: AgentRequest) -> AgentInsight:
        detail = self.repository.get_deal_detail(request.deal_id or "deal-apex-expansion")
        insight = self.engine.analyze_prospecting(detail, request)
        return self.repository.persist_agent_insight(detail.deal.id, insight)

    def deal_intelligence(self, request: AgentRequest) -> AgentInsight:
        detail = self.repository.get_deal_detail(request.deal_id or "deal-apex-expansion")
        insight = self.engine.analyze_deal_intelligence(detail, request)
        return self.repository.persist_agent_insight(detail.deal.id, insight)

    def retention(self, request: AgentRequest) -> AgentInsight:
        detail = self.repository.get_deal_detail(request.deal_id or "deal-nimbus-renewal")
        insight = self.engine.analyze_retention(detail, request)
        return self.repository.persist_agent_insight(detail.deal.id, insight)

    def competitive_intel(self, request: AgentRequest) -> AgentInsight:
        detail = self.repository.get_deal_detail(request.deal_id or "deal-apex-expansion")
        insight = self.engine.analyze_competitive_intel(detail, request)
        return self.repository.persist_agent_insight(detail.deal.id, insight)

    def execute_action(self, request: ExecuteActionRequest) -> ExecuteActionResponse:
        action = request.action
        if action.type == "create_task":
            task = self.repository.create_task(TaskCreate.model_validate(action.payload))
            return ExecuteActionResponse(status="applied", entity_id=task.id, detail=task.title)
        if action.type == "append_note":
            note = self.repository.append_note(NoteCreate.model_validate(action.payload))
            return ExecuteActionResponse(status="applied", entity_id=note.id, detail=note.content)
        if action.type == "update_deal":
            deal_id = action.payload["deal_id"]
            deal = self.repository.update_deal(
                deal_id,
                {key: value for key, value in action.payload.items() if key != "deal_id"},
            )
            return ExecuteActionResponse(status="applied", entity_id=deal.id, detail=deal.recommended_next_action)
        return ExecuteActionResponse(
            status="applied",
            entity_id=action.id,
            detail="Playbook acknowledged",
        )
