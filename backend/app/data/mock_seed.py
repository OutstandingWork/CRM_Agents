from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.models import Activity, Company, Contact, Deal, Note, Signal, Task


def _ts(days_ago: int, hours: int = 0) -> datetime:
    return datetime.now(UTC) - timedelta(days=days_ago, hours=hours)


COMPANIES = [
    Company(
        id="comp-apex",
        name="Apex Robotics",
        industry="Manufacturing AI",
        employee_band="201-500",
        region="North America",
        fit_score=91,
        competitive_pressure=74,
        churn_risk=34,
        summary="Scaling enterprise automation programs across three new plants.",
    ),
    Company(
        id="comp-bluefin",
        name="Bluefin Cloud",
        industry="B2B SaaS",
        employee_band="501-1000",
        region="EMEA",
        fit_score=88,
        competitive_pressure=62,
        churn_risk=57,
        summary="Consolidating RevOps tooling while expanding enterprise accounts.",
    ),
    Company(
        id="comp-nimbus",
        name="Nimbus Health",
        industry="Healthtech",
        employee_band="1001-5000",
        region="North America",
        fit_score=79,
        competitive_pressure=68,
        churn_risk=81,
        summary="Usage has softened after a difficult platform migration.",
    ),
]

CONTACTS = [
    Contact(
        id="ctc-apex-1",
        name="Maya Chen",
        title="VP Revenue Operations",
        email="maya.chen@apex.example",
        company_id="comp-apex",
        persona="economic_buyer",
        influence_score=93,
    ),
    Contact(
        id="ctc-bluefin-1",
        name="Omar Haddad",
        title="Director of Sales Strategy",
        email="omar.haddad@bluefin.example",
        company_id="comp-bluefin",
        persona="champion",
        influence_score=83,
    ),
    Contact(
        id="ctc-nimbus-1",
        name="Nina Patel",
        title="Chief Customer Officer",
        email="nina.patel@nimbus.example",
        company_id="comp-nimbus",
        persona="executive_sponsor",
        influence_score=95,
    ),
]

DEALS = [
    Deal(
        id="deal-apex-expansion",
        name="Apex Robotics Expansion",
        company_id="comp-apex",
        primary_contact_id="ctc-apex-1",
        owner="Rhea Kapoor",
        stage="Negotiation",
        amount=180000,
        health_score=46,
        engagement_trend="down",
        risk_flags=["No stakeholder reply in 12 days", "Competitor mention", "Security review stalled"],
        recommended_next_action="Run executive recovery play with ROI plus security talking points.",
        agent_summary="Champion is still engaged, but legal and security stakeholders have gone quiet.",
        last_activity_at=_ts(2),
        stage_probability=57,
        days_in_stage=19,
        urgency="high",
    ),
    Deal(
        id="deal-bluefin-netnew",
        name="Bluefin Cloud Net-New",
        company_id="comp-bluefin",
        primary_contact_id="ctc-bluefin-1",
        owner="Arjun Mehta",
        stage="Proposal",
        amount=95000,
        health_score=71,
        engagement_trend="flat",
        risk_flags=["Pricing hesitation"],
        recommended_next_action="Package phased rollout with benchmark proof points.",
        agent_summary="Healthy discovery completed, but pricing pressure is increasing.",
        last_activity_at=_ts(1),
        stage_probability=66,
        days_in_stage=11,
        urgency="medium",
    ),
    Deal(
        id="deal-nimbus-renewal",
        name="Nimbus Health Renewal",
        company_id="comp-nimbus",
        primary_contact_id="ctc-nimbus-1",
        owner="Sara Iqbal",
        stage="Negotiation",
        amount=240000,
        health_score=39,
        engagement_trend="down",
        risk_flags=["Usage decline", "Support escalations", "Executive sponsor changed"],
        recommended_next_action="Launch retention intervention and exec sponsor alignment plan.",
        agent_summary="Renewal is at risk after adoption slipped in two regions.",
        last_activity_at=_ts(3),
        stage_probability=44,
        days_in_stage=25,
        urgency="high",
    ),
]

