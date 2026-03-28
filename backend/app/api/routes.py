from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.models import (
    AgentInsight,
    AgentRequest,
    DashboardResponse,
    Deal,
    DealDetail,
    ExecuteActionRequest,
    ExecuteActionResponse,
    Note,
    NoteCreate,
    RuntimeContext,
    Signal,
    SignalCreate,
    Task,
    TaskCreate,
)
from app.core.config import get_settings
from app.services.agent_service import AgentService
from app.services.crm_service import get_repository
from app.services.repository import CRMRepository

router = APIRouter()


def get_agent_service(repository: CRMRepository = Depends(get_repository)) -> AgentService:
    return AgentService(repository)


@router.get("/health")
def health(repository: CRMRepository = Depends(get_repository)) -> dict[str, str | bool]:
    return {
        "status": "ok",
        "crm_provider": repository.provider_name,
        "live_crm_connected": repository.live_crm_connected,
    }


@router.get("/runtime", response_model=RuntimeContext)
def runtime(repository: CRMRepository = Depends(get_repository)) -> RuntimeContext:
    settings = get_settings()
    return RuntimeContext(
        app_name=settings.app_name,
        crm_provider=repository.provider_name,
        crm_mode_label=repository.crm_mode_label,
        live_crm_connected=repository.live_crm_connected,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(repository: CRMRepository = Depends(get_repository)) -> DashboardResponse:
    return repository.get_dashboard()


@router.get("/deals", response_model=list[Deal])
def deals(repository: CRMRepository = Depends(get_repository)) -> list[Deal]:
    return repository.list_deals()


@router.get("/deals/{deal_id}", response_model=DealDetail)
def deal_detail(deal_id: str, repository: CRMRepository = Depends(get_repository)) -> DealDetail:
    return repository.get_deal_detail(deal_id)


@router.get("/companies/{company_id}")
def company(company_id: str, repository: CRMRepository = Depends(get_repository)):
    return repository.get_company(company_id)


@router.get("/contacts/{contact_id}")
def contact(contact_id: str, repository: CRMRepository = Depends(get_repository)):
    return repository.get_contact(contact_id)


@router.post("/tasks", response_model=Task)
def create_task(payload: TaskCreate, repository: CRMRepository = Depends(get_repository)) -> Task:
    return repository.create_task(payload)


@router.post("/notes", response_model=Note)
def append_note(payload: NoteCreate, repository: CRMRepository = Depends(get_repository)) -> Note:
    return repository.append_note(payload)


@router.post("/signals/ingest", response_model=Signal)
def ingest_signal(payload: SignalCreate, repository: CRMRepository = Depends(get_repository)) -> Signal:
    return repository.ingest_signal(payload)


@router.post("/agents/prospect", response_model=AgentInsight)
def agent_prospect(payload: AgentRequest, service: AgentService = Depends(get_agent_service)) -> AgentInsight:
    return service.prospect(payload)


@router.post("/agents/deal-intelligence/analyze", response_model=AgentInsight)
def agent_deal_intelligence(
    payload: AgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentInsight:
    return service.deal_intelligence(payload)


@router.post("/agents/retention/analyze", response_model=AgentInsight)
def agent_retention(payload: AgentRequest, service: AgentService = Depends(get_agent_service)) -> AgentInsight:
    return service.retention(payload)


@router.post("/agents/competitive-intel/analyze", response_model=AgentInsight)
def agent_competitive_intel(
    payload: AgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentInsight:
    return service.competitive_intel(payload)


@router.post("/agents/action/execute", response_model=ExecuteActionResponse)
def execute_action(
    payload: ExecuteActionRequest,
    service: AgentService = Depends(get_agent_service),
) -> ExecuteActionResponse:
    return service.execute_action(payload)
