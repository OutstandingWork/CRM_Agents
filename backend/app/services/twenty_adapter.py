from __future__ import annotations

from app.core.models import NoteCreate, SignalCreate, TaskCreate
from app.services.repository import CRMRepository, MockCRMRepository


class TwentyCRMRepository(MockCRMRepository, CRMRepository):
    """
    Thin placeholder adapter.

    The demo app runs against the in-memory seed model until a live Twenty workspace
    is wired in. The class exists so the rest of the backend depends on a stable CRM
    repository interface instead of the mock implementation directly.
    """

    def create_task(self, payload: TaskCreate):
        return super().create_task(payload)

    def append_note(self, payload: NoteCreate):
        return super().append_note(payload)

    def ingest_signal(self, payload: SignalCreate):
        return super().ingest_signal(payload)
