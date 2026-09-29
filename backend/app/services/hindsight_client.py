"""
Hindsight memory service for SecOps Memory.

This module is the only place where the application talks directly
to the official hindsight-client SDK.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from hindsight_client import Hindsight
from hindsight_client_api.exceptions import ApiException

from app.config import get_settings

logger = logging.getLogger("secops_memory.hindsight")


class HindsightUnavailableError(Exception):
    """Raised when Hindsight cannot be reached or used."""


@dataclass
class SimilarIncidentMemory:
    """A recalled security incident memory."""

    text: str
    score: float | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class RecallResult:
    """Result returned by Hindsight recall."""

    memories: list[SimilarIncidentMemory]
    raw_query: str
    available: bool


class HindsightService:
    """Wrapper around the official Hindsight SDK."""

    def __init__(self) -> None:
        settings = get_settings()

        self._bank_id = settings.hindsight_bank_id

        self._client = Hindsight(
            base_url=settings.hindsight_base_url,
            api_key=settings.hindsight_api_key or None,
        )

        self._bank_ready = False

    def ensure_bank(self) -> bool:
        """
        Create the organization's Hindsight memory bank.

        If the bank already exists, reuse it.
        If Hindsight cannot be reached, return False instead of
        crashing the application.
        """

        if self._bank_ready:
            return True

        try:
            self._client.create_bank(
                bank_id=self._bank_id,
                name="SecOps Memory — Incident Response",
                mission=(
                    "Remember how this organization has handled past "
                    "security incidents — root causes, investigation "
                    "steps, containment actions, what worked, what did "
                    "not work, and analyst feedback — so future incidents "
                    "of a similar type get a faster and more "
                    "organization-specific response."
                ),
                background=(
                    "Security operations center (SOC) incident response "
                    "memory bank. Stores structured records of resolved "
                    "security incidents."
                ),
            )

            self._bank_ready = True

            logger.info(
                "Hindsight bank '%s' ready",
                self._bank_id,
            )

            return True

        except ApiException as exc:

            # A 409 normally means the bank already exists.
            # Treat that as success.
            if exc.status == 409:
                logger.info(
                    "Hindsight bank '%s' already exists. Reusing it.",
                    self._bank_id,
                )

                self._bank_ready = True
                return True

            # Do NOT treat every 4xx as "bank already exists".
            # For example:
            # 401 -> authentication problem
            # 402 -> insufficient credits
            # 403 -> permission problem
            # 404 -> incorrect endpoint/resource
            # 422 -> invalid request
            logger.error(
                "Hindsight API error while creating bank. "
                "HTTP status: %s | Error: %s",
                exc.status,
                exc,
            )

            return False

        except Exception:
            # Print the complete traceback so we can diagnose
            # SDK/network/configuration problems.
            logger.exception(
                "Hindsight bank creation failed unexpectedly"
            )

            return False

    def recall_similar_incidents(
        self,
        query: str,
        max_tokens: int = 3000,
    ) -> RecallResult:
        """
        Recall previous incidents that are semantically similar
        to the current incident.
        """

        try:
            result = self._client.recall(
                bank_id=self._bank_id,
                query=query,
                max_tokens=max_tokens,
                budget="mid",
            )

        except Exception:
            logger.exception(
                "Hindsight recall failed. "
                "Continuing without historical memory."
            )

            return RecallResult(
                memories=[],
                raw_query=query,
                available=False,
            )

        memories = []

        for item in getattr(result, "results", []):
            memories.append(
                SimilarIncidentMemory(
                    text=getattr(
                        item,
                        "text",
                        str(item),
                    ),
                    score=getattr(
                        item,
                        "score",
                        None,
                    ),
                    tags=list(
                        getattr(
                            item,
                            "tags",
                            [],
                        )
                        or []
                    ),
                )
            )

        return RecallResult(
            memories=memories,
            raw_query=query,
            available=True,
        )

    def retain_incident_experience(
        self,
        *,
        incident_id: str,
        summary_content: str,
        incident_type: str,
        outcome: str,
        document_id: str | None = None,
    ) -> bool:
        """
        Store a resolved security incident as durable memory.

        Hindsight receives the complete incident narrative and extracts
        useful information from it for future recall.
        """

        try:
            self._client.retain(
                bank_id=self._bank_id,
                content=summary_content,
                document_id=document_id or incident_id,
                tags=[
                    f"type:{incident_type}",
                    f"outcome:{outcome}",
                    f"incident:{incident_id}",
                ],
                context=(
                    "Resolved security incident retained for "
                    "future incident-response recall."
                ),
            )

            logger.info(
                "Incident '%s' successfully retained in Hindsight.",
                incident_id,
            )

            return True

        except ApiException as exc:
            logger.error(
                "Hindsight retain API error for incident '%s'. "
                "HTTP status: %s | Error: %s",
                incident_id,
                exc.status,
                exc,
            )

            return False

        except Exception:
            logger.exception(
                "Hindsight retain failed for incident '%s'.",
                incident_id,
            )

            return False

    def close(self) -> None:
        """Close the Hindsight HTTP connection."""

        try:
            self._client.close()
        except Exception:
            logger.exception("Error while closing Hindsight client.")


# Singleton service instance
_service: HindsightService | None = None


def get_hindsight_service() -> HindsightService:
    """Return the shared Hindsight service."""

    global _service

    if _service is None:
        _service = HindsightService()

    return _service