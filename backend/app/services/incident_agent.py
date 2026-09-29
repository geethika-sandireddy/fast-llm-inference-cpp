"""
SecOps incident-response agent.

Flow:

Current incident
      ↓
Hindsight recall
      ↓
Historical incident knowledge
      ↓
Groq LLM
      ↓
Recommended response plan
"""

from __future__ import annotations

from dataclasses import dataclass

from groq import Groq

from app.config import get_settings
from app.services.hindsight_client import (
    HindsightService,
    RecallResult,
    get_hindsight_service,
)


@dataclass
class IncidentAnalysis:
    """Result produced by the SecOps incident-response agent."""

    incident: str
    response: str
    memories_used: list[str]
    hindsight_available: bool


class IncidentAgent:
    """AI security incident-response agent."""

    def __init__(
        self,
        hindsight: HindsightService | None = None,
    ) -> None:

        settings = get_settings()

        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured in .env"
            )

        self._groq = Groq(
            api_key=settings.groq_api_key
        )

        self._model = settings.groq_model

        self._hindsight = (
            hindsight
            if hindsight is not None
            else get_hindsight_service()
        )

    def analyze(
        self,
        incident: str,
    ) -> IncidentAnalysis:
        """
        Analyze a security incident using the current incident
        plus historical organizational memory.
        """

        # -----------------------------------------------------
        # 1. Recall historical incidents
        # -----------------------------------------------------

        recall: RecallResult = (
            self._hindsight.recall_similar_incidents(
                query=incident,
                max_tokens=3000,
            )
        )

        memories = [
            memory.text
            for memory in recall.memories
        ]

        # -----------------------------------------------------
        # 2. Build historical context
        # -----------------------------------------------------

        if memories:
            historical_context = "\n\n".join(
                f"Historical Memory {i + 1}:\n{memory}"
                for i, memory in enumerate(memories)
            )
        else:
            historical_context = (
                "No relevant historical incident memories "
                "were available."
            )

        # -----------------------------------------------------
        # 3. System prompt
        # -----------------------------------------------------

        system_prompt = """
You are a Security Operations Center (SOC) incident-response analyst.

Analyze the security incident using ONLY:

1. Facts explicitly provided in the current incident.
2. Information explicitly present in the recalled historical memories.

IMPORTANT RULES:

- NEVER invent logs, timestamps, IP addresses, usernames,
  devices, cloud providers, event IDs, tools, alerts, SIEM
  results, or evidence.

- NEVER claim that an investigation was performed when it was
  not actually performed.

- If information is missing, write:
  "Not provided" or "Requires verification".

- Clearly separate:
    * Known Facts
    * Historical Lessons
    * Recommended Actions
    * Items Requiring Verification

- Historical memories are organizational experience.
  They are NOT evidence that the same facts are true in the
  current incident.

- Adapt historical response patterns to the current incident.

- Do not blindly copy previous responses.

- Do not invent facts to make the response more detailed.

- Prioritize safe containment and investigation.

Your response must contain:

1. Incident Assessment
2. Known Facts
3. Immediate Containment
4. Investigation Steps
5. Remediation
6. Relevant Historical Lessons
7. Items Requiring Verification
8. Recommended Next Actions
"""

        # -----------------------------------------------------
        # 4. User prompt
        # -----------------------------------------------------

        user_prompt = f"""
CURRENT SECURITY INCIDENT:

{incident}


HISTORICAL ORGANIZATIONAL MEMORY:

{historical_context}


Analyze the current incident using the historical memory
where relevant.

Create a practical incident-response plan for the SOC analyst.

Do not claim that any investigation has already happened
unless that fact is explicitly provided in the current
incident or historical memory.
"""

        # -----------------------------------------------------
        # 5. Call Groq
        # -----------------------------------------------------

        completion = self._groq.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                },
                {
                    "role": "user",
                    "content": user_prompt.strip(),
                },
            ],
            temperature=0.2,
        )

        response = (
            completion.choices[0]
            .message
            .content
            or "No response was generated."
        )

        # -----------------------------------------------------
        # 6. Return analysis
        # -----------------------------------------------------

        return IncidentAnalysis(
            incident=incident,
            response=response,
            memories_used=memories,
            hindsight_available=recall.available,
        )


_agent: IncidentAgent | None = None


def get_incident_agent() -> IncidentAgent:
    """Return the shared incident agent."""

    global _agent

    if _agent is None:
        _agent = IncidentAgent()

    return _agent