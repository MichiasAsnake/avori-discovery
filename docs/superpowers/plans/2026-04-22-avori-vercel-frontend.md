# Avori Vercel Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Vercel-deployed Next.js frontend in the same repo that replaces Streamlit as the primary UI and implements the approved frontend audit.

**Architecture:** Add a `web/` Next.js App Router app that consumes the existing FastAPI backend over same-origin API paths. Keep Python discovery and storage logic intact, add the missing browser-facing chat endpoint, and implement the audit-driven layout in the React UI.

**Tech Stack:** Next.js App Router, TypeScript, React, FastAPI, Python, pytest, Node test runner

---

### Task 1: Scaffold the Next.js app and deployment shape

**Files:**
- Create: `web/package.json`
- Create: `web/next.config.ts`
- Create: `web/tsconfig.json`
- Create: `web/src/app/layout.tsx`
- Create: `web/src/app/page.tsx`
- Create: `web/src/app/globals.css`
- Modify: `README.md`
- Test: `web/package.json`

- [ ] **Step 1: Write the failing deployment test**

Create a build script and expect it to fail before the app exists:

```bash
cd web
npm run build
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm run build
```

Expected: FAIL because `web/` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Scaffold a Next.js App Router app under `web/` with:

- TypeScript
- App Router
- root layout
- root page
- global styles
- build/dev scripts

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm run build
```

Expected: PASS with a successful Next.js production build.

- [ ] **Step 5: Commit**

```bash
git -C /tmp/avori-discovery/.worktrees/vercel-frontend add web README.md
git -C /tmp/avori-discovery/.worktrees/vercel-frontend commit -m "Scaffold Next.js frontend for Vercel"
```

### Task 2: Add browser-facing backend support for launch

**Files:**
- Modify: `app.py`
- Modify: `agent.py`
- Test: `tests/test_api.py`
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:

- a chat API endpoint that accepts a message and returns an agent reply
- a natural-language candidate discussion seed helper if needed

Example test shape:

```python
def test_chat_endpoint_returns_message(client):
    response = client.post("/chat", json={"message": "Assess this product"})
    assert response.status_code == 200
    assert "reply" in response.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
/tmp/avori-discovery/.venv/bin/python -m pytest tests/test_api.py tests/test_agent.py -q
```

Expected: FAIL because `/chat` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add:

- a small POST `/chat` API route in `app.py`
- backend plumbing in `agent.py` that reuses the existing agent/session flow for browser chat

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
/tmp/avori-discovery/.venv/bin/python -m pytest tests/test_api.py tests/test_agent.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git -C /tmp/avori-discovery/.worktrees/vercel-frontend add app.py agent.py tests/test_api.py tests/test_agent.py
git -C /tmp/avori-discovery/.worktrees/vercel-frontend commit -m "Add browser chat API for frontend"
```

### Task 3: Build the shared frontend data layer

**Files:**
- Create: `web/src/lib/api.ts`
- Create: `web/src/lib/polling.ts`
- Create: `web/src/lib/csv.ts`
- Create: `web/src/lib/score.ts`
- Create: `web/src/types/avori.ts`
- Test: `web/src/lib/score.test.ts`
- Test: `web/src/lib/csv.test.ts`

- [ ] **Step 1: Write the failing tests**

Add tests for:

- score label mapping
- CSV export shaping
- polling helper completion behavior

Example:

```ts
import { describe, expect, it } from "vitest";
import { scoreTier } from "./score";

describe("scoreTier", () => {
  it("maps strong scores to high", () => {
    expect(scoreTier(90)).toBe("high");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm test -- --runInBand
```

Expected: FAIL because helper modules do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create:

- API client functions for discovery/search/detail/watchlist/chat
- polling helper for job status
- CSV export helper for candidates
- score legend/tier helper
- shared frontend types

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm test -- --runInBand
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git -C /tmp/avori-discovery/.worktrees/vercel-frontend add web/src/lib web/src/types
git -C /tmp/avori-discovery/.worktrees/vercel-frontend commit -m "Add frontend API and utility layer"
```

### Task 4: Implement the audit-driven page layout

**Files:**
- Create: `web/src/components/discovery-sidebar.tsx`
- Create: `web/src/components/candidates-table.tsx`
- Create: `web/src/components/detail-panel.tsx`
- Create: `web/src/components/watchlist-panel.tsx`
- Create: `web/src/components/chat-panel.tsx`
- Create: `web/src/components/empty-state.tsx`
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/app/globals.css`
- Test: `web/src/app/page.test.tsx`

- [ ] **Step 1: Write the failing tests**

Add React tests for:

- tabs `Candidates` and `Watchlist`
- onboarding empty state
- score legend
- image rendering in detail panel
- review summary visible above signals
- CSV export button

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm test -- --runInBand
```

Expected: FAIL because the audited UI is not implemented yet.

- [ ] **Step 3: Write minimal implementation**

Implement:

- sidebar with controls only
- main body tabs
- fixed-height candidates table
- wider detail pane than chat pane
- detail image
- visible score help
- visible review summary
- natural-language discuss prompt
- CSV export
- watchlist main-tab layout
- velocity as metric/trend

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm test -- --runInBand
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git -C /tmp/avori-discovery/.worktrees/vercel-frontend add web/src/components web/src/app
git -C /tmp/avori-discovery/.worktrees/vercel-frontend commit -m "Implement audited Avori research interface"
```

### Task 5: Connect the frontend to live backend flows

**Files:**
- Modify: `web/src/app/page.tsx`
- Modify: `web/src/components/chat-panel.tsx`
- Modify: `web/src/components/watchlist-panel.tsx`
- Test: `web/src/app/page.test.tsx`

- [ ] **Step 1: Write the failing tests**

Add integration-style component tests for:

- async discovery start and polling
- keyword search update
- detail fetch on row select
- watchlist add/remove refresh
- chat send and reply render

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm test -- --runInBand
```

Expected: FAIL because the page is not wired to the backend yet.

- [ ] **Step 3: Write minimal implementation**

Wire the page to:

- `POST /discovery/run` + polling
- `/products/search`
- `/products/{id}`
- `/watchlist`
- `/watchlist/refresh`
- `/chat`

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm test -- --runInBand
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git -C /tmp/avori-discovery/.worktrees/vercel-frontend add web/src/app/page.tsx web/src/components
git -C /tmp/avori-discovery/.worktrees/vercel-frontend commit -m "Connect frontend to Avori backend workflows"
```

### Task 6: Final deployment verification

**Files:**
- Modify: `README.md`
- Modify: `.env.example`
- Test: `tests/test_api.py`
- Test: `web/package.json`

- [ ] **Step 1: Write the failing verification checks**

Identify the final launch commands:

```bash
/tmp/avori-discovery/.venv/bin/python -m pytest -q
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm test -- --runInBand
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm run build
```

- [ ] **Step 2: Run checks to verify any remaining failures**

Run the commands above before final cleanup.

Expected: any remaining failures reflect unfinished launch work.

- [ ] **Step 3: Write minimal implementation**

Finalize:

- README launch instructions
- env var docs for frontend/backend
- Vercel-ready frontend scripts/config

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
/tmp/avori-discovery/.venv/bin/python -m pytest -q
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm test -- --runInBand
cd /tmp/avori-discovery/.worktrees/vercel-frontend/web && npm run build
```

Expected:

- pytest PASS
- frontend tests PASS
- Next.js build PASS

- [ ] **Step 5: Commit**

```bash
git -C /tmp/avori-discovery/.worktrees/vercel-frontend add README.md .env.example web
git -C /tmp/avori-discovery/.worktrees/vercel-frontend commit -m "Prepare Avori frontend for Vercel launch"
```
