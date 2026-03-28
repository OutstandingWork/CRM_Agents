# Repo Map

## Top Level

- [docker-compose.yml](../docker-compose.yml): local stack definition
- [.env.example](../.env.example): starter environment values
- [.env](../.env): local environment overrides
- [README.md](../README.md): main entry point for contributors

## Backend Map

- [backend/pyproject.toml](../backend/pyproject.toml): Python package metadata and dependencies
- [backend/Dockerfile](../backend/Dockerfile): API container image
- [backend/app/main.py](../backend/app/main.py): FastAPI app bootstrapping and CORS
- [backend/app/api/routes.py](../backend/app/api/routes.py): HTTP endpoints
- [backend/app/core/config.py](../backend/app/core/config.py): settings and env parsing
- [backend/app/core/models.py](../backend/app/core/models.py): shared request/response models
- [backend/app/agents/engine.py](../backend/app/agents/engine.py): heuristic agent logic and trace construction
- [backend/app/services/agent_service.py](../backend/app/services/agent_service.py): orchestration and action execution
- [backend/app/services/crm_service.py](../backend/app/services/crm_service.py): repository selection
- [backend/app/services/espo_adapter.py](../backend/app/services/espo_adapter.py): EspoCRM integration
- [backend/app/services/repository.py](../backend/app/services/repository.py): repository interface and in-memory/demo behavior
- [backend/app/services/llm_service.py](../backend/app/services/llm_service.py): Gemini enrichment layer
- [backend/tests/test_api.py](../backend/tests/test_api.py): API smoke tests

## Frontend Map

- [frontend/package.json](../frontend/package.json): scripts and dependencies
- [frontend/Dockerfile](../frontend/Dockerfile): frontend container image
- [frontend/index.html](../frontend/index.html): app shell and font loading
- [frontend/src/main.tsx](../frontend/src/main.tsx): React entrypoint
- [frontend/src/pages/App.tsx](../frontend/src/pages/App.tsx): main data-loading page
- [frontend/src/components/DealList.tsx](../frontend/src/components/DealList.tsx): deal selector
- [frontend/src/components/DealOverview.tsx](../frontend/src/components/DealOverview.tsx): selected-deal summary
- [frontend/src/components/AgentPanel.tsx](../frontend/src/components/AgentPanel.tsx): agent run UI, timeline, and actions
- [frontend/src/components/MetricCard.tsx](../frontend/src/components/MetricCard.tsx): KPI cards
- [frontend/src/components/ui.tsx](../frontend/src/components/ui.tsx): small shared UI primitives
- [frontend/src/lib/api.ts](../frontend/src/lib/api.ts): API client
- [frontend/src/lib/types.ts](../frontend/src/lib/types.ts): shared frontend types
- [frontend/src/styles.css](../frontend/src/styles.css): layout and design system

## Where To Start

If you are new to the codebase:

1. Read [README.md](../README.md).
2. Read [docs/ARCHITECTURE.md](./ARCHITECTURE.md).
3. Open [frontend/src/pages/App.tsx](../frontend/src/pages/App.tsx) and [backend/app/api/routes.py](../backend/app/api/routes.py).
4. Follow one end-to-end flow from button click to API response to CRM write-back.