ACTIVITIES = [
    Activity(
        id="act-1",
        deal_id="deal-apex-expansion",
        kind="email",
        title="Sent revised security FAQ",
        timestamp=_ts(2, 6),
        owner="Rhea Kapoor",
        outcome="No reply yet",
    ),
    Activity(
        id="act-2",
        deal_id="deal-apex-expansion",
        kind="meeting",
        title="Commercial negotiation call",
        timestamp=_ts(5),
        owner="Rhea Kapoor",
        outcome="Buyer positive, procurement cautious",
    ),
    Activity(
        id="act-3",
        deal_id="deal-bluefin-netnew",
        kind="call",
        title="Pricing review",
        timestamp=_ts(1, 4),
        owner="Arjun Mehta",
        outcome="Requested phased pricing option",
    ),
    Activity(
        id="act-4",
        deal_id="deal-nimbus-renewal",
        kind="meeting",
        title="Quarterly business review",
        timestamp=_ts(7),
        owner="Sara Iqbal",
        outcome="Usage trend concerns raised by customer success",
    ),
]

TASKS = [
    Task(
        id="tsk-1",
        deal_id="deal-apex-expansion",
        title="Prepare executive ROI recap",
        owner="Rhea Kapoor",
        due_date=str((datetime.now(UTC) + timedelta(days=1)).date()),
        source="agent",
    ),
    Task(
        id="tsk-2",
        deal_id="deal-nimbus-renewal",
        title="Schedule retention workshop with CS lead",
        owner="Sara Iqbal",
        due_date=str((datetime.now(UTC) + timedelta(days=2)).date()),
        source="human",
    ),
]

NOTES = [
    Note(
        id="note-1",
        entity_id="deal-apex-expansion",
        entity_type="deal",
        content="Champion mentioned AtlasIQ in the last procurement thread.",
        created_at=_ts(4),
        author="AI Revenue Copilot",
    ),
    Note(
        id="note-2",
        entity_id="deal-nimbus-renewal",
        entity_type="deal",
        content="Support sentiment dipped after the migration bug backlog expanded.",
        created_at=_ts(6),
        author="Sara Iqbal",
    ),
]

SIGNALS = [
    Signal(
        id="sig-1",
        deal_id="deal-apex-expansion",
        type="engagement_drop",
        title="Reply velocity slowed",
        detail="Security stakeholders have not responded for 12 days.",
        severity="high",
        created_at=_ts(1),
        weight=-12,
    ),
    Signal(
        id="sig-2",
        deal_id="deal-apex-expansion",
        type="competitor_mention",
        title="Competitor surfaced",
        detail="Champion referenced AtlasIQ as a fallback in procurement.",
        severity="high",
        created_at=_ts(3),
        weight=-10,
    ),
    Signal(
        id="sig-3",
        deal_id="deal-bluefin-netnew",
        type="positive_reply",
        title="Champion requested proposal revision",
        detail="Requested phased rollout pricing instead of delaying.",
        severity="medium",
        created_at=_ts(1),
        weight=8,
    ),
    Signal(
        id="sig-4",
        deal_id="deal-nimbus-renewal",
        type="usage_decline",
        title="Usage decline in two business units",
        detail="Weekly active users fell 18% month over month in EMEA and APAC.",
        severity="high",
        created_at=_ts(2),
        weight=-13,
    ),
    Signal(
        id="sig-5",
        deal_id="deal-nimbus-renewal",
        type="stakeholder_change",
        title="New executive sponsor",
        detail="Former COO left; renewal now owned by the new CCO.",
        severity="high",
        created_at=_ts(5),
        weight=-9,
    ),
    Signal(
        id="sig-6",
        deal_id="deal-bluefin-netnew",
        type="market_news",
        title="Funding announced",
        detail="Bluefin announced a new EMEA expansion program that may accelerate demand.",
        severity="low",
        created_at=_ts(4),
        weight=5,
    ),
]
