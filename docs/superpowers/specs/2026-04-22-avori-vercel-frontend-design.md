# Avori Vercel Frontend Design

**Date:** 2026-04-22

**Goal:** Replace the Streamlit dashboard as the primary UI with a Vercel-deployed Next.js frontend in the same repo and same Vercel project, while preserving the Python FastAPI backend and implementing the frontend audit requirements.

## Scope

This design covers the first launchable web frontend for Avori Discovery:

- same repo
- same Vercel project
- full workflow
- audit-driven UX changes

Included:

- discovery run + async polling
- keyword search
- candidates table with filters, CSV export, and score explanation
- product detail panel with image, review summary, formatted signals, and TikTok URL
- watchlist tab with velocity/graduation display
- chat panel with natural-language seed prompts
- onboarding empty state
- frontend layout changes required by the audit

Not included in this phase:

- full backend rewrite from Python to TypeScript
- durable hosted database migration beyond the current backend storage model
- authentication and multi-user accounts
- advanced charting beyond the audit-required watchlist trend presentation

## Constraints

- The existing Python FastAPI backend remains the canonical business logic layer for discovery, scoring, watchlist, job status, and product detail.
- The new frontend must be deployable on Vercel.
- The frontend must follow the audit, not simply replicate the Streamlit layout.
- The implementation should minimize risky backend churn unless required to support the launch UI.

## Recommended Approach

Build a Next.js App Router frontend under a new subdirectory in the same repo and make it the deployed interface. Keep the FastAPI backend in the repo and expose it through same-project routes or same-origin API calls so the frontend can use:

- `POST /discovery/run`
- `GET /discovery/jobs/{job_id}`
- `GET /products/search`
- `GET /products/{product_id}`
- `GET /watchlist`
- `POST /watchlist`
- `POST /watchlist/refresh`
- `DELETE /watchlist/{product_id}`

Why this is the right choice:

- It fixes the main product issue: there is currently no proper deployable UI on Vercel.
- It preserves the working Python discovery logic instead of rewriting scoring and TikHub integration for launch.
- It directly supports the audit’s architecture recommendation: deployed UI should consume the API and use the async discovery job pattern.

## Alternatives Considered

### 1. Keep improving Streamlit

Pros:

- fastest local UX changes
- minimal new tooling

Cons:

- does not solve the launch requirement for Vercel
- keeps the product tied to a local dashboard metaphor
- still leaves deployment architecture awkward

Rejected because it fails the primary launch goal.

### 2. Rewrite backend into Next.js APIs/server actions

Pros:

- single stack
- potentially cleaner long-term deploy model

Cons:

- high-risk migration
- duplicates or rewrites Python discovery logic during a frontend rebuild
- too much scope for launch

Rejected for launch due to risk and time.

## Repo Structure

Recommended additions:

- `web/`
  - Next.js app
- `web/src/app/`
  - route segments and layouts
- `web/src/components/`
  - candidates table, filters, detail panel, watchlist panel, chat panel, empty states
- `web/src/lib/`
  - API client, polling helpers, CSV export helpers, score presentation helpers
- `web/src/types/`
  - shared frontend response models
- optional `web/src/app/api/`
  - proxy routes only if needed for deployment consistency

Existing backend stays in place:

- `app.py`
- `agent.py`
- `avori_discovery.py`
- `storage.py`
- `endpoints/`

## Frontend Information Architecture

The launch UI should follow the audit’s structure, not the current Streamlit one.

### Top-level layout

- left sidebar: controls only
  - run discovery
  - keyword search
  - filters
  - score legend/help
- main area:
  - tabs: `Candidates`, `Watchlist`

This addresses the audit item that the watchlist should not live in the sidebar.

### Candidates tab

The `Candidates` tab should have three persistent zones:

1. fixed-height candidates table
2. detail pane
3. chat pane

The table should not push detail below the fold. The intended layout is:

- candidates table in a constrained-height scrollable card
- detail + chat displayed beneath or beside it depending on viewport
- desktop ratio biased toward detail, not 50/50

For desktop:

- table section at the top with internal scroll
- below it, split layout with approximately 70/30 or 65/35 detail/chat emphasis

For mobile:

- table first
- selected product detail next
- chat last

### Watchlist tab

The `Watchlist` tab should become a first-class workspace:

- list or table of tracked products
- velocity as a metric/trend indicator, not plain caption text
- graduated state visible as badge/status
- room for snapshots and future richer trend visualization

## Audit Requirements Mapping

### 1. Watchlist belongs in a tab

Implemented by main-body tabs:

- `Candidates`
- `Watchlist`

### 2. Frontend must use async discovery jobs

The frontend must call:

- `POST /discovery/run`
- then poll `GET /discovery/jobs/{job_id}`

The UI should show explicit expectation-setting text such as:

- “Running discovery — this usually takes around 30 seconds.”

No direct blocking frontend call to a synchronous discovery action.

### 3. Product image must be shown

The detail panel must render `image_url` prominently near the top.

### 4. Score needs explanation

The table/header/filter area should include a visible score legend/help text explaining:

- score combines sales/rating/early-window factors
- early window products receive a bonus
- higher is better

The design should use both:

- raw numeric score
- a visual label/badge such as High / Medium / Low

### 5. Empty state must onboard

If there are no results and no prior discovery file/state, the `Candidates` tab should show:

- a launch CTA
- short explanation of what discovery does
- instruction to run discovery from the sidebar

### 6. Table cannot push detail below fold

The candidates table must be rendered in a fixed-height scrollable region.

### 7. Velocity should be a trend indicator

The watchlist should display velocity with:

