from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.core.config import Settings
from app.core.models import AgentInsight, DealDetail


@dataclass
class LLMService:
    settings: Settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.gemini_api_key and self.settings.llm_provider.lower() == "gemini")

    def enrich_insight(self, insight: AgentInsight, detail: DealDetail) -> AgentInsight:
        if not self.enabled:
            return insight

        prompt = self._build_prompt(insight, detail)
        payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "You are a concise B2B sales operations copilot. "
                            "Return strict JSON with keys summary, rationale, and talking_points. "
                            "summary must be one sentence. rationale must be an array of 3 concise bullets. "
                            "talking_points must be an array of 3 concise bullets."
                        )
                    }
                ]
            },
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "responseMimeType": "application/json",
            },
        }

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
        )

        try:
            response = httpx.post(
                url,
                params={"key": self.settings.gemini_api_key},
                json=payload,
                timeout=20.0,
            )
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            return insight.model_copy(
                update={
                    "summary": parsed.get("summary", insight.summary),
                    "rationale": parsed.get("rationale", insight.rationale)[:3],
                    "talking_points": parsed.get("talking_points", insight.talking_points)[:3],
                }
            )
        except Exception:
            return insight

    def _build_prompt(self, insight: AgentInsight, detail: DealDetail) -> str:
        signals = "\n".join(
            f"- {signal.title}: {signal.detail} ({signal.severity})" for signal in detail.signals[:4]
        )
        return f"""
Agent type: {insight.agent_type}
Deal: {detail.deal.name}
Company: {detail.company.name}
Industry: {detail.company.industry}
Owner: {detail.deal.owner}
Stage: {detail.deal.stage}
Amount: {detail.deal.amount}
Health score: {detail.deal.health_score}
Engagement trend: {detail.deal.engagement_trend}
Current heuristic summary: {insight.summary}

Signals:
{signals}

Return stronger operator-facing language for a CRM cockpit.
""".strip()
