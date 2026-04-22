# Avori Discovery

Avori Discovery is a TikTok Shop product-research tool for finding candidates, scoring them, and managing a lightweight watchlist.

The primary launch UI is now a Next.js research board in [`web/`](web). The Python FastAPI app remains the canonical backend for discovery, ranking, watchlist management, and chat.

## Deployment on Vercel

This repo is prepared for a same-repo Vercel launch with:

- `web/` as the Next.js frontend
- `app.py` as the FastAPI backend
- `vercel.json` using Vercel Services so both deploy under one project and one domain

Deployed route shape:

- `/` serves the Next.js UI
- `/api/*` serves the FastAPI backend

Important: Vercel Services is currently a private beta. If your Vercel account does not have Services enabled yet, the practical fallback is two Vercel projects from the same repo: one rooted at `web/`, one rooted at the repository root for the API.

### What deploys

- `web/` is the launch UI
- `app.py` is the backend entrypoint
- `vercel.json` mounts the backend under `/api`

### What stays local

- `dashboard.py` is still a Streamlit dashboard for local use
- Streamlit itself is not the Vercel entrypoint

### Environment variables

Set these in Vercel Project Settings:

- `TIKHUB_API_KEY`
- `AVORI_REGION` optional, defaults to `US`
- `AVORI_LANG` optional, defaults to `en`
- `AVORI_SEED_TERMS` optional, comma-separated
- `AVORI_SELLER_IDS` optional, comma-separated
- `AVORI_DATA_DIR` optional. If omitted on Vercel, the app uses `/tmp/avori-discovery`
- `AVORI_AGENT_MODEL` optional, defaults to `gpt-4o-mini`
- `AVORI_DASHBOARD_PRICE_MAX` optional, defaults to `200`
- `AVORI_SEARCH_PAGE_COUNT` optional, defaults to `3`
- `AVORI_TRACKING_GRADUATION_SOLD_COUNT` optional, defaults to `5000`
- `NEXT_PUBLIC_AVORI_API_BASE_URL` optional. Defaults to `/api` for Vercel Services. For local frontend development against a separately running backend, set it to `http://127.0.0.1:8000`

### Deploy

1. Import the GitHub repo into Vercel
2. Keep the root directory as the repository root
3. Ensure the project is configured for Services and that `vercel.json` is respected
4. Add the environment variables above
5. Deploy without a custom build command or output directory

### Local development

Backend only:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Frontend only:

```bash
cd web
npm install
NEXT_PUBLIC_AVORI_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

If your Vercel account has Services enabled, `vercel dev` is the closest match to the deployed route layout.

### API endpoints

- `GET /api/health`
- `POST /api/discovery/run`
- `GET /api/discovery/jobs/{job_id}`
- `GET /api/products/search?keyword=travel+bag`
- `GET /api/products/{product_id}`
- `POST /api/chat`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `POST /api/watchlist/refresh`
- `DELETE /api/watchlist/{product_id}`

### Persistence note

On Vercel, watchlist data, discovery job state, and agent session files default to `/tmp/avori-discovery`, which is writable but ephemeral. The app now stores watchlist and job state in SQLite instead of flat JSON, but Vercel deployments are still best for stateless API use and testing unless `AVORI_DATA_DIR` points to durable storage.

## Scheduled discovery

The repo includes `.github/workflows/daily-discovery.yml`, which runs the discovery pipeline every day and uploads the generated output files as a workflow artifact. The workflow also refreshes tracked watchlist products so velocity and graduation status keep updating over time.