- directional indicator
- signed/positive interpretation
- status emphasis

If time permits in launch scope, use a small sparkline-style UI. If not, metric + arrow is sufficient.

### 8. Detail/chat ratio should favor detail

The detail panel gets more width than chat on desktop.

### 9. Review summary should be visible and higher up

The detail panel order should be:

1. image
2. title + metrics
3. review summary
4. categories
5. supplementary signals
6. TikTok link
7. watchlist controls

Review summary should be expanded or visible by default when present.

### 10. CSV export

Filtered candidates must be exportable from the frontend.

### 11. Natural-language chat prompts

The “Discuss in chat” action should generate user-readable natural language prompts, not pipe-delimited developer strings.

## Component Design

### Sidebar Controls

Responsibilities:

- trigger discovery
- trigger keyword search
- adjust filters
- display score help

Should not contain:

- watchlist rows
- dense persistent result content

### Candidates Table

Responsibilities:

- show ranked rows
- allow row selection
- stay visible without pushing the rest of the UI off screen
- export filtered data to CSV

Columns:

- rank
- title
- price
- sold count
- review count
- score
- early window badge
- keyword
- seller

Behavior:

- selected row updates detail pane
- score column has inline legend or table header help

### Detail Panel

Responsibilities:

- show selected product image and core metrics
- prioritize review summary
- render formatted supplementary signals
- expose TikTok URL
- allow add-to-watchlist and discuss-in-chat actions

### Chat Panel

Responsibilities:

- show conversation history
- allow freeform product/research questions
- seed a product-specific natural-language prompt from the selected candidate

### Watchlist Panel

Responsibilities:

- show tracked products
- velocity indicators
- graduated status
- remove actions
- space for future history/trend visuals

## Data Flow

### Discovery flow

1. User clicks `Run Discovery`
2. Frontend posts to `/discovery/run`
3. Backend returns `job_id`
4. Frontend polls `/discovery/jobs/{job_id}`
5. When completed, frontend replaces candidate data with payload result set
6. Detail and watchlist state update off the new dataset

### Search flow

1. User enters keyword
2. Frontend requests `/products/search?keyword=...`
3. Results replace current candidates list

### Detail flow

1. User selects a row
2. Frontend requests `/products/{product_id}` if detail not already cached
3. Detail pane updates

### Watchlist flow

1. User adds item from detail panel
2. Frontend posts to `/watchlist`
3. Watchlist tab refreshes
4. Optional refresh endpoint updates velocity/tracking state

### Chat flow

1. User submits freeform question or clicks discuss
2. Frontend sends a natural-language prompt to a backend chat endpoint or existing agent path
3. Response streams or returns into chat history

Note:

The current backend exposes agent functions but not a dedicated web chat endpoint. Launch implementation will likely require adding a simple chat API route backed by the existing agent/session model. This is in scope because full workflow includes basic chat.

## Backend Changes Required for Frontend Launch

The frontend migration is not purely cosmetic. These backend additions or adjustments are required:

### Required

- add a chat API endpoint suitable for the Next.js frontend
- ensure discovery job payloads contain the fields the UI needs without extra local-file assumptions
- confirm CORS or same-origin routing behavior works under same-project deployment

### Likely useful

- provide a normalized score explanation constant or metadata from the backend
- optionally add a watchlist listing endpoint that returns richer display-ready structures

### Not required immediately

- rewriting discovery logic
- replacing Python storage layer

## Launch UX

The launch UI should feel like a focused operator console, not a generic admin panel.

Desired qualities:

- deliberate visual hierarchy
- clear call-to-action when empty
- research-oriented detail emphasis
- visual recognition via images
- strong table usability
- obvious async state feedback

Recommended style direction:

- clean, product-ops layout
- bold but restrained accent color
- strong typography
- cards/tabs/tables, not dashboard clutter

## Vercel Deployment Design

Same repo, same Vercel project means:

- Next.js frontend becomes the primary deployed application
- Python backend remains part of the repo and must still be callable in production

Two workable deployment shapes:

### Recommended

Use Next.js as the root deployed app and proxy frontend API requests to the Python backend path exposed in the same project or through Vercel routing.

### Fallback

If same-project mixed runtime routing proves awkward, keep same repo but deploy only the Next.js app from Vercel and point it at a separately hosted Python API. This is a fallback only, not the target.

## Testing Strategy

### Frontend tests

- data polling helper tests
- score label/legend mapping tests
- CSV export helper tests
- detail/watchlist rendering tests
- empty-state tests

### Integration tests

- discovery start + polling success
- keyword search result rendering
- watchlist add/remove refresh
- product detail fetch and rendering
- discuss-in-chat prompt formatting

### Manual verification

- desktop and mobile layout
- long watchlist scaling
- no-results onboarding path
- image rendering
- CSV download
- async discovery loading states

## Risks

### 1. Same-project mixed-runtime deployment complexity

Risk:

- Next.js + Python in one Vercel project can require careful routing behavior

Mitigation:

- keep backend entrypoints stable
- test deployment shape early before polishing UI details

### 2. Chat endpoint gap

Risk:

- there is no clean browser-facing chat API yet

Mitigation:

- add a narrow backend chat endpoint that reuses the existing agent/session logic

### 3. Over-scoping the frontend rewrite

Risk:

- trying to over-perfect the launch UI delays shipping

Mitigation:

- build exactly what the audit requires for launch
- avoid extra product surfaces

## Recommendation

Proceed with a Next.js frontend inside the same repo, deployed as the primary Vercel UI, backed by the existing FastAPI service. Implement the audit items as launch requirements, not backlog ideas. Keep Streamlit out of the deployment path.
