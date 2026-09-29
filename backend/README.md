# SecOps Memory — Backend (Phase 1–3)

What exists so far: FastAPI app, config, and a working `HindsightService`
wrapper around the real `hindsight-client` SDK, plus the smoke test that
proves retain → recall actually round-trips. No LLM, no incident agent,
no frontend yet — that's Phase 4+.

## Setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

- **Hindsight Cloud** (recommended for the hackathon — zero infra):
  set `HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io` and
  `HINDSIGHT_API_KEY=<your key>`. Apply promo code `MEMHACK99` in the
  billing section after registering for $50 in free credits.
- **Local Docker** instead:
  ```bash
  export OPENAI_API_KEY=sk-xxx
  docker run --rm -it --pull always -p 8888:8888 -p 9999:9999 \
    -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
    -v $HOME/.hindsight-docker:/home/hindsight/.pg0 \
    ghcr.io/vectorize-io/hindsight:latest
  ```
  then set `HINDSIGHT_BASE_URL=http://localhost:8888` and leave
  `HINDSIGHT_API_KEY` blank.

## Phase 3 checkpoint — run this first

```bash
pytest tests/test_hindsight_smoke.py -v -s
```

This retains one synthetic incident memory, waits for Hindsight's async
processing, then recalls it and asserts it comes back. **Do not build
anything past this point until it passes.** In my sandbox this fails
cleanly with "Bank creation/connection failed" because I have no network
route to Hindsight's servers and can't run Docker here — that's expected;
run it yourself against your real Hindsight Cloud key or local instance.

## Run the API

```bash
uvicorn app.main:app --reload --port 8000
curl http://localhost:8000/health
```

`hindsight_reachable` in the response tells you immediately whether the
bank connection is live — that's the same check the smoke test uses.

## What's next (Phase 4+, not built yet)

- `services/llm_client.py` — Groq wrapper
- `services/incident_agent.py` — the analyze → recall → generate → retain
  orchestration from the architecture diagram
- `routers/incidents.py` — `POST /incidents`, `POST /incidents/{id}/resolve`
- Frontend (Next.js)
