# Agent Flows

## Available Agents

The backend currently supports four agent workflows:

- `deal_intelligence`
- `prospecting`
- `retention`
- `competitive_intel`

Endpoints are defined in [backend/app/api/routes.py](../backend/app/api/routes.py).

## Common Response Shape

Every agent returns an `AgentInsight` object defined in [backend/app/core/models.py](../backend/app/core/models.py).

Core fields:

- `agent_type`
- `summary`
- `score`
- `rationale`
- `talking_points`
- `actions`
- `tools_used`
- `timeline`
- `generated_at`

## Execution Stages

The backend assembles a standard execution trace in [backend/app/agents/engine.py](../backend/app/agents/engine.py):

1. `Context loaded`
2. `Signals inspected`
3. `Narrative refined`
4. `Actions staged`

## Tool Call Semantics

The `tools_used` list is UI-facing telemetry for the run.

Current tool labels include:

- `CRMRepository.get_deal_detail`
- `Signal analyzer`
- `LLMService.enrich_insight`
- `AgentEngine action planner`

This lets the frontend show what happened in a way that is understandable to operators.

## LLM Behavior

LLM enrichment happens in [backend/app/services/llm_service.py](../backend/app/services/llm_service.py).

Behavior:

- If Gemini credentials are configured, the heuristic response is refined with stronger operator-facing language.
- If Gemini is unavailable or errors, the backend falls back to the deterministic heuristic output.

The trace reflects that:

- `completed` if LLM enrichment ran
- `skipped` if it did not

## CRM Persistence

Current persistence shape in EspoCRM:

- Latest rollup fields are stored inside Opportunity description metadata.
- Derived signals are stored as Espo `Note` records tagged with `kind = signal`.
- Activity history is stored as Espo `Note` records tagged with `kind = activity`.
- Agent runs are stored as Espo `Note` records tagged with `kind = analysis`.

This means the CRM contains both:

- the latest state used by the cockpit
- the historical artifacts created by analysis

## Action Execution

The agent never writes to the CRM during analysis.

It returns candidate actions such as:

- `create_task`
- `append_note`
- `update_deal`
- `send_playbook`

Only `/api/agents/action/execute` performs the write, and only after the operator clicks `Apply`.

Implementation lives in [backend/app/services/agent_service.py](../backend/app/services/agent_service.py).
