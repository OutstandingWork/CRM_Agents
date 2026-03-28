from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.repository import CRMRepository, MockCRMRepository
from app.services.espo_adapter import EspoCRMRepository


@lru_cache
def get_repository() -> CRMRepository:
    settings = get_settings()
    if settings.crm_provider.lower() in {"espo", "espocrm"}:
        return EspoCRMRepository(settings)
    return MockCRMRepository()
