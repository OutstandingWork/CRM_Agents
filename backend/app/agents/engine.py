from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import Settings
from app.core.models import (
    AgentAction,
    AgentInsight,
    AgentRequest,
    AgentTimelineStep,
    AgentToolCall,
    DealDetail,
)
from app.services.llm_service import LLMService

try:
    from strands import Agent as StrandsAgent  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    StrandsAgent = None


class AgentEngine:
    def __init__(self, settings: Settings) -> None:
        self.strands_enabled = StrandsAgent is not None
        self.llm = LLMService(settings)

    def analyze_prospecting(self, detail: DealDetail, request: AgentRequest) -> AgentInsight:
        company = detail.company
        contact = detail.contact
        score = min(99, round((company.fit_score + contact.influence_score) / 2))
        summary = (
            f"{company.name} is a strong fit for expansion selling with a high-influence buyer "
            f"and clear automation pressure in {company.industry.lower()}."
        )
        actions = [
            AgentAction(
                id="prospect-task",
                type="create_task",
                label="Create multithread outreach task",
                payload={
                    "deal_id": detail.deal.id,
                    "title": f"Run persona-based outreach to {contact.name}",
                    "owner": detail.deal.owner,
                    "due_date": str((datetime.now(UTC) + timedelta(days=1)).date()),
                    "source": "agent",
                },
                rationale="High fit plus executive influence justify a fast outbound sequence.",
            ),
            AgentAction(
                id="prospect-note",
                type="append_note",
                label="Save personalized outreach draft",
                payload={
                    "entity_id": detail.deal.id,
                    "entity_type": "deal",
                    "content": (
                        f"Draft outreach: Maya, your team is scaling complex plant automation. "
                        "We can help your RevOps team tighten forecasting and remove security review delays."
                    ),
                    "author": "Prospecting Agent",
                },
                rationale="Persisting copy inside CRM lets the team review before sending.",
            ),
        ]
        insight = AgentInsight(
            agent_type="prospecting",
            summary=summary,
            score=score,
            rationale=[
                f"Company fit score is {company.fit_score}.",
                f"Primary contact influence score is {contact.influence_score}.",
                "Recent market momentum suggests budget availability.",
            ],
            talking_points=[
                "Lead with ROI from shorter procurement cycles.",
                "Use plant expansion as the urgency anchor.",
                "Offer a security-review acceleration pack in the first meeting.",
            ],
            actions=actions,
            tools_used=self._build_tool_calls(
                detail,
                llm_detail="Strengthen outbound messaging against account context.",
            ),
            timeline=self._build_timeline(
                detail,
                "prospecting",
                "Score account fit and draft multithread outreach recommendations.",
            ),
            generated_at=datetime.now(UTC),
        )
        return self.llm.enrich_insight(insight, detail)

    def analyze_deal_intelligence(self, detail: DealDetail, request: AgentRequest) -> AgentInsight:
        score = max(1, 100 - detail.deal.health_score)
        action_note = (
            "Recovery play: re-engage the economic buyer, neutralize the competitor mention, "
            "and unblock security with a tailored proof package."
        )
        actions = [
            AgentAction(
                id="deal-task",
                type="create_task",
                label="Create executive recovery task",
                payload={
                    "deal_id": detail.deal.id,
                    "title": "Schedule exec-to-exec recovery call with buyer and security lead",
                    "owner": detail.deal.owner,
                    "due_date": str((datetime.now(UTC) + timedelta(days=1)).date()),
                    "source": "agent",
                },
                rationale="A stalled negotiation with silent security stakeholders needs escalation.",
            ),
            AgentAction(
                id="deal-note",
                type="append_note",
                label="Save recovery playbook",
                payload={
                    "entity_id": detail.deal.id,
                    "entity_type": "deal",
                    "content": action_note,
                    "author": "Deal Intelligence Agent",
                },
                rationale="The playbook should remain attached to the deal timeline for the AE and manager.",
            ),
            AgentAction(
                id="deal-update",
                type="update_deal",
                label="Update recommended next action",
                payload={
                    "deal_id": detail.deal.id,
                    "recommended_next_action": "Run exec recovery call plus security proof bundle within 24 hours.",
                    "agent_summary": action_note,
                },
                rationale="Frontline guidance needs to be visible in the CRM board immediately.",
            ),
        ]
        insight = AgentInsight(
            agent_type="deal_intelligence",
            summary="Deal is slipping because engagement dropped while competitive pressure increased.",
            score=score,
            rationale=[
                f"Health score fell to {detail.deal.health_score}.",
                "Two high-severity signals hit the deal in the last three days.",
                "The champion still exists, so recovery is plausible with fast intervention.",
            ],
            talking_points=[
                "Reframe around deployment risk reduction, not just price.",
                "Acknowledge AtlasIQ directly and contrast implementation speed.",
                "Offer a shared security review checkpoint with named owners.",
            ],
            actions=actions,
            tools_used=self._build_tool_calls(
                detail,
                llm_detail="Refine recovery messaging and operator-facing rationale.",
            ),
            timeline=self._build_timeline(
                detail,
                "deal intelligence",
                "Inspect risk signals, score slip probability, and assemble recovery actions.",
            ),
            generated_at=datetime.now(UTC),
        )
        return self.llm.enrich_insight(insight, detail)

    def analyze_retention(self, detail: DealDetail, request: AgentRequest) -> AgentInsight:
        company = detail.company
        score = company.churn_risk
        content = (
            "Retention intervention: launch adoption sprint, executive sponsor reset, "
            "and service recovery narrative tied to next-quarter milestones."
        )
        actions = [
            AgentAction(
                id="retention-task",
                type="create_task",
                label="Create retention workshop task",
                payload={
                    "deal_id": detail.deal.id,
                    "title": "Run 14-day retention workshop with CS, product, and sponsor",
                    "owner": detail.deal.owner,
                    "due_date": str((datetime.now(UTC) + timedelta(days=2)).date()),
                    "source": "agent",
                },
                rationale="Cross-functional intervention is needed when usage and sentiment both dip.",
            ),
            AgentAction(
                id="retention-update",
                type="update_deal",
                label="Mark churn risk on deal",
                payload={
                    "deal_id": detail.deal.id,
                    "recommended_next_action": "Retention workshop plus sponsor realignment in 48 hours.",
                    "agent_summary": content,
                },
                rationale="The renewal should reflect a visible churn intervention plan.",
            ),
        ]
        insight = AgentInsight(
            agent_type="retention",
            summary="Usage decline and support friction indicate elevated renewal risk.",
            score=score,
            rationale=[
                f"Customer churn risk is {company.churn_risk}.",
                "An executive sponsor changed mid-cycle.",
                "Adoption decline is concentrated in two regions, which makes the plan more actionable.",
            ],
            talking_points=[
                "Open with the specific adoption recovery milestones.",
                "Offer a named executive escalation path for support issues.",
                "Tie renewal to a phased success plan rather than a broad commitment ask.",
            ],
            actions=actions,
            tools_used=self._build_tool_calls(
                detail,
                llm_detail="Tighten renewal-save narrative for the account team.",
            ),
            timeline=self._build_timeline(
                detail,
                "retention",
                "Review churn indicators and prepare a retention intervention plan.",
            ),
            generated_at=datetime.now(UTC),
        )
        return self.llm.enrich_insight(insight, detail)

    def analyze_competitive_intel(self, detail: DealDetail, request: AgentRequest) -> AgentInsight:
        company = detail.company
        score = company.competitive_pressure
        note = (
            "Competitive update: AtlasIQ is framing lower procurement friction. Counter with "
            "faster rollout proof, stronger services coverage, and quantified ramp impact."
        )
        actions = [
            AgentAction(
                id="comp-note",
                type="append_note",
                label="Save battlecard summary",
                payload={
                    "entity_id": detail.deal.id,
                    "entity_type": "deal",
                    "content": note,
                    "author": "Competitive Intel Agent",
                },
                rationale="Keep the battlecard in the active deal context instead of a separate knowledge base.",
            ),
        ]
        insight = AgentInsight(
            agent_type="competitive_intel",
            summary="Competitive pressure is material but still defensible with deal-specific positioning.",
            score=score,
            rationale=[
                f"Competitive pressure score is {company.competitive_pressure}.",
                "The competitor was mentioned by name in a recent buyer interaction.",
                "Current risk is narrative weakness, not total stakeholder loss.",
            ],
            talking_points=[
                "Differentiate on services responsiveness and operational adoption.",
                "Quantify time-to-value in the first 90 days.",
                "Use customer proof points from comparable enterprise accounts.",
            ],
            actions=actions,
            tools_used=self._build_tool_calls(
                detail,
                llm_detail="Tune battlecard framing for the live opportunity.",
            ),
            timeline=self._build_timeline(
                detail,
                "competitive intel",
                "Inspect competitor mentions and draft account-specific counter-positioning.",
            ),
            generated_at=datetime.now(UTC),
        )
        return self.llm.enrich_insight(insight, detail)

    def _build_tool_calls(self, detail: DealDetail, llm_detail: str) -> list[AgentToolCall]:
        return [
            AgentToolCall(
                id="crm_fetch",
                label="Fetch CRM context",
                tool="CRMRepository.get_deal_detail",
                status="completed",
                detail=f"Loaded deal, company, contact, notes, tasks, and signals for {detail.deal.name}.",
            ),
            AgentToolCall(
                id="signal_scan",
                label="Scan account signals",
                tool="Signal analyzer",
                status="completed",
                detail=f"Reviewed {len(detail.signals)} signals and {len(detail.activities)} activity events.",
            ),
            AgentToolCall(
                id="llm_enrichment",
                label="Refine operator summary",
                tool="LLMService.enrich_insight",
                status="completed" if self.llm.enabled else "skipped",
                detail=llm_detail if self.llm.enabled else "LLM enrichment skipped. Heuristic agent output returned.",
            ),
            AgentToolCall(
                id="action_builder",
                label="Prepare CRM-safe actions",
                tool="AgentEngine action planner",
                status="completed",
                detail="Built review-first actions without mutating CRM records.",
            ),
        ]

    def _build_timeline(
        self,
        detail: DealDetail,
        workflow_label: str,
        summary: str,
    ) -> list[AgentTimelineStep]:
        return [
            AgentTimelineStep(
                id="context",
                label="Context loaded",
                status="completed",
                detail=f"{detail.deal.name} and account context loaded from the CRM graph.",
                tool_call_ids=["crm_fetch"],
            ),
            AgentTimelineStep(
                id="inspection",
                label="Signals inspected",
                status="completed",
                detail=summary,
                tool_call_ids=["signal_scan"],
            ),
            AgentTimelineStep(
                id="language",
                label="Narrative refined",
                status="completed" if self.llm.enabled else "skipped",
                detail=(
                    f"LLM pass completed for {workflow_label} language and operator copy."
                    if self.llm.enabled
                    else "Heuristic summary used directly because LLM enrichment is unavailable."
                ),
                tool_call_ids=["llm_enrichment"],
            ),
            AgentTimelineStep(
                id="actions",
                label="Actions staged",
                status="completed",
                detail="Recommended next steps are ready for review and optional CRM write-back.",
                tool_call_ids=["action_builder"],
            ),
        ]
