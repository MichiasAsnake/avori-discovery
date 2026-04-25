# Avori Discovery

Avori Discovery is a TikTok Shop product-research tool for finding candidates, scoring them, and managing a lightweight watchlist.

## Deployment on Vercel

This repo is prepared for Vercel as a Python API project.

### What deploys

- `app.py` is the FastAPI entrypoint Vercel detects automatically
- `/` serves a lightweight browser landing page with quick links and product search
- `/api`, `/health`, `/docs`, and the rest of the API routes are served directly by FastAPI

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

### Deploy

1. Import the GitHub repo into Vercel
2. Keep the root directory as the repository root
3. Add the environment variables above
4. Deploy without a custom build command or output directory

### API endpoints

- `GET /` browser landing page
- `GET /api` machine-readable deployment status
- `GET /health`
- `POST /discovery/run`
- `GET /discovery/jobs/{job_id}`
- `GET /products/search?keyword=travel+bag`
- `GET /products/{product_id}`
- `GET /watchlist`
- `POST /watchlist`
- `POST /watchlist/refresh`
- `DELETE /watchlist/{product_id}`

### Persistence note

On Vercel, watchlist data, discovery job state, and agent session files default to `/tmp/avori-discovery`, which is writable but ephemeral. The app now stores watchlist and job state in SQLite instead of flat JSON, but Vercel deployments are still best for stateless API use and testing unless `AVORI_DATA_DIR` points to durable storage.

## Scheduled discovery

The repo includes `.github/workflows/daily-discovery.yml`, which runs the discovery pipeline every day and uploads the generated output files as a workflow artifact. The workflow also refreshes tracked watchlist products so velocity and graduation status keep updating over time.
