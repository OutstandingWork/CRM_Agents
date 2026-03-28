# Repo Map

## Top Level

- [docker-compose.yml](/home/pratyush/Desktop/CRM_AGENT/docker-compose.yml): local stack definition
- [.env.example](/home/pratyush/Desktop/CRM_AGENT/.env.example): starter environment values
- [.env](/home/pratyush/Desktop/CRM_AGENT/.env): local environment overrides
- [README.md](/home/pratyush/Desktop/CRM_AGENT/README.md): main entry point for contributors

## Backend Map

- [backend/pyproject.toml](/home/pratyush/Desktop/CRM_AGENT/backend/pyproject.toml): Python package metadata and dependencies
- [backend/Dockerfile](/home/pratyush/Desktop/CRM_AGENT/backend/Dockerfile): API container image
- [backend/app/main.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/main.py): FastAPI app bootstrapping and CORS
- [backend/app/api/routes.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/api/routes.py): HTTP endpoints
- [backend/app/core/config.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/core/config.py): settings and env parsing
- [backend/app/core/models.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/core/models.py): shared request/response models
- [backend/app/agents/engine.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/agents/engine.py): heuristic agent logic and trace construction
- [backend/app/services/agent_service.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/services/agent_service.py): orchestration and action execution
- [backend/app/services/crm_service.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/services/crm_service.py): repository selection
- [backend/app/services/espo_adapter.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/services/espo_adapter.py): EspoCRM integration
- [backend/app/services/repository.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/services/repository.py): repository interface and in-memory/demo behavior
- [backend/app/services/llm_service.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/services/llm_service.py): Gemini enrichment layer
- [backend/tests/test_api.py](/home/pratyush/Desktop/CRM_AGENT/backend/tests/test_api.py): API smoke tests

## Frontend Map

- [frontend/package.json](/home/pratyush/Desktop/CRM_AGENT/frontend/package.json): scripts and dependencies
- [frontend/Dockerfile](/home/pratyush/Desktop/CRM_AGENT/frontend/Dockerfile): frontend container image
- [frontend/index.html](/home/pratyush/Desktop/CRM_AGENT/frontend/index.html): app shell and font loading
- [frontend/src/main.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/main.tsx): React entrypoint
- [frontend/src/pages/App.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/pages/App.tsx): main data-loading page
- [frontend/src/components/DealList.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/components/DealList.tsx): deal selector
- [frontend/src/components/DealOverview.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/components/DealOverview.tsx): selected-deal summary
- [frontend/src/components/AgentPanel.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/components/AgentPanel.tsx): agent run UI, timeline, and actions
- [frontend/src/components/MetricCard.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/components/MetricCard.tsx): KPI cards
- [frontend/src/components/ui.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/components/ui.tsx): small shared UI primitives
- [frontend/src/lib/api.ts](/home/pratyush/Desktop/CRM_AGENT/frontend/src/lib/api.ts): API client
- [frontend/src/lib/types.ts](/home/pratyush/Desktop/CRM_AGENT/frontend/src/lib/types.ts): shared frontend types
- [frontend/src/styles.css](/home/pratyush/Desktop/CRM_AGENT/frontend/src/styles.css): layout and design system

## Where To Start

If you are new to the codebase:

1. Read [README.md](/home/pratyush/Desktop/CRM_AGENT/README.md).
2. Read [docs/ARCHITECTURE.md](/home/pratyush/Desktop/CRM_AGENT/docs/ARCHITECTURE.md).
3. Open [frontend/src/pages/App.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/pages/App.tsx) and [backend/app/api/routes.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/api/routes.py).
4. Follow one end-to-end flow from button click to API response to CRM write-back.
