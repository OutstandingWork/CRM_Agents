# Development Guide

## Prerequisites

- Docker and Docker Compose
- Python `3.12+` if running backend outside containers
- Node `20+` if running frontend outside containers

## Environment

Main environment variables are defined in:

- [.env.example](/home/pratyush/Desktop/CRM_AGENT/.env.example)
- [.env](/home/pratyush/Desktop/CRM_AGENT/.env)
- [backend/app/core/config.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/core/config.py)

Important values:

- `CRM_AGENT_CRM_PROVIDER`
- `CRM_AGENT_ESPO_BASE_URL`
- `CRM_AGENT_ESPO_USERNAME`
- `CRM_AGENT_ESPO_PASSWORD`
- `CRM_AGENT_CORS_ORIGINS`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `VITE_API_BASE_URL`

## Running With Docker

Start:

```bash
docker compose up --build
```

Stop:

```bash
docker compose down
```

View logs:

```bash
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f espocrm
```

Check running services:

```bash
docker compose ps
```

## Running Outside Docker

### Backend

```bash
cd backend
pip install -e .[dev]
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing And Validation

Backend tests:

```bash
cd backend
python -m pytest
```

Frontend build:

```bash
cd frontend
npm run build
```

Useful API probes:

```bash
curl http://localhost:8001/api/health
curl http://localhost:8001/api/runtime
curl http://localhost:8001/api/dashboard
```

Run deal intelligence directly:

```bash
curl -X POST http://localhost:8001/api/agents/deal-intelligence/analyze \
  -H 'Content-Type: application/json' \
  -d '{"deal_id":"deal-apex-expansion"}'
```

## Working On The Frontend

Start here:

- [frontend/src/pages/App.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/pages/App.tsx)
- [frontend/src/components/AgentPanel.tsx](/home/pratyush/Desktop/CRM_AGENT/frontend/src/components/AgentPanel.tsx)
- [frontend/src/styles.css](/home/pratyush/Desktop/CRM_AGENT/frontend/src/styles.css)

The visual system is currently:

- dark mode by default
- `Space Grotesk` for headlines
- `Manrope` for body copy
- glassy surface treatment with sparse accent color

If you change backend response models, update:

- [backend/app/core/models.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/core/models.py)
- [frontend/src/lib/types.ts](/home/pratyush/Desktop/CRM_AGENT/frontend/src/lib/types.ts)

## Working On The Backend

Start here:

- [backend/app/api/routes.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/api/routes.py)
- [backend/app/services/agent_service.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/services/agent_service.py)
- [backend/app/agents/engine.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/agents/engine.py)
- [backend/app/services/espo_adapter.py](/home/pratyush/Desktop/CRM_AGENT/backend/app/services/espo_adapter.py)

Rules of thumb:

- keep HTTP behavior in `routes.py`
- keep orchestration in `agent_service.py`
- keep agent reasoning and trace assembly in `engine.py`
- keep provider-specific CRM access in adapter/repository code

## Current Known Constraint

If Docker cannot reach Docker Hub, `docker compose up --build` may fail while resolving base images. In that case the running local images can still be used for development, but a fresh rebuild depends on outbound registry access.
