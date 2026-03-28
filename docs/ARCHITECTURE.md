# Architecture

## System Overview

This repo is a small full-stack app with three runtime layers:

1. `frontend`
2. `api`
3. `crm`

The frontend is the operator surface.
The API is the business layer.
EspoCRM is the CRM system of record.

## Request Flow

Typical user flow:

1. User opens the React app.
2. Frontend calls `/api/runtime`, `/api/dashboard`, and `/api/deals`.
3. User selects a deal.
4. Frontend calls `/api/deals/{deal_id}`.
5. User runs an agent.
6. Frontend calls an agent endpoint such as `/api/agents/deal-intelligence/analyze`.
7. Backend loads CRM context from the repository.
8. `AgentEngine` generates insight, timeline, tool-call trace, and candidate actions.
9. Optional LLM enrichment improves wording.
10. Frontend renders the result and waits for operator approval.
11. If the user clicks `Apply`, frontend calls `/api/agents/action/execute`.
12. Backend writes the approved action through the repository.

## Runtime Topology

Defined in [docker-compose.yml](../docker-compose.yml).

Services:

- `frontend`
- `api`
- `espocrm`
- `espocrm-db`

Published host ports:

- `5173` for the Vite frontend
- `8001` for the FastAPI backend
- `8080` for EspoCRM

Internal service-to-service calls:

- frontend -> API via `http://localhost:8001/api`
- API -> EspoCRM via `http://espocrm`
- EspoCRM -> MariaDB via `espocrm-db`

## Backend Layering

The backend is intentionally simple:

- `app/api/`
  Route definitions and HTTP surface
- `app/core/`
  Shared config and Pydantic models
- `app/services/`
  Repository implementations, CRM adapters, LLM integration, and orchestration service
- `app/agents/`
  Agent heuristics and response assembly
- `app/data/`
  Mock or seed data helpers

The main dependency path is:

`routes -> AgentService / repository -> AgentEngine -> LLMService`

## Frontend Layering

The frontend is also thin:

- `src/pages/App.tsx`
  top-level data loading and page composition
- `src/components/`
  deal list, deal overview, agent panel, metric cards, UI primitives
- `src/lib/api.ts`
  API client
- `src/lib/types.ts`
  frontend types mirroring backend response shapes
- `src/styles.css`
  visual system and layout

## Agent Trace Design

Each agent result now includes:

- `tools_used`
- `timeline`

These are not external tool invocations in the LangChain sense. They are explicit execution-stage metadata describing what the backend did while producing the insight.

That design gives the frontend enough information to show:

- what the agent looked at
- which internal subsystems were involved
- whether the LLM enrichment step ran
- whether the output is ready for approval

## Current CRM Storage Model

The current implementation keeps EspoCRM as the durable store in CRM mode by using:

- native `Account`, `Contact`, `Opportunity`, and `Task` records
- Opportunity description metadata for the latest rollup snapshot
- Espo `Note` records for:
  - seed notes
  - activity history
  - derived risk signals
  - persisted agent analysis runs

This avoids backend-only durable state while still keeping the implementation compatible with stock EspoCRM.
