# Avori Discovery

Avori Discovery is a TikTok Shop product-research tool for finding candidates, scoring them, and managing a lightweight watchlist.

## Deployment on Vercel

This repo is prepared for Vercel as a Python API project.

### What deploys

- `api/index.py` exposes a FastAPI wrapper for the discovery workflow
- `/` rewrites to `/api`
- `/health` rewrites to `/api/health`
- `/docs` rewrites to `/api/docs`

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

### Deploy

1. Import the GitHub repo into Vercel
2. Keep the root directory as the repository root
3. Add the environment variables above
4. Deploy

### API endpoints

- `GET /health`
- `POST /api/discovery/run`
- `GET /api/products/search?keyword=travel+bag`
- `GET /api/products/{product_id}`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `DELETE /api/watchlist/{product_id}`

### Persistence note

On Vercel, watchlist data and agent session files default to `/tmp/avori-discovery`, which is writable but ephemeral. That means Vercel deployments are good for stateless API use and testing, but watchlist persistence is not guaranteed across cold starts or redeploys unless you later move that data to a real external store.
