## Avori Web

This is the primary launch UI for Avori Discovery. It is a Next.js App Router frontend that consumes the FastAPI backend exposed under `/api` in production.

### Local development

```bash
cd web
npm install
NEXT_PUBLIC_AVORI_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Run the backend separately from the repository root:

```bash
uvicorn app:app --reload
```

### Scripts

```bash
npm run dev
npm test
npm run build
```

### Audit-specific UI behavior

- candidates and watchlist are separate main-body tabs
- discovery uses the async job API pattern
- detail panel shows image, review summary, categories, supplementary signals, TikTok URL, and watchlist controls
- the candidates table is fixed-height with CSV export
- score includes both raw value and visual tier
- chat uses natural-language prompts rather than pipe-delimited debug strings

### Deployment

The repository root contains `vercel.json` configured for Vercel Services:

- `web/` mounted at `/`
- `app.py` mounted at `/api`

If Services is unavailable for your account, deploy `web/` and the backend as separate Vercel projects from the same repository.
