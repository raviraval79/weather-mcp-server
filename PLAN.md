# weather-mcp-server — Project Plan

A Python MCP server wrapping the [Open-Meteo API](https://open-meteo.com/), served over
Streamable HTTP, containerized with Docker, and deployed to GCP Cloud Run (free tier).
GitHub is the source of truth; GitHub Actions handles CI/CD.

---

## Repository Structure

```
weather-mcp-server/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD: build → push to Artifact Registry → deploy to Cloud Run
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + MCP endpoint (Streamable HTTP)
│   ├── tools.py                # MCP tool definitions
│   └── openmeteo.py            # Async Open-Meteo API client (httpx)
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── .env.example
└── README.md
```

---

## MCP Tools

All tools call the Open-Meteo API — no API key required.

| Tool | Description |
|---|---|
| `get_current_weather` | Current conditions for a given latitude/longitude |
| `get_forecast` | N-day hourly or daily forecast |
| `get_historical_weather` | Historical weather data for a date range |

---

## Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| HTTP framework | FastAPI + uvicorn |
| MCP protocol | `mcp[server]` (Anthropic Python SDK), Streamable HTTP transport |
| HTTP client | `httpx` (async) |
| Container | Docker (`python:3.12-slim`) |
| Registry | GCP Artifact Registry |
| Deployment | GCP Cloud Run |
| CI/CD | GitHub Actions |

---

## Phase 1 — GCP Setup (one-time, manual)

1. Enable APIs:
   - `Artifact Registry API`
   - `Cloud Run API`
2. Create an Artifact Registry Docker repository, e.g.:
   ```
   us-central1-docker.pkg.dev/<GCP_PROJECT_ID>/mcp-images
   ```
3. Create a GCP Service Account for GitHub Actions with these roles:
   - `roles/run.admin`
   - `roles/artifactregistry.writer`
   - `roles/iam.serviceAccountUser`
4. Export the Service Account key as JSON.
5. Add the following GitHub repository secrets:
   - `GCP_SA_KEY` — the Service Account JSON key
   - `GCP_PROJECT_ID` — your GCP project ID
   - `GCP_REGION` — target region (recommended: `us-central1`)

> **Note:** Cloud Build API is **not** needed. Docker images are built inside GitHub Actions
> and only pushed to Artifact Registry; Cloud Run pulls from there directly.

---

## Phase 2 — Artifact Registry Cleanup Policy

To keep image storage permanently within the **0.5 GB free tier**, configure a cleanup policy
on the Artifact Registry repository to retain only the last 2 tagged images. This can be set
via the GCP Console or `gcloud` CLI:

```bash
gcloud artifacts repositories set-cleanup-policies mcp-images \
  --project=$GCP_PROJECT_ID \
  --location=us-central1 \
  --policy='[{"name":"keep-last-2","action":{"type":"Keep"},"mostRecentVersions":{"keepCount":2}}]'
```

---

## Phase 3 — Containerization

- Base image: `python:3.12-slim`
- Runs as a **non-root user** for security
- Exposes port **8080** (Cloud Run default)
- `.dockerignore` excludes `.git`, `__pycache__`, `.env`, and test files to keep image lean

---

## Phase 4 — CI/CD (GitHub Actions)

**Trigger:** push to `main` branch

**Pipeline steps:**
1. Authenticate to GCP using `GCP_SA_KEY` secret (via `google-github-actions/auth`)
2. Configure Docker to push to Artifact Registry
3. Build Docker image and push:
   ```
   us-central1-docker.pkg.dev/<project>/mcp-images/weather-mcp-server:$GITHUB_SHA
   ```
4. Deploy to Cloud Run with free-tier-optimised flags:
   ```
   --min-instances=0        # scale to zero when idle → $0 cost at rest
   --max-instances=3
   --memory=512Mi
   --cpu=1
   --port=8080
   --allow-unauthenticated  # adjust if you want to lock the endpoint down
   ```

---

## Phase 5 — Free Tier Summary

| GCP Service | Free Allowance | Expected Usage | Cost |
|---|---|---|---|
| Cloud Run | 2M requests, 180K vCPU-sec, 360K GiB-sec / month | Low (dev/personal) | **$0** |
| Artifact Registry | 0.5 GB storage | ~150–200 MB (with cleanup policy) | **$0** |
| Cloud Build | Not used (builds run in GitHub Actions) | — | **$0** |
| GitHub Actions | 2,000 min/month (private repo) | ~3–5 min/deploy | **$0** |
| Open-Meteo API | Unlimited (no key required) | — | **$0** |

**Total estimated monthly cost: $0**

---

## Phase 6 — Local Development & Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8080

# Test with MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8080/mcp
```

---

## Phase 7 — Post-Deploy Validation

```bash
# Smoke test against the live Cloud Run URL
curl -X POST https://<cloud-run-url>/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

---

## Next Steps

1. Create the GCP project resources (Phase 1)
2. Add GitHub secrets
3. Scaffold the application code (`app/`, `Dockerfile`, `requirements.txt`)
4. Set up the GitHub Actions workflow (`.github/workflows/deploy.yml`)
5. Push to `main` and verify the first deployment
