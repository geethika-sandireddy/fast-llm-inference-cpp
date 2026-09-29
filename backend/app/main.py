import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.hindsight_client import get_hindsight_service
from app.services.incident_agent import get_incident_agent

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title="SecOps Memory API",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in settings.cors_origins.split(",")
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    """Make sure the Hindsight memory bank is available."""
    get_hindsight_service().ensure_bank()


# ============================================================
# Request / Response Models
# ============================================================


class IncidentRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class IncidentResponse(BaseModel):
    title: str
    description: str
    response: str
    memories_used: list[str]
    hindsight_available: bool


class ResolveRequest(BaseModel):
    title: str = Field(..., min_length=1)
    incident_description: str = Field(..., min_length=1)

    # What the AI originally recommended
    ai_response: str = Field(..., min_length=1)

    # What the analyst actually did
    analyst_actions: str = Field(..., min_length=1)

    # Final result
    outcome: str = Field(..., min_length=1)

    # Human feedback about the response
    analyst_feedback: str = Field(..., min_length=1)


class ResolveResponse(BaseModel):
    incident_id: str
    stored: bool
    message: str


# ============================================================
# Health
# ============================================================


@app.get("/health")
def health() -> dict:
    hindsight_ok = (
        get_hindsight_service().ensure_bank()
    )

    return {
        "status": "ok",
        "env": settings.app_env,
        "hindsight_bank_id": settings.hindsight_bank_id,
        "hindsight_reachable": hindsight_ok,
    }


# ============================================================
# Analyze Incident
# ============================================================


@app.post(
    "/incidents/analyze",
    response_model=IncidentResponse,
)
def analyze_incident(
    request: IncidentRequest,
) -> IncidentResponse:

    try:
        agent = get_incident_agent()

        incident_text = (
            f"Incident title: {request.title}\n\n"
            f"Incident description: {request.description}"
        )

        result = agent.analyze(incident_text)

        return IncidentResponse(
            title=request.title,
            description=request.description,
            response=result.response,
            memories_used=result.memories_used,
            hindsight_available=result.hindsight_available,
        )

    except Exception as exc:
        logging.exception(
            "Incident analysis failed"
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# Resolve Incident + Store Analyst Feedback
# ============================================================


@app.post(
    "/incidents/{incident_id}/resolve",
    response_model=ResolveResponse,
)
def resolve_incident(
    incident_id: str,
    request: ResolveRequest,
) -> ResolveResponse:

    try:
        hindsight = get_hindsight_service()

        # Create a complete narrative for Hindsight.
        #
        # This is important because we want future agents to learn
        # not only what the incident was, but also:
        # - what AI recommended
        # - what the analyst actually did
        # - what the outcome was
        # - what the analyst learned
        memory_content = f"""
Resolved Security Incident

Incident ID:
{incident_id}

Incident Title:
{request.title}

Incident Description:
{request.incident_description}

AI Response:
{request.ai_response}

Actual Analyst Actions:
{request.analyst_actions}

Outcome:
{request.outcome}

Analyst Feedback:
{request.analyst_feedback}

Lesson for Future Incidents:
The analyst feedback and actual response above should be considered
when handling similar security incidents in the future.
""".strip()

        stored = hindsight.retain_incident_experience(
            incident_id=incident_id,
            summary_content=memory_content,
            incident_type="security_incident",
            outcome=request.outcome,
        )

        if not stored:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Incident was received, but the experience "
                    "could not be stored in Hindsight."
                ),
            )

        return ResolveResponse(
            incident_id=incident_id,
            stored=True,
            message=(
                "Incident resolution and analyst feedback "
                "were successfully stored in Hindsight."
            ),
        )

    except HTTPException:
        raise

    except Exception as exc:
        logging.exception(
            "Incident resolution failed"
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )