# weather-mcp-server

An [MCP](https://modelcontextprotocol.io/) server wrapping the [Open-Meteo API](https://open-meteo.com/), deployed on GCP Cloud Run. No API key required — Open-Meteo is free and open.

## Tools

| Tool | Description |
|---|---|
| `get_current_weather` | Current conditions for a lat/lon |
| `get_forecast` | Up to 16-day daily (or hourly) forecast |
| `get_historical_weather` | Historical daily data for a date range |

## Local development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8080

# Health check
curl http://localhost:8080/health

# Test with MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8080/mcp
```

## GCP Setup (one-time)

### 1. Enable APIs
```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  --project=weather-mcp-project
```

### 2. Create Artifact Registry repository
```bash
gcloud artifacts repositories create mcp-images \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker images for weather-mcp-server" \
  --project=weather-mcp-project
```

### 3. Set cleanup policy (keeps storage within free 0.5 GB tier)
```bash
gcloud artifacts repositories set-cleanup-policies mcp-images \
  --project=weather-mcp-project \
  --location=us-central1 \
  --policy='[{"name":"keep-last-2","action":{"type":"Keep"},"mostRecentVersions":{"keepCount":2}}]'
```

### 4. Create a Service Account for GitHub Actions
```bash
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions SA" \
  --project=weather-mcp-project

# Grant required roles
for role in roles/run.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding weather-mcp-project \
    --member="serviceAccount:github-actions-sa@weather-mcp-project.iam.gserviceaccount.com" \
    --role="$role"
done

# Export key
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=github-actions-sa@weather-mcp-project.iam.gserviceaccount.com
```

### 5. Add GitHub repository secrets

In your repo → **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
|---|---|
| `GCP_SA_KEY` | Contents of `sa-key.json` (delete the file after!) |

> The project ID and region are hardcoded in the workflow — no secret needed for those.

## Deployment

Push to `main` — GitHub Actions builds the Docker image, pushes it to Artifact Registry, and deploys to Cloud Run automatically.

## Smoke test (post-deploy)

```bash
CLOUD_RUN_URL=https://<your-cloud-run-url>

# Health
curl $CLOUD_RUN_URL/health

# List MCP tools
curl -X POST $CLOUD_RUN_URL/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## Cost

Everything runs within GCP free tier limits at typical personal/dev usage. See [PLAN.md](./PLAN.md) for the full breakdown.
