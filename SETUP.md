# Setup

## 1. Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for the full local stack)
- A Google Cloud project with the Gemini API enabled
- A ClickHouse instance (local via Docker, or ClickHouse Cloud)

## 2. Environment variables

Copy the template and fill in real values:

```bash
cp .env.example .env
```

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-1.5-pro

CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DATABASE=production_db
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

APP_ENV=development
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_PER_MINUTE=60
```

The backend runs without a `GEMINI_API_KEY` — each agent falls back to a
deterministic offline mode so the pipeline still produces a full demo, but
Gemini's reasoning materially improves scene extraction and recommendation
quality, so set a real key before the hackathon demo.

## 3. Deploy the Streamlit app

The repository includes `streamlit_app.py`, which runs the existing
orchestrator directly and does not require the FastAPI or React services.

### Streamlit Cloud

1. Create a new app from this repository.
2. Set the main file to `streamlit_app.py`.
3. In the app's **Settings > Secrets**, add:

```toml
GEMINI_API_KEY = "your-api-key"
GEMINI_MODEL = "gemini-1.5-pro"
```

4. Deploy. Streamlit Cloud installs `requirements.txt` automatically.

ClickHouse settings can be added to the same Secrets section when remote
history persistence is needed:

```toml
CLICKHOUSE_HOST = "your-clickhouse-host"
CLICKHOUSE_PORT = "8123"
CLICKHOUSE_DATABASE = "production_db"
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = "your-password"
```

The app also works without Gemini credentials by using the deterministic
fallback responses built into the agents.

## 4. Run everything with Docker Compose (recommended for the demo)

```bash
docker compose up --build
```

This starts:
- ClickHouse on `localhost:8123` (HTTP) / `9000` (native), seeded from
  `clickhouse/init.sql` and `clickhouse/sample_data.sql`
- The FastAPI backend on `localhost:8000`
- The React frontend on `localhost:3000`
- Grafana on `localhost:3001` (default login `admin` / `admin`)

## 5. Run components individually (development)

### Backend

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### ClickHouse schema (if not using Docker Compose)

```bash
clickhouse-client --multiquery < clickhouse/init.sql
clickhouse-client --multiquery < clickhouse/sample_data.sql
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## 6. Wiring Grafana to ClickHouse

1. Open Grafana at `localhost:3001`.
2. Add a data source → ClickHouse (install the ClickHouse plugin if not
   bundled) → host `clickhouse:8123` (or `localhost:8123` outside Docker),
   database `production_db`.
3. Build a panel over `risk_reports` (risk level over time) and
   `equipment_inventory` (current availability) for a production-wide view.

## 7. Deploying to Google Cloud Run

```bash
# Build and push the backend image
gcloud builds submit --tag gcr.io/PROJECT_ID/script-to-screen-guardian

# Store secrets
echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "$CLICKHOUSE_HOST" | gcloud secrets create clickhouse-host --data-file=-
echo -n "$CLICKHOUSE_USER" | gcloud secrets create clickhouse-user --data-file=-
echo -n "$CLICKHOUSE_PASSWORD" | gcloud secrets create clickhouse-password --data-file=-

# Replace PROJECT_ID in deployment.yaml, then deploy
gcloud run services replace deployment.yaml --region=us-central1
```

Point the frontend's `REACT_APP_API_URL` at the resulting Cloud Run URL and
redeploy the frontend (e.g. Cloud Run, Firebase Hosting, or Vercel).

## 8. Verifying the setup

```bash
curl http://localhost:8000/health
# {"status": "ok", "env": "development"}
```

Then open `localhost:3000`, run the pre-filled sample script, and confirm a
risk report renders for `SCENE_12`.
