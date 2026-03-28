# CRM Agent

SalesOps demo stack for running CRM-aware revenue agents on top of a lightweight self-hosted CRM.

It combines:

- `frontend/`: React + Vite operator cockpit
- `backend/`: FastAPI API, CRM abstraction layer, and agent orchestration
- `docker-compose.yml`: local runtime for frontend, API, EspoCRM, and MariaDB

The current product shape is:

- A dark-mode SaaS-style cockpit for reviewing deals and running agent workflows
- A FastAPI backend that exposes deals, dashboard state, and agent endpoints
- EspoCRM as the live system of record for CRM entities
- Review-first agent actions that can write back to the CRM only after approval
- CRM-backed analysis state where:
  - latest rollup is stored on Opportunity description metadata
  - signal history is stored in Espo Notes
  - activity history is stored in Espo Notes
  - analysis runs are stored in Espo Notes

## Quick Start

1. Copy the environment file.

```bash
cp .env.example .env
```

2. Set a Gemini key if you want LLM enrichment.

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

3. Start the stack.

```bash
docker compose up --build
```

4. Open the app.

- Frontend: `http://localhost:5173`
- API: `http://localhost:8001`
- API docs: `http://localhost:8001/docs`
- EspoCRM: `http://localhost:8080`

EspoCRM default login:

- Username: `admin`
- Password: `admin`

## What Is In The Repo

### Frontend

The frontend is a single-screen operator workspace that:

- loads dashboard, runtime, and deal detail data from the API
- lets an operator run one of four agent workflows
- shows execution timeline and tool-call trace for each run
- lets the operator apply returned actions back into the CRM

Key files:

- [frontend/src/pages/App.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/pages/App.tsx)
- [frontend/src/components/AgentPanel.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/components/AgentPanel.tsx)
- [frontend/src/components/DealOverview.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/components/DealOverview.tsx)
- [frontend/src/lib/api.ts](/home/pratyush/Desktop/CRM_AGENT/frontend/src/lib/api.ts)
- [frontend/src/styles.css](/home/pratyush/Desktop/CRM_AGENT/frontend/src/styles.css)

### Backend

The backend exposes a thin application API over a repository layer and agent engine.

The main responsibilities are:

- return dashboard and deal data
- normalize access to the configured CRM provider
- generate agent insights and actions
- execute approved actions through the repository

Key files:

- [backend/app/main.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/main.py)
- [backend/app/api/routes.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/api/routes.py)
- [backend/app/services/agent_service.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/services/agent_service.py)
- [backend/app/agents/engine.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/agents/engine.py)
- [backend/app/services/espo_adapter.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/services/espo_adapter.py)
- [backend/app/core/models.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/core/models.py)

## Agent Flows

The app currently exposes four workflow types:

- `deal_intelligence`
- `prospecting`
- `retention`
- `competitive_intel`

Each agent response returns:

- a summary
- a score
- rationale bullets
- talking points
- reviewable actions
- `tools_used`
- `timeline`

The timeline and tool-call trace are generated in [backend/app/agents/engine.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/agents/engine.py) and rendered in [frontend/src/components/AgentPanel.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/components/AgentPanel.tsx).

Current CRM persistence model:

- Accounts, Contacts, Opportunities, and Tasks are native Espo records
- Latest health/risk rollup is embedded in Opportunity description metadata
- Seed notes, derived risk signals, activity history, and agent runs are stored as Espo `Note` records with structured metadata
- In `espo` mode the backend no longer silently falls back to hidden in-memory mock reads

## Runtime Notes

- Frontend container publishes `5173`
- API container publishes `8001 -> 8000`
- EspoCRM publishes `8080 -> 80`
- API talks to EspoCRM over Docker service DNS using `http://espocrm`

The current stack was verified locally with:

- reachable frontend on `http://localhost:5173`
- reachable API on `http://localhost:8001`
- reachable EspoCRM on `http://localhost:8080`
- successful `POST /api/agents/deal-intelligence/analyze` calls in API logs

## Development

Read these next:

- [docs/ARCHITECTURE.md](/home/pratyush/Desktop/CRM_AGENT/docs/ARCHITECTURE.md)
- [docs/DEVELOPMENT.md](/home/pratyush/Desktop/CRM_AGENT/docs/DEVELOPMENT.md)
- [docs/AGENT-FLOWS.md](/home/pratyush/Desktop/CRM_AGENT/docs/AGENT-FLOWS.md)
- [docs/REPO-MAP.md](/home/pratyush/Desktop/CRM_AGENT/docs/REPO-MAP.md)

## Testing

Backend tests live in [backend/tests/test_api.py](/home/pratyush/Desktop/CRM_AGENT/backend/tests/test_api.py).

Typical commands:

```bash
cd backend
python -m pytest
```

```bash
cd frontend
npm run build
```

If local host toolchains are not installed, the same commands can be run inside the running containers.
