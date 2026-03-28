from __future__ import annotations

import base64
import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import Settings
from app.core.models import (
    Activity,
    AgentInsight,
    Company,
    Contact,
    Deal,
    DealDetail,
    Note,
    NoteCreate,
    Signal,
    SignalCreate,
    Task,
    TaskCreate,
)
from app.data.mock_seed import ACTIVITIES, COMPANIES, CONTACTS, DEALS, NOTES, TASKS
from app.services.repository import CRMRepository

META_MARKER = "[CRM_AGENT_META]"


class EspoCRMRepository(CRMRepository):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.espo_base_url.rstrip("/") + "/api/v1"
        self.auth_header = self._build_auth_header()
        self.current_user_id = self._get_current_user()["id"]
        if self.settings.espo_seed_demo_data:
            self._seed_demo_workspace()
        self._validate_workspace()

    @property
    def provider_name(self) -> str:
        return "espocrm"

    @property
    def live_crm_connected(self) -> bool:
        return True

    @property
    def crm_mode_label(self) -> str:
        return "Live EspoCRM"

    def get_dashboard(self) -> Any:
        deals = self.list_deals()
        at_risk = sorted(deals, key=lambda deal: deal.health_score)[:3]
        workspace = self._fetch_workspace()
        active_signals: list[Signal] = [
            signal
            for opportunity in workspace["opportunities"]
            if self._get_meta(opportunity.get("description"), "external_key")
            for signal in self._build_signals(opportunity, workspace["notes"])
        ]
        active_signals = sorted(active_signals, key=lambda item: item.created_at, reverse=True)[:5]
        pipeline_amount = sum(deal.amount for deal in deals)
        rescued = len([deal for deal in deals if deal.health_score >= 65])
        warning_count = len([deal for deal in deals if deal.health_score < 50])
        acceptance = min(99, 62 + len(active_signals) * 4)
        from app.core.models import DashboardMetric, DashboardResponse

        metrics = [
            DashboardMetric(label="Pipeline Coverage", value=f"${round(pipeline_amount / 1000)}k", delta=f"{len(deals)} active deals", tone="positive"),
            DashboardMetric(label="Deals Rescued", value=str(rescued), delta="Derived from latest CRM health", tone="positive"),
            DashboardMetric(label="Attention Required", value=str(warning_count), delta="Low-health opportunities", tone="warning"),
            DashboardMetric(label="Action Acceptance", value=f"{acceptance}%", delta="CRM-backed suggestions", tone="neutral"),
        ]
        hero_deal_id = at_risk[0].id if at_risk else deals[0].id
        return DashboardResponse(
            metrics=metrics,
            hero_deal_id=hero_deal_id,
            at_risk_deals=at_risk,
            active_signals=active_signals,
        )

    def list_deals(self) -> list[Deal]:
        workspace = self._fetch_workspace()
        deals = [
            self._build_deal_snapshot(opportunity, workspace)
            for opportunity in workspace["opportunities"]
            if self._get_meta(opportunity.get("description"), "external_key")
        ]
        return sorted(deals, key=lambda deal: (deal.stage_probability, -deal.amount))

    def get_deal_detail(self, deal_id: str) -> DealDetail:
        workspace = self._fetch_workspace()
        opportunity = self._find_opportunity_by_deal_id(workspace["opportunities"], deal_id)
        signals = self._sync_signal_notes(opportunity, workspace)
        workspace = self._fetch_workspace()
        opportunity = self._find_opportunity_by_deal_id(workspace["opportunities"], deal_id)
        account = self._find_account(workspace["accounts"], opportunity["accountId"])
        contact = self._find_contact_for_opportunity(workspace["contacts"], opportunity)
        activities = self._build_activities(opportunity, workspace["notes"])
        tasks = self._build_tasks(opportunity, workspace["tasks"])
        notes = self._build_notes(opportunity, workspace["notes"])
        deal = self._build_deal_snapshot(opportunity, workspace, signals=signals, activities=activities)
        company = self._build_company(account, signals)
        return DealDetail(
            deal=deal,
            company=company,
            contact=self._build_contact(contact),
            activities=activities,
            tasks=tasks,
            notes=notes,
            signals=signals,
        )

    def get_company(self, company_id: str) -> Company:
        workspace = self._fetch_workspace()
        account = self._find_account_by_company_id(workspace["accounts"], company_id)
        related_opportunity = next(
            (opportunity for opportunity in workspace["opportunities"] if opportunity.get("accountId") == account["id"]),
            None,
        )
        signals = self._build_signals(related_opportunity, workspace["notes"]) if related_opportunity else []
        return self._build_company(account, signals)

    def get_contact(self, contact_id: str) -> Contact:
        workspace = self._fetch_workspace()
        contact = self._find_contact_by_contact_id(workspace["contacts"], contact_id)
        return self._build_contact(contact)

    def create_task(self, payload: TaskCreate) -> Task:
        workspace = self._fetch_workspace()
        opportunity = self._find_opportunity_by_deal_id(workspace["opportunities"], payload.deal_id)
        description = self._compose_text(
            f"Source: {payload.source}",
            {
                "kind": "task",
                "external_key": f"generated-task:{payload.deal_id}:{self._slugify(payload.title)}:{payload.due_date}",
                "owner": payload.owner,
                "source": payload.source,
            },
        )
        remote = self._request(
            "POST",
            "/Task",
            json={
                "name": payload.title,
                "status": "Not Started",
                "description": description,
                "dateEnd": f"{payload.due_date} 00:00:00",
                "parentType": "Opportunity",
                "parentId": opportunity["id"],
                "assignedUserId": self.current_user_id,
            },
        )
        return self._task_from_remote(remote, opportunity["id"])

    def append_note(self, payload: NoteCreate) -> Note:
        parent_type, parent_id = self._resolve_parent(payload.entity_type, payload.entity_id)
        remote = self._request(
            "POST",
            "/Note",
            json={
                "post": self._compose_text(
                    payload.content,
                    {
                        "kind": "note",
                        "author": payload.author,
                        "external_key": f"generated-note:{payload.entity_id}:{datetime.now(UTC).isoformat()}",
                    },
                ),
                "parentType": parent_type,
                "parentId": parent_id,
            },
        )
        return self._note_from_remote(remote)

    def ingest_signal(self, payload: SignalCreate) -> Signal:
        workspace = self._fetch_workspace()
        opportunity = self._find_opportunity_by_deal_id(workspace["opportunities"], payload.deal_id)
        signal = Signal(
            id=payload.deal_id,
            deal_id=payload.deal_id,
            type=payload.type,
            title=payload.title,
            detail=payload.detail,
            severity=payload.severity,
            weight=payload.weight,
            created_at=datetime.now(UTC),
        )
        self._upsert_note(
            workspace["notes"],
            opportunity["id"],
            self._compose_text(
                payload.detail,
                {
                    "kind": "signal",
                    "external_key": f"signal:{payload.deal_id}:{payload.type}:{self._slugify(payload.title)}",
                    "signal_type": payload.type,
                    "title": payload.title,
                    "detail": payload.detail,
                    "severity": payload.severity,
                    "weight": payload.weight,
                    "generated_at": signal.created_at.isoformat(),
                },
            ),
        )
        self._refresh_opportunity_rollup(opportunity, workspace["notes"])
        return signal

    def update_deal(self, deal_id: str, updates: dict) -> Deal:
        workspace = self._fetch_workspace()
        opportunity = self._find_opportunity_by_deal_id(workspace["opportunities"], deal_id)
        body, meta = self._split_text_and_meta(opportunity.get("description"))
        meta.update(
            {
                "recommended_next_action": updates.get("recommended_next_action", meta.get("recommended_next_action", "")),
                "latest_agent_summary": updates.get("agent_summary", meta.get("latest_agent_summary", "")),
                "stage_entered_at": meta.get("stage_entered_at") or datetime.now(UTC).isoformat(),
            }
        )
        remote = self._request(
            "PUT",
            f"/Opportunity/{opportunity['id']}",
            json={
                "amount": updates.get("amount", int(float(opportunity.get("amount") or 0))),
                "stage": self._map_stage_to_espo(updates.get("stage", self._map_stage_from_espo(opportunity.get("stage")))),
                "description": self._compose_text(body, meta),
                "closeDate": opportunity["closeDate"],
            },
        )
        return self._build_deal_snapshot(remote, self._fetch_workspace())

    def persist_agent_insight(self, deal_id: str, insight: AgentInsight) -> AgentInsight:
        workspace = self._fetch_workspace()
        opportunity = self._find_opportunity_by_deal_id(workspace["opportunities"], deal_id)
        body, meta = self._split_text_and_meta(opportunity.get("description"))
        meta.update(
            {
                "latest_agent_type": insight.agent_type,
                "latest_agent_score": insight.score,
                "latest_agent_summary": insight.summary,
                "last_analyzed_at": insight.generated_at.isoformat(),
                "recommended_next_action": insight.actions[0].label if insight.actions else meta.get("recommended_next_action", ""),
            }
        )
        self._request(
            "PUT",
            f"/Opportunity/{opportunity['id']}",
            json={
                "amount": int(float(opportunity.get("amount") or 0)),
                "stage": opportunity.get("stage"),
                "description": self._compose_text(body, meta),
                "closeDate": opportunity["closeDate"],
            },
        )
        self._request(
            "POST",
            "/Note",
            json={
                "post": self._compose_text(
                    insight.summary,
                    {
                        "kind": "analysis",
                        "external_key": f"analysis:{deal_id}:{insight.generated_at.isoformat()}",
                        "agent_type": insight.agent_type,
                        "score": insight.score,
                        "summary": insight.summary,
                        "rationale": insight.rationale,
                        "talking_points": insight.talking_points,
                        "tools_used": [item.model_dump() for item in insight.tools_used],
                        "timeline": [item.model_dump() for item in insight.timeline],
                        "generated_at": insight.generated_at.isoformat(),
                    },
                ),
                "parentType": "Opportunity",
                "parentId": opportunity["id"],
            },
        )
        self._refresh_opportunity_rollup(opportunity, self._fetch_workspace()["notes"])
        return insight

    def _build_auth_header(self) -> dict[str, str]:
        if self.settings.espo_api_key:
            return {"X-Api-Key": self.settings.espo_api_key}
        raw = f"{self.settings.espo_username}:{self.settings.espo_password}".encode()
        encoded = base64.b64encode(raw).decode()
        return {"Espo-Authorization": encoded, "Authorization": f"Basic {encoded}"}

    def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = httpx.request(
            method,
            f"{self.base_url}{path}",
            headers=self.auth_header,
            json=json,
            params=params,
            timeout=20.0,
        )
        response.raise_for_status()
        if response.text:
            return response.json()
        return {}

    def _list(self, path: str) -> list[dict[str, Any]]:
        return self._request("GET", path, params={"maxSize": 200, "offset": 0}).get("list", [])

    def _get_current_user(self) -> dict[str, Any]:
        users = self._list("/User")
        if not users:
            raise RuntimeError("EspoCRM user lookup failed: no users available for assignment.")
        return users[0]

    def _validate_workspace(self) -> None:
        accounts = self._list("/Account")
        opportunities = self._list("/Opportunity")
        if not accounts or not opportunities:
            raise RuntimeError("EspoCRM seed validation failed: expected Accounts and Opportunities to exist.")

    def _seed_demo_workspace(self) -> None:
        accounts = self._list("/Account")
        contacts = self._list("/Contact")
        opportunities = self._list("/Opportunity")
        tasks = self._list("/Task")
        notes = self._list("/Note")

        account_ids: dict[str, str] = {}
        for company in COMPANIES:
            remote = self._find_by_external_key(accounts, company.id, "description") or next(
                (item for item in accounts if item.get("name") == company.name),
                None,
            )
            payload = {
                "name": company.name,
                "description": self._compose_text(
                    f"{company.summary}\nIndustry: {company.industry}",
                    {
                        "external_key": company.id,
                        "employee_band": company.employee_band,
                        "region": company.region,
                        "industry": company.industry,
                    },
                ),
            }
            if remote:
                self._request("PUT", f"/Account/{remote['id']}", json=payload)
                account_ids[company.id] = remote["id"]
            else:
                created = self._request("POST", "/Account", json=payload)
                accounts.append(created)
                account_ids[company.id] = created["id"]

        for contact in CONTACTS:
            remote = self._find_by_external_key(contacts, contact.id, "description") or next(
                (item for item in contacts if item.get("emailAddress") == contact.email),
                None,
            )
            first_name, last_name = self._split_name(contact.name)
            payload = {
                "firstName": first_name,
                "lastName": last_name,
                "title": contact.title,
                "emailAddress": contact.email,
                "accountId": account_ids[contact.company_id],
                "description": self._compose_text(
                    f"Persona: {contact.persona}",
                    {
                        "external_key": contact.id,
                        "persona": contact.persona,
                        "company_id": contact.company_id,
                    },
                ),
            }
            if remote:
                self._request("PUT", f"/Contact/{remote['id']}", json=payload)
            else:
                contacts.append(self._request("POST", "/Contact", json=payload))

        for deal in DEALS:
            remote = self._find_by_external_key(opportunities, deal.id, "description") or next(
                (item for item in opportunities if item.get("name") == deal.name),
                None,
            )
            payload = {
                "name": deal.name,
                "amount": deal.amount,
                "stage": self._map_stage_to_espo(deal.stage),
                "accountId": account_ids[deal.company_id],
                "closeDate": str((datetime.now(UTC) + timedelta(days=max(deal.days_in_stage, 14))).date()),
                "description": self._compose_text(
                    f"Owner: {deal.owner}\n{deal.recommended_next_action}",
                    {
                        "external_key": deal.id,
                        "primary_contact_id": deal.primary_contact_id,
                        "owner": deal.owner,
                        "urgency": deal.urgency,
                        "stage_probability_seed": deal.stage_probability,
                        "stage_entered_at": (datetime.now(UTC) - timedelta(days=deal.days_in_stage)).isoformat(),
                        "recommended_next_action": deal.recommended_next_action,
                        "latest_agent_summary": deal.agent_summary,
                        "engagement_trend_seed": deal.engagement_trend,
                    },
                ),
            }
            if remote:
                self._request("PUT", f"/Opportunity/{remote['id']}", json=payload)
            else:
                opportunities.append(self._request("POST", "/Opportunity", json=payload))

        opportunities = self._list("/Opportunity")
        for task in TASKS:
            remote = self._find_by_external_key(tasks, task.id, "description")
            opportunity = self._find_opportunity_by_deal_id(opportunities, task.deal_id)
            payload = {
                "name": task.title,
                "status": "Completed" if task.status == "done" else "Not Started",
                "description": self._compose_text(
                    f"Source: {task.source}",
                    {
                        "kind": "task",
                        "external_key": task.id,
                        "owner": task.owner,
                        "source": task.source,
                    },
                ),
                "dateEnd": f"{task.due_date} 00:00:00",
                "parentType": "Opportunity",
                "parentId": opportunity["id"],
                "assignedUserId": self.current_user_id,
            }
            if remote:
                self._request(
                    "PUT",
                    f"/Task/{remote['id']}",
                    json={
                        "name": payload["name"],
                        "status": payload["status"],
                        "description": payload["description"],
                        "dateEnd": payload["dateEnd"],
                        "assignedUserId": payload["assignedUserId"],
                    },
                )
            else:
                tasks.append(self._request("POST", "/Task", json=payload))

        notes = self._list("/Note")
        for note in NOTES:
            opportunity = self._find_opportunity_by_deal_id(opportunities, note.entity_id)
            post = self._compose_text(
                note.content,
                {
                    "kind": "note",
                    "external_key": note.id,
                    "author": note.author,
                    "observed_at": note.created_at.isoformat(),
                },
            )
            self._upsert_note(notes, opportunity["id"], post)

        for activity in ACTIVITIES:
            opportunity = self._find_opportunity_by_deal_id(opportunities, activity.deal_id)
            post = self._compose_text(
                f"{activity.title}\nOutcome: {activity.outcome}",
                {
                    "kind": "activity",
                    "external_key": activity.id,
                    "activity_kind": activity.kind,
                    "title": activity.title,
                    "owner": activity.owner,
                    "outcome": activity.outcome,
                    "observed_at": activity.timestamp.isoformat(),
                },
            )
            self._upsert_note(notes, opportunity["id"], post)

        workspace = self._fetch_workspace()
        for opportunity in workspace["opportunities"]:
            if self._get_meta(opportunity.get("description"), "external_key"):
                self._sync_signal_notes(opportunity, workspace)

    def _fetch_workspace(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "accounts": self._list("/Account"),
            "contacts": self._list("/Contact"),
            "opportunities": self._list("/Opportunity"),
            "tasks": self._list("/Task"),
            "notes": self._list("/Note"),
        }

    def _find_by_external_key(
        self,
        records: list[dict[str, Any]],
        external_key: str,
        field: str,
    ) -> dict[str, Any] | None:
        return next((item for item in records if self._get_meta(item.get(field), "external_key") == external_key), None)

    def _find_account(self, accounts: list[dict[str, Any]], account_id: str) -> dict[str, Any]:
        return next(item for item in accounts if item["id"] == account_id)

    def _find_account_by_company_id(self, accounts: list[dict[str, Any]], company_id: str) -> dict[str, Any]:
        return next(item for item in accounts if self._get_meta(item.get("description"), "external_key") == company_id)

    def _find_contact_for_opportunity(self, contacts: list[dict[str, Any]], opportunity: dict[str, Any]) -> dict[str, Any]:
        contact_key = self._get_meta(opportunity.get("description"), "primary_contact_id")
        return next(item for item in contacts if self._get_meta(item.get("description"), "external_key") == contact_key)

    def _find_contact_by_contact_id(self, contacts: list[dict[str, Any]], contact_id: str) -> dict[str, Any]:
        return next(item for item in contacts if self._get_meta(item.get("description"), "external_key") == contact_id)

    def _find_opportunity_by_deal_id(self, opportunities: list[dict[str, Any]], deal_id: str) -> dict[str, Any]:
        return next(
            item
            for item in opportunities
            if self._get_meta(item.get("description"), "external_key") == deal_id or item.get("id") == deal_id
        )

    def _resolve_parent(self, entity_type: str, entity_id: str) -> tuple[str, str]:
        workspace = self._fetch_workspace()
        if entity_type == "deal":
            opportunity = self._find_opportunity_by_deal_id(workspace["opportunities"], entity_id)
            return "Opportunity", opportunity["id"]
        if entity_type == "company":
            account = self._find_account_by_company_id(workspace["accounts"], entity_id)
            return "Account", account["id"]
        contact = self._find_contact_by_contact_id(workspace["contacts"], entity_id)
        return "Contact", contact["id"]

    def _build_company(self, account: dict[str, Any], signals: list[Signal]) -> Company:
        body, meta = self._split_text_and_meta(account.get("description"))
        fit_score = self._derive_fit_score(meta.get("industry", ""), meta.get("employee_band", ""))
        competitive_pressure = min(100, 30 + sum(abs(item.weight) for item in signals if item.type == "competitor_mention"))
        churn_risk = min(100, 20 + sum(abs(item.weight) for item in signals if item.type in {"usage_decline", "support_escalation", "stakeholder_change"}))
        return Company(
            id=meta.get("external_key", account["id"]),
            name=account["name"],
            industry=meta.get("industry", "Unknown"),
            employee_band=meta.get("employee_band", "Unknown"),
            region=meta.get("region", "Unknown"),
            fit_score=fit_score,
            competitive_pressure=max(1, competitive_pressure),
            churn_risk=max(1, churn_risk),
            summary=body.split("\n", 1)[0].strip(),
        )

    def _build_contact(self, contact: dict[str, Any]) -> Contact:
        _, meta = self._split_text_and_meta(contact.get("description"))
        title = contact.get("title") or "Unknown"
        return Contact(
            id=meta.get("external_key", contact["id"]),
            name=contact.get("name") or f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip(),
            title=title,
            email=contact.get("emailAddress", ""),
            company_id=meta.get("account_external_key", meta.get("company_id", "")),
            persona=meta.get("persona", "stakeholder"),
            influence_score=self._derive_influence_score(title),
        )

    def _build_deal_snapshot(
        self,
        opportunity: dict[str, Any],
        workspace: dict[str, list[dict[str, Any]]],
        *,
        signals: list[Signal] | None = None,
        activities: list[Activity] | None = None,
    ) -> Deal:
        body, meta = self._split_text_and_meta(opportunity.get("description"))
        if signals is None:
            signals = self._build_signals(opportunity, workspace["notes"])
        if activities is None:
            activities = self._build_activities(opportunity, workspace["notes"])
        health_score = self._compute_health_score(signals)
        trend = self._compute_engagement_trend(signals)
        risk_flags = [item.title for item in sorted(signals, key=lambda signal: abs(signal.weight), reverse=True)[:3]]
        stage_probability = self._compute_stage_probability(self._map_stage_from_espo(opportunity.get("stage")), health_score)
        last_activity = max((item.timestamp for item in activities), default=datetime.now(UTC))
        days_in_stage = max(
            1,
            (datetime.now(UTC) - self._parse_datetime(meta.get("stage_entered_at"), fallback=last_activity)).days,
        )
        latest_summary = meta.get("latest_agent_summary", body.split("\n")[-1].strip())
        return Deal(
            id=meta.get("external_key", opportunity["id"]),
            name=opportunity["name"],
            company_id=self._get_account_external_key(opportunity["accountId"], workspace["accounts"]),
            primary_contact_id=meta.get("primary_contact_id", ""),
            owner=meta.get("owner", opportunity.get("assignedUserName") or "CRM"),
            stage=self._map_stage_from_espo(opportunity.get("stage")),
            amount=int(float(opportunity.get("amount") or 0)),
            health_score=health_score,
            engagement_trend=trend,
            risk_flags=risk_flags,
            recommended_next_action=meta.get("recommended_next_action", "Review latest agent analysis in CRM."),
            agent_summary=latest_summary,
            last_activity_at=last_activity,
            stage_probability=stage_probability,
            days_in_stage=days_in_stage,
            urgency=self._compute_urgency(health_score, signals),
        )

    def _build_tasks(self, opportunity: dict[str, Any], tasks: list[dict[str, Any]]) -> list[Task]:
        items = [item for item in tasks if item.get("parentId") == opportunity["id"]]
        return sorted((self._task_from_remote(item, opportunity["id"]) for item in items), key=lambda item: item.due_date)

    def _task_from_remote(self, task: dict[str, Any], opportunity_id: str) -> Task:
        _, meta = self._split_text_and_meta(task.get("description"))
        return Task(
            id=meta.get("external_key", f"task:{task['id']}"),
            deal_id="",
            title=task["name"],
            owner=meta.get("owner", task.get("assignedUserName") or "CRM"),
            due_date=(task.get("dateEnd") or str(datetime.now(UTC).date()))[:10],
            status="done" if task.get("status") == "Completed" else "open",
            source=meta.get("source", "espocrm"),
        ).model_copy(update={"deal_id": self._get_meta_from_parent(opportunity_id)})

    def _get_meta_from_parent(self, opportunity_id: str) -> str:
        opportunity = self._request("GET", f"/Opportunity/{opportunity_id}")
        return self._get_meta(opportunity.get("description"), "external_key") or opportunity_id

    def _build_notes(self, opportunity: dict[str, Any], notes: list[dict[str, Any]]) -> list[Note]:
        items = []
        for item in notes:
            if item.get("parentId") != opportunity["id"]:
                continue
            _, meta = self._split_text_and_meta(item.get("post"))
            if meta.get("kind") != "note":
                continue
            items.append(self._note_from_remote(item))
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def _note_from_remote(self, note: dict[str, Any]) -> Note:
        body, meta = self._split_text_and_meta(note.get("post"))
        created_at = self._parse_datetime(meta.get("observed_at"), fallback=self._parse_datetime(note.get("createdAt")))
        return Note(
            id=meta.get("external_key", note["id"]),
            entity_id=meta.get("entity_id", note.get("parentId", "")),
            entity_type="deal" if note.get("parentType") == "Opportunity" else "company" if note.get("parentType") == "Account" else "contact",
            content=body.strip(),
            created_at=created_at,
            author=meta.get("author", note.get("createdByName") or "CRM"),
        )

    def _build_activities(self, opportunity: dict[str, Any], notes: list[dict[str, Any]]) -> list[Activity]:
        items: list[Activity] = []
        deal_id = self._get_meta(opportunity.get("description"), "external_key") or opportunity["id"]
        for item in notes:
            if item.get("parentId") != opportunity["id"]:
                continue
            _, meta = self._split_text_and_meta(item.get("post"))
            if meta.get("kind") != "activity":
                continue
            items.append(
                Activity(
                    id=meta.get("external_key", item["id"]),
                    deal_id=deal_id,
                    kind=meta.get("activity_kind", "note"),
                    title=meta.get("title", "Activity"),
                    timestamp=self._parse_datetime(meta.get("observed_at"), fallback=self._parse_datetime(item.get("createdAt"))),
                    owner=meta.get("owner", item.get("createdByName") or "CRM"),
                    outcome=meta.get("outcome", ""),
                )
            )
        return sorted(items, key=lambda item: item.timestamp, reverse=True)

    def _build_signals(self, opportunity: dict[str, Any], notes: list[dict[str, Any]]) -> list[Signal]:
        deal_id = self._get_meta(opportunity.get("description"), "external_key") or opportunity["id"]
        items: list[Signal] = []
        for item in notes:
            if item.get("parentId") != opportunity["id"]:
                continue
            _, meta = self._split_text_and_meta(item.get("post"))
            if meta.get("kind") != "signal":
                continue
            items.append(
                Signal(
                    id=meta.get("external_key", item["id"]),
                    deal_id=deal_id,
                    type=meta.get("signal_type", "market_news"),
                    title=meta.get("title", "Signal"),
                    detail=meta.get("detail", ""),
                    severity=meta.get("severity", "low"),
                    created_at=self._parse_datetime(meta.get("generated_at"), fallback=self._parse_datetime(item.get("createdAt"))),
                    weight=int(meta.get("weight", 0)),
                )
            )
        return sorted(items, key=lambda item: item.created_at, reverse=True)

    def _sync_signal_notes(self, opportunity: dict[str, Any], workspace: dict[str, list[dict[str, Any]]]) -> list[Signal]:
        specs = self._derive_signal_specs(opportunity, workspace)
        for spec in specs:
            self._upsert_note(
                workspace["notes"],
                opportunity["id"],
                self._compose_text(
                    spec["detail"],
                    {
                        "kind": "signal",
                        "external_key": spec["external_key"],
                        "signal_type": spec["type"],
                        "title": spec["title"],
                        "detail": spec["detail"],
                        "severity": spec["severity"],
                        "weight": spec["weight"],
                        "generated_at": datetime.now(UTC).isoformat(),
                    },
                ),
            )
        self._refresh_opportunity_rollup(opportunity, self._fetch_workspace()["notes"])
        workspace = self._fetch_workspace()
        opportunity = self._find_opportunity_by_deal_id(workspace["opportunities"], self._get_meta(opportunity.get("description"), "external_key") or opportunity["id"])
        return self._build_signals(opportunity, workspace["notes"])

    def _refresh_opportunity_rollup(self, opportunity: dict[str, Any], notes: list[dict[str, Any]]) -> None:
        signals = self._build_signals(opportunity, notes)
        body, meta = self._split_text_and_meta(opportunity.get("description"))
        meta.update(
            {
                "latest_health_score": self._compute_health_score(signals),
                "latest_engagement_trend": self._compute_engagement_trend(signals),
                "latest_risk_flags": [item.title for item in sorted(signals, key=lambda signal: abs(signal.weight), reverse=True)[:3]],
                "latest_stage_probability": self._compute_stage_probability(
                    self._map_stage_from_espo(opportunity.get("stage")),
                    self._compute_health_score(signals),
                ),
                "latest_urgency": self._compute_urgency(self._compute_health_score(signals), signals),
            }
        )
        self._request(
            "PUT",
            f"/Opportunity/{opportunity['id']}",
            json={
                "amount": int(float(opportunity.get("amount") or 0)),
                "stage": opportunity.get("stage"),
                "description": self._compose_text(body, meta),
                "closeDate": opportunity["closeDate"],
            },
        )

    def _derive_signal_specs(
        self,
        opportunity: dict[str, Any],
        workspace: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        notes = [item for item in workspace["notes"] if item.get("parentId") == opportunity["id"]]
        tasks = [item for item in workspace["tasks"] if item.get("parentId") == opportunity["id"]]
        activity_items = self._build_activities(opportunity, workspace["notes"])
        latest_activity = max((item.timestamp for item in activity_items), default=datetime.now(UTC) - timedelta(days=10))
        text_blob = "\n".join((item.get("post") or "") for item in notes).lower()
        specs: list[dict[str, Any]] = []
        deal_key = self._get_meta(opportunity.get("description"), "external_key") or opportunity["id"]
        if (datetime.now(UTC) - latest_activity).days >= 7:
            specs.append(
                self._signal_spec(
                    deal_key,
                    "engagement_drop",
                    "Reply velocity slowed",
                    f"Latest logged activity is {(datetime.now(UTC) - latest_activity).days} days old.",
                    "high",
                    -12,
                )
            )
        if "atlasiq" in text_blob or "competitor" in text_blob:
            specs.append(
                self._signal_spec(
                    deal_key,
                    "competitor_mention",
                    "Competitor surfaced",
                    "Opportunity notes mention a competitive fallback during procurement.",
                    "high",
                    -10,
                )
            )
        if "usage" in text_blob or "weekly active users" in text_blob or "adoption" in text_blob:
            specs.append(
                self._signal_spec(
                    deal_key,
                    "usage_decline",
                    "Usage decline detected",
                    "CRM notes reference reduced usage or adoption friction on the account.",
                    "high",
                    -13,
                )
            )
        if "support" in text_blob or "backlog" in text_blob or "escalation" in text_blob:
            specs.append(
                self._signal_spec(
                    deal_key,
                    "support_escalation",
                    "Support pressure increased",
                    "Customer-facing notes mention support escalation or a growing backlog.",
                    "medium",
                    -8,
                )
            )
        if "new executive sponsor" in text_blob or "sponsor changed" in text_blob:
            specs.append(
                self._signal_spec(
                    deal_key,
                    "stakeholder_change",
                    "Executive sponsor changed",
                    "CRM activity indicates a new decision owner for the account.",
                    "high",
                    -9,
                )
            )
        if "funding announced" in text_blob or "expansion program" in text_blob:
            specs.append(
                self._signal_spec(
                    deal_key,
                    "market_news",
                    "Expansion catalyst surfaced",
                    "Recent account notes mention a market or funding event that may accelerate demand.",
                    "low",
                    5,
                )
            )
        if "phased rollout pricing" in text_blob or "proposal revision" in text_blob:
            specs.append(
                self._signal_spec(
                    deal_key,
                    "positive_reply",
                    "Champion requested proposal revision",
                    "The buyer asked for a revised proposal rather than going silent.",
                    "medium",
                    8,
                )
            )
        overdue_tasks = [
            task for task in tasks
            if task.get("status") != "Completed" and (task.get("dateEnd") or str(datetime.now(UTC).date())) < str(datetime.now(UTC).date())
        ]
        if overdue_tasks:
            specs.append(
                self._signal_spec(
                    deal_key,
                    "engagement_drop",
                    "Execution follow-up slipped",
                    f"{len(overdue_tasks)} open task(s) are overdue on the opportunity.",
                    "medium",
                    -6,
                )
            )
        return specs

    def _signal_spec(
        self,
        deal_key: str,
        signal_type: str,
        title: str,
        detail: str,
        severity: str,
        weight: int,
    ) -> dict[str, Any]:
        return {
            "external_key": f"signal:{deal_key}:{signal_type}:{self._slugify(title)}",
            "type": signal_type,
            "title": title,
            "detail": detail,
            "severity": severity,
            "weight": weight,
        }

    def _upsert_note(self, existing_notes: list[dict[str, Any]], parent_id: str, post: str) -> None:
        external_key = self._get_meta(post, "external_key")
        existing = next(
            (
                item
                for item in existing_notes
                if item.get("parentId") == parent_id and self._get_meta(item.get("post"), "external_key") == external_key
            ),
            None,
        )
        payload = {"post": post, "parentType": "Opportunity", "parentId": parent_id}
        if existing:
            self._request("PUT", f"/Note/{existing['id']}", json={"post": post})
        else:
            created = self._request("POST", "/Note", json=payload)
            existing_notes.append(created)

    def _compute_health_score(self, signals: list[Signal]) -> int:
        delta = sum(signal.weight for signal in signals)
        return max(1, min(100, 70 + delta))

    def _compute_engagement_trend(self, signals: list[Signal]) -> str:
        delta = sum(signal.weight for signal in signals)
        if delta < -5:
            return "down"
        if delta > 5:
            return "up"
        return "flat"

    def _compute_stage_probability(self, stage: str, health_score: int) -> int:
        base = {
            "Lead": 22,
            "Qualified": 38,
            "Proposal": 58,
            "Negotiation": 68,
            "Closed Won": 100,
            "Closed Lost": 0,
        }.get(stage, 40)
        adjusted = base + round((health_score - 60) / 3)
        return max(1, min(100, adjusted))

    def _compute_urgency(self, health_score: int, signals: list[Signal]) -> str:
        if health_score < 50 or any(item.severity == "high" for item in signals):
            return "high"
        if health_score < 70:
            return "medium"
        return "low"

    def _derive_fit_score(self, industry: str, employee_band: str) -> int:
        score = 60
        if "ai" in industry.lower() or "saas" in industry.lower() or "health" in industry.lower():
            score += 15
        if employee_band in {"201-500", "501-1000"}:
            score += 12
        if employee_band == "1001-5000":
            score += 8
        return max(1, min(99, score))

    def _derive_influence_score(self, title: str) -> int:
        lowered = title.lower()
        if "chief" in lowered:
            return 95
        if "vp" in lowered:
            return 90
        if "director" in lowered:
            return 82
        return 70

    def _get_account_external_key(self, account_id: str, accounts: list[dict[str, Any]]) -> str:
        account = self._find_account(accounts, account_id)
        return self._get_meta(account.get("description"), "external_key") or account_id

    def _split_name(self, name: str) -> tuple[str, str]:
        parts = name.split(" ", 1)
        if len(parts) == 1:
            return parts[0], "-"
        return parts[0], parts[1]

    def _compose_text(self, body: str, meta: dict[str, Any]) -> str:
        clean_body = body.strip()
        return f"{clean_body}\n\n{META_MARKER}{json.dumps(meta, sort_keys=True)}"

    def _split_text_and_meta(self, text: str | None) -> tuple[str, dict[str, Any]]:
        if not text:
            return "", {}
        if META_MARKER not in text:
            return text.strip(), {}
        body, raw_meta = text.split(META_MARKER, 1)
        try:
            return body.strip(), json.loads(raw_meta.strip())
        except json.JSONDecodeError:
            return text.strip(), {}

    def _get_meta(self, text: str | None, key: str) -> Any:
        _, meta = self._split_text_and_meta(text)
        return meta.get(key)

    def _parse_datetime(self, value: Any, *, fallback: datetime | None = None) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            normalized = value.replace("Z", "+00:00").replace(" ", "T")
            try:
                parsed = datetime.fromisoformat(normalized)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=UTC)
                return parsed.astimezone(UTC)
            except ValueError:
                pass
        return fallback or datetime.now(UTC)

    def _map_stage_to_espo(self, stage: str) -> str:
        mapping = {
            "Lead": "Prospecting",
            "Qualified": "Qualification",
            "Proposal": "Proposal",
            "Negotiation": "Negotiation",
            "Closed Won": "Closed Won",
            "Closed Lost": "Closed Lost",
        }
        return mapping.get(stage, "Proposal")

    def _map_stage_from_espo(self, stage: str | None) -> str:
        mapping = {
            "Prospecting": "Lead",
            "Qualification": "Qualified",
            "Proposal": "Proposal",
            "Negotiation": "Negotiation",
            "Closed Won": "Closed Won",
            "Closed Lost": "Closed Lost",
        }
        return mapping.get(stage or "", "Proposal")

    def _slugify(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
