# MechSense — Implementation Plan

Plan derived from `prompt.md` (master project spec). This file tracks the agreed scope, stack, phases, and verification gates.

## 1. Agreed Scope Decisions

| Topic | Decision |
|---|---|
| Authentication | **None.** Single-user demo/portfolio app (spec makes auth optional). |
| Anomaly detection | **Phases 1 + 2 only:** rule-based thresholds + rolling statistical detector. Isolation Forest (Phase 3) documented as a future extension per spec's final instructions. |
| Deployment | Dockerfiles, `docker-compose.yml`, and GitHub Actions written as deliverables. Only **local run is verified** (Docker is not installed on this machine; no untested cloud claims). |
| Build pacing | **Incremental phases with a checkpoint** after each before continuing. |

## 2. Environment (verified at plan time)

- Node 24.12.0 / npm 11.19.1
- Python 3.12.3 with `uv`
- PostgreSQL 16 running locally; OS role `shahbaz` has CREATEDB → databases `mechsense` (dev) and `mechsense_test` (tests)
- No passwordless sudo → all installs at user level (npm / uv)
- Repository initially contained only `prompt.md`

## 3. Technology Stack

### Frontend
- Vite + React 19 + TypeScript
- Tailwind CSS **v4** via `@tailwindcss/vite` (CSS-based `@theme`, no `tailwind.config.js`)
- shadcn/ui initialized with `npx shadcn@latest init -t vite` (new-york style, OKLCH tokens)
  - Chart component ships on **Recharts v3** — use `var(--chart-1)` (not `hsl(var(--chart-1))`)
- TanStack Query v5 (server state), TanStack Table v9 (grids)
- React Hook Form + Zod (forms/validation)
- `motion/react` (subtle transitions, reduced-motion aware)
- date-fns, Sonner (toasts), React Router v7 (library mode), Lucide React
- cmdk (command palette, comes with shadcn)
- Vitest + React Testing Library + MSW (frontend tests)
- ESLint + Prettier

Exact versions pinned at install time after checking peer dependencies; lockfiles committed.

### Backend (Python 3.12, managed by `uv`)
- FastAPI + Pydantic v2
- **SQLAlchemy 2.x (sync)** + psycopg driver
  - *Rationale:* pandas/NumPy processing is sync; sync sessions run in FastAPI's threadpool; simpler and easier to test than async. Recorded as an "Engineering Decision."
- Alembic migrations against PostgreSQL 16
- pandas + NumPy (simulation, CSV import, statistics)
- pytest + httpx (`ASGITransport`) for API tests
- Ruff for lint + format
- scikit-learn **not** installed (ML phase deferred)

### DevOps
- `.env.example` (no real secrets), `.gitignore`
- Dockerfiles (backend, frontend) + `docker-compose.yml` (Postgres + API + web) — written, not executed locally
- GitHub Actions workflow: backend lint/test, frontend lint/typecheck/test/build

## 4. Project Structure

```
mechsense/
  frontend/
    src/
      components/          # shared UI (shadcn + app-level composites)
      features/
        dashboard/ machines/ sensors/ anomalies/
        maintenance/ imports/ analytics/
      hooks/ lib/ routes/ types/ test/
    public/
    Dockerfile
    package.json
  backend/
    app/
      api/v1/              # routers: health, dashboard, machines, readings,
                           # anomalies, maintenance, imports, analytics,
                           # simulation, configuration
      core/                # config, logging, exceptions
      db/                  # engine, session, base
      models/              # SQLAlchemy models
      schemas/             # Pydantic request/response
      services/            # business logic
      repositories/        # query layer where useful
      detection/           # threshold + statistical engines (testable units)
      simulation/          # deterministic synthetic data generator
      utils/
      main.py
    migrations/            # Alembic
    tests/
    scripts/               # seed.py, sample CSV generator
    Dockerfile
    pyproject.toml
  docs/
    architecture.md api.md data-dictionary.md
    anomaly-detection.md deployment.md
  docker-compose.yml
  .env.example
  .gitignore
  README.md
  plan.md                  # this file
  prompt.md                # original spec
```

Detection and simulation logic lives **outside** route handlers so it can be unit-tested independently (spec §13).

## 5. Data Model (minimum)

1. **Machine** — id, unique identifier, name, type, location, manufacturer, model, install date, operating status, description, thresholds JSON, timestamps. Deactivation keeps history (no hard delete).
2. **SensorReading** — id, machine FK, timezone-aware timestamp, vibration_rms, temperature, rpm, load_pct, nullable pressure, source (`simulated`/`imported`), quality metadata. Indexes: `(machine_id, timestamp)`.
3. **AnomalyEvent** — machine FK, metric, observed value, threshold/baseline used, severity, method, detection time, reading FK, explanation, status (`open`/`acknowledged`/`resolved`), separate ack/resolve timestamps + notes. Indexes: `(machine_id, created_at)`, `(status, severity)`.
4. **MaintenanceWorkOrder** — machine FK, title, description, type, priority, status, scheduled/start/completion timestamps, technician, findings, actions taken; M:N links to anomaly events. Index: `(status, scheduled_date)`.
5. **DataImportJob** — filename, counts accepted/rejected, error summary, timestamps.
6. **DetectionRun** (optional) — records statistical-detection runs/parameters.

## 6. Phase Breakdown & Checkpoints

### Phase 1 — Scaffold & plan *(checkpoint: both apps boot)*
- Monorepo directories, `.gitignore`, `.env.example`
- `uv` project + `pyproject.toml`; Vite React-TS app
- Create `mechsense` and `mechsense_test` databases; verify connectivity
- Ruff, ESLint, Prettier configs
- Verify shadcn CLI + npm registry access
- Deliverables: dependency list + short architecture note (spec §21)

### Phase 2 — Backend foundation *(checkpoint: `pytest` green, API serves)*
- All models + relationships + indexes + constraints
- `alembic upgrade head` initial migration on dev DB
- Deterministic, re-runnable seed (`scripts/seed.py`):
  - 5 demo machines (P-101, M-204, F-301, C-401, B-501), labeled simulated
  - ≥7 days history, ~12 readings/hour, seeded RNG
  - Correlated signals: normal ops, shutdowns, gradual drift, spikes, sensor noise, injected abnormal events
- **Threshold detector** implemented here (seeded anomaly events require it) with dedup/open-event grouping
- Endpoints: health, machines CRUD, readings queries (date/machine filters, pagination), dashboard summary
- Consistent error envelope, status codes, OpenAPI; no DB models exposed
- pytest: machine CRUD, reading filters, invalid input, threshold boundaries, seed idempotency

### Phase 3 — Frontend foundation *(checkpoint: shell + dashboard show real API data)*
- shadcn init; industrial theme: deep navy/charcoal base, teal accents, green/amber/red status, polished light mode, OKLCH tokens
- App shell: sidebar (identity, active-route indicator, collapse), header (title/breadcrumbs, search, theme toggle, notifications, profile menu, quick actions), command palette with keyboard support
- API client module, typed responses, query keys, shared hooks
- Shared states: skeletons, error cards, empty states
- Overview page: summary metrics, machine health table, recent anomalies, latest activity — all sourced from `/api/v1/dashboard/summary` etc.

### Phase 4 — End-to-end features *(checkpoint: complete engineer workflow works)*
- **Machines:** list w/ search + type/status filters + sort + pagination; create/edit; thresholds config; deactivate; detail page (current readings, latest alert, maintenance history)
- **Sensor explorer / machine detail charts:** Recharts v3 via shadcn chart; selectable metrics, time ranges, tooltips, threshold + anomaly markers, per-unit axes (never shared incompatible scales), missing-data handling, CSV export; engineering-context copy with clear disclaimers (not safety limits)
- **Anomaly events:** search, severity/machine/sensor/date filters, sort/pagination, detail view, acknowledge vs resolve (separate timestamps), notes, links to machine + reading
- **Maintenance:** CRUD, schedule, statuses (open/in-progress/completed), technician, priority, link work orders to anomaly events; overdue/upcoming surfaced on dashboard
- **CSV import:** select → preview headers/rows → column mapping → validate (timestamps, required cols, numerics, ranges, duplicates) with row-numbered errors → atomic import → accepted/rejected counts → import history; size/row limits; content validation; downloadable sample CSV; tz-aware convention documented
- **Simulation:** `POST /api/v1/simulation/step` (generate → persist → detect → event → notify), `POST /api/v1/demo/generate`, live-toggle polling that stops when disabled/page inactive, duplicate-process guard
- **Analytics:** trends endpoint + page; every chart shows real backend data

### Phase 5 — Statistical detection *(checkpoint: tests prove behavior)*
- Rolling robust z-score (median/MAD) detector
- Min-observation requirements, zero-variance + missing-value handling
- Explanation strings; statistical anomalies distinguished from threshold violations
- Unit tests: detection logic, duplicate suppression, boundary cases
- Methodology documented in `docs/anomaly-detection.md`

### Phase 6 — Quality & delivery *(checkpoint: all gates pass)*
- Run and **fix** (never disable) all gates:
  ```
  uv run ruff check . && uv run ruff format --check .
  uv run pytest
  cd frontend && npm run lint && npm run typecheck && npm test && npm run build
  alembic upgrade head from a clean database
  ```
- Dockerfiles + `docker-compose.yml` (Postgres w/ persistence, startup order, healthchecks) — flagged **unverified locally**
- `.env.example`, migration + seed commands documented
- GitHub Actions workflow
- README: what it does, engineering problem, features, screenshots, stack, architecture diagram, ERD, sensor model/units, detection methodology, run/test commands, API docs, CSV format, Docker, deployment path, **Engineering Decisions**, recruiter demo walkthrough, limitations — no fabricated metrics
- `docs/` set complete
- Optional stretch: Playwright critical-path E2E (generate readings → open machine → inspect/acknowledge anomaly → create work order → verify persistence); skipped with a note if browser download fails

## 7. Risks & Fallbacks

| Risk | Fallback |
|---|---|
| shadcn/Recharts API drift | Pin exact versions at install; confirm with `npm ls` |
| No Docker daemon | Ship compose/Dockerfile artifacts; document as unverified; app runs locally on Postgres 16 |
| Playwright browser download blocked | E2E optional per spec; document skip reason |
| shadcn registry/network unavailable at install | Fall back to manual component setup per official docs |

## 8. Final Acceptance Gate

Map to spec §22: frontend↔backend connected; Postgres persists all entities; seed reproducible; dashboard shows real aggregates; charts correct units/timestamps; machine CRUD end-to-end; threshold + statistical detection tested; ack/resolve persist; work orders create/update; CSV validation reports errors; simulation creates readings + triggers detection; polished responsive shadcn UI with all states; tests pass; Docker/migration docs; complete README; **no fake frontend state or decorative buttons**.

## 9. Progress Log

- [x] Phase 1 — Scaffold & plan
- [x] Phase 2 — Backend foundation
- [x] Phase 3 — Frontend foundation *(completed — see §13)*
- [ ] Phase 4 — End-to-end features
- [ ] Phase 5 — Statistical detection
- [ ] Phase 6 — Quality & delivery

## 10. Phase 1 Results (completed)

### Verified boot (checkpoint passed)
- Backend: `uv run uvicorn app.main:app` → `/health` 200, `/openapi.json` 200, `/docs` 200, CORS header for `http://localhost:5173`
- Frontend: `npm run dev` → `http://localhost:5173/` 200 (Vite 8, React 19, TS 6)
- Databases created: `mechsense`, `mechsense_test` (role `shahbaz`)
- Gates at end of Phase 1: `ruff check` ✔ · `ruff format --check` ✔ · `eslint` ✔ (0 errors) · `tsc -b` ✔ · `vite build` ✔ · `npm audit` **0 vulnerabilities**

### Actual dependency list (installed & resolved)

**Backend (`uv`, Python 3.12):** fastapi 0.143.1 · uvicorn 0.54.0 · pydantic 2.14.1 · pydantic-settings 2.16.0 · SQLAlchemy 2.1.4 · psycopg 3.3.6 · alembic 1.20.0 · pandas 2.3.3 · numpy 2.5.4 · python-dateutil 2.9 · dev: pytest 8.4.2 · pytest-cov 6.3.0 · httpx 0.28.1 · ruff 0.17.0

**Frontend (npm):** react 19.2 · vite 8.3 · typescript ~6.0 · tailwindcss 4.3 + @tailwindcss/vite · shadcn/ui v4.21.5 (radix-nova style, Lucide, Geist) · lucide-react 1.57 · radix-ui 1.8 (unified) · react-router 8.4 · @tanstack/react-query 5.104 · @tanstack/react-table 9.3 · react-hook-form 7.90 · zod 4.6 · @hookform/resolvers 5.9 · motion 14.2 · date-fns 4.4 · sonner 2.0 · dev: eslint 10 + typescript-eslint 8.7 · prettier 3.9 · vitest/RTL/MSW (added in test phase)

### Key setup decisions made during Phase 1
1. **shadcn v4 quirks:** CLI flags changed (`-b` = component base library, not color; presets: nova/vega/…). Initialized with `-t vite -b radix -p nova`.
2. **Vendored `shadcn/tailwind.css`** → `frontend/src/styles/shadcn.css` (with sync instructions in header comment). The `shadcn` npm package (added automatically by init) pulls 7 high-severity audit findings via its CLI tooling (braces/micromatch DoS) and is a CLI, not a runtime lib — removed; app builds clean with 0 vulnerabilities.
3. **oxlint (new create-vite default) replaced with ESLint 10 flat config + Prettier** per spec §2.
4. **`cors_origins` uses `NoDecode`** — pydantic-settings JSON-parses list fields from dotenv; NoDecode keeps the documented comma-separated `.env` format working.
5. **Vite dev proxy** forwards `/api` → `127.0.0.1:8000` (frontend `.env` uses `VITE_API_BASE_URL=/api/v1`, same-origin in dev; no CORS needed in the browser flow).
6. **Git note:** the repo root is the parent `Projects to upload to github/` folder with unrelated pre-existing files/history — all MechSense work stays uncommitted unless explicitly requested.


## 11. Phase 2 Results (completed)

### Checkpoint passed
- `uv run pytest` green: **80 tests** across 8 files (thresholds, detection service, generator, machines/readings/anomalies/dashboard APIs, seed)
- `ruff check` ✔ · `ruff format --check` ✔ · API serves every Phase-2 endpoint of the §13 contract
- Migrations: 3 revisions applied (`1a9dda654cff` initial → `7a58f7b51dfd` unique reading index → `b3f1c0d24e88` `live` enum value)

### Final API surface (Phase 2 scope)
- `GET /health`
- `GET /api/v1/dashboard/summary?period=1h|6h|24h|7d|30d`
- `GET|POST /api/v1/machines` · `GET|PATCH /api/v1/machines/{id}`
- `GET|POST /api/v1/readings` · `GET /api/v1/machines/{id}/readings`
- `GET /api/v1/anomalies` · `GET /api/v1/anomalies/{id}` · `POST .../acknowledge` · `POST .../resolve`

### Contract decisions documented
1. **Pagination params:** `page` + `page_size` (max from settings); list responses are `Page[MachineSummary]` (health-enriched rows), detail/create/update stay `MachineRead`.
2. **Health filter:** `GET /machines?health=healthy|warning|critical|inactive|no_data` — SQL mirror of `services.machines.compute_health` (LATERAL latest reading + open-event EXISTS + threshold CASE) so pagination stays correct; a test asserts SQL results equal the Python-derived `health_status` column.
3. **`POST /readings`** added (not in the spec's starting list) as the single ingestion write path — CSV import and `/simulation/step` will reuse `services.readings.ingest_reading`. Duplicate `(machine_id, timestamp)` → 409; naive timestamps interpreted as UTC; response includes `affected_anomaly_ids`.
4. **Lifecycle:** acknowledge is idempotent while acknowledged, 409 after resolve (`invalid_state`); resolve is idempotent (updates notes); resolve-from-open keeps `acknowledged_at` null.
5. **Reading uniqueness enforced** at DB level (`uq_sensor_readings_machine_ts`) — DISTINCT ON ties were previously nondeterministic.

### Detection/seed outcomes
- Seeded dataset: 5 machines × 2,017 readings (10,085 rows, 7 days @ 5 min, seeded RNG) + 3 work orders
- Exactly **5 designed events** (one per condition): P-101 vibration + temperature escalated warning→critical in place (vibration leads temperature), C-401 pressure + vibration critical spike (single point), B-501 warning-only elevation; F-301/M-204 healthy
- Re-run without `--force` is a no-op; `--force` clears and rebuilds (both covered by tests)
- Acknowledgment ≠ resolution semantics encoded in tests

### Bugs found & fixed during Phase 2 smoke/tests
1. **`autoflush=False` hid pending events** from `active_event` → duplicate events, no escalation. Fixed: `db.flush()` after event insert in `detection.service.process_reading` (batch-safe).
2. **Pydantic `from_attributes` missing** on `AnomalyMachineRef`/`AnomalyReadingRef` → all anomaly endpoints 500.
3. **Deprecated `select.distinct(col)`** (DISTINCT ON) raised `SADeprecationWarning` (escalated to error by pytest `filterwarnings`) → migrated to `select.ext(distinct_on(...))` (SQLAlchemy 2.1).
4. **Session timezone:** engine now sets `TimeZone=UTC` — all timestamps serialize `+00:00`/`Z`.
5. **Generator margin tuning** so demo data can't flap thresholds diurnally: C-401 operating margins widened, spike amplitudes sized to cross critical at any load phase, P-101 fault temperature extra raised (vibration still leads temperature).

### Test suite notes
- `tests/conftest.py`: session-scoped engine on `TEST_DATABASE_URL`, function-scoped `drop_all`/`create_all` (order-independent), FastAPI `dependency_overrides[get_db]` + `TestClient`, factories (`create_machine`, `ingest`, `add_reading`)
- Seed tests use a fixed anchor (`2026-01-16T13:00Z`) for reproducibility; work-order dates relative to real today keep overdue/upcoming assertions stable

## 12. Phase 3 — Frontend foundation (COMPLETED — results in §13)

### Completed
**Design flow (impeccable skill):**
- `PRODUCT.md` created at project root — inferred from `prompt.md` (the explicit brief) per the user's "continue" instruction; every inferred fact labeled. Platform: web; no Stack section needed (codebase answers it).
- Surface brief committed: `.impeccable/surfaces/frontend-src-app-tsx.md` (primary `frontend/src/App.tsx`, related `frontend/src/pages/Overview.tsx`) with the six-block **Direction contract** (THESIS / OWN-WORLD / STORY / FIRST VIEWPORT / FORM / SIGNATURE / FINISH).
  - Mode: **Operate**, execution: **code-led** (no image generation → code-first only path; app screens are code-first regardless).
  - World: **established/inherited** — brief-pinned industrial navy/teal from Phase-1 OKLCH tokens in `index.css`; no concept-seed roll (brief-pinned layout: persistent sidebar per spec §4). `seed: none (unavailable)`.
  - **Signature move: "threshold horizon"** — every sensor chart draws the machine's real warning/critical limits as dashed rules with tinted bands and shades detected anomaly intervals as vertical columns.
- Finish flow still owed at Phase 3d: batched screenshots (desktop+mobile) → `impeccable detect --json` → finish reviewer subagent → documenter (DESIGN.md + `.impeccable/design.json`).

**shadcn / tooling:**
- 27 UI components added via `npx shadcn add` (card, badge, skeleton, tabs, select, dropdown-menu, tooltip, separator, input, table, command, switch, popover, dialog, sheet, alert, breadcrumb, sonner, checkbox, label, alert-dialog, sidebar, chart, form, scroll-area, input-group, textarea) + **recharts** + cmdk + next-themes. `frontend/package.json` now 22 deps.
- `tsconfig.app.json` fixed: added `paths {"@/*": ["./src/*"]}` (root-solution `paths` don't apply under `tsc -b`) and **`strict: true`**; removed deprecated `baseUrl` (TS 6 deprecation) from both configs. `tsc -b` green afterwards, including all vendored shadcn code.
- Vendored `src/hooks/use-mobile.ts` rewritten with `useSyncExternalStore` (shadcn's original tripped `react-hooks/set-state-in-effect`).

**Code written (all type-checked green before the final micro-refactor):**
- `src/api/types.ts` — mirrors backend Pydantic schemas exactly (Page, MachineSummary/MachineRead, ReadingRead, AnomalyRead, Dashboard*, enums).
- `src/api/client.ts` — `ApiError` from the `{error:{code,message,details}}` envelope, `buildQuery`, `fetchAllPages` (up to 6×500 rows for the 7-day chart window), network-error copy names the recovery (backend on :8000).
- `src/api/queries.ts` — query keys + `useDashboard` (60s refetch), `useMachines`, `useMachine`, `useMachineReadings` (trailing 1h/6h/24h/7d windows), `useAnomalies`, `useAnomaly`.
- Entry: `main.tsx` (QueryClient retry policy: no retry on 4xx; next-themes default **dark**; TooltipProvider; Sonner Toaster), `index.html` (real title/description, anti-FOUC theme script, new pulse-mark `public/favicon.svg`), old Vite scaffold (`App.tsx`, `App.css`, assets) deleted.
- Shell: `components/layout/nav.ts` (8 items / 3 groups: Monitor, Assets, System), `site-sidebar.tsx` (shadcn inset Sidebar, collapsible icon rail, wordmark, live alert-count badge on Anomaly Events from the dashboard query, demo-engineer footer), `app-header.tsx` (breadcrumb `h1`, ⌘K search button, quick-actions menu navigating to real routes, alert bell dropdown with top-5 open anomalies, theme toggle, profile menu), `command-palette.tsx` (pages + live machine search + actions; fetch enabled only when open), `app-shell.tsx` (SidebarProvider, Ctrl/⌘K toggle, 1440px content column).
- Routes (`routes.tsx`): Overview real; `/machines`, `/machines/:id`, `/explorer`, `/anomalies`, `/maintenance`, `/import`, `/analytics`, `/settings` are honest `PageStub`s listing their Phase-4/5 scope; index + `*` redirect to `/overview`.
- Overview (real API data): `PeriodControl` (1h/6h/24h/7d/30d), `MetricStrip` (6 cells in a hairline grid — only the anomalies cell shows a period delta, computed from `anomalies_period.current/previous`; no fake trends), `MachineHealthTable` (severity-sorted, `HealthChip`, open-alert count badges, vibration/temp with units, last-reading age, rows link to machine detail), `RecentAnomalies` (6 latest events: severity chip, value vs limit, status chip, relative time), `SensorTrendChart` — **threshold horizon**: machine Select (defaults to worst-health machine), metric tabs (Pressure only when configured), range tabs (24h one request; 7d follows ≤6 pages), tinted warning/critical `ReferenceArea` bands + dashed limit `ReferenceLine`s + anomaly interval shading, custom tooltip with units, `isAnimationActive={false}`, per-metric decimals.
- Shared: `components/domain/chips.tsx` (Health/Severity/AnomalyStatus chips), `components/feedback.tsx` (ErrorState with recovery copy + retry, EmptyState, skeletons), `lib/format.ts` (METRIC_META units/decimals, health rank/order, relative time), `lib/route-meta.ts`.

### PAUSE POINT — exact state & remaining steps
**Last edits were NOT re-verified** (session paused for power-off). Two known issues to fix first:

1. `src/components/overview/sensor-trend-chart.tsx` line 1: `useEffect` is imported but both effects were removed in the purity refactor → remove it from the import (would fail `tsc` `noUnusedLocals`).
2. Same file, anomaly `ReferenceArea` (~line 290): `x2={new Date(event.resolved_at ?? window?.end ?? Date.now()).getTime()}` — `Date.now()` trips `react-hooks/purity`. Fix with data already in scope (no impure calls in render):
   ```tsx
   x2={event.resolved_at ? new Date(event.resolved_at).getTime() : (windowEndMs ?? points.at(-1)?.t ?? 0)}
   ```
   (`windowEndMs` is already defined in the component.)

**Then, in order (Phase 3d):**
1. Unexport `errorMessage` from `components/feedback.tsx` (keep local — fixes its `react-refresh` warning; no external users).
2. Move `PERIOD_LABEL` from `components/overview/period-control.tsx` to `src/lib/format.ts` (fixes its warning; update imports in `period-control.tsx`, `metric-strip.tsx`, `pages/Overview.tsx`).
3. `eslint.config.js`: add vendored shadcn exports to `allowExportNames`: `'badgeVariants', 'tabsListVariants', 'useSidebar'` (alongside existing `'buttonVariants'`).
4. Gates: `npx prettier --write .` (38 files pending) → `npx tsc -b --force` → `npx eslint .` (target 0 errors / 0 warnings) → `npm run build`.
5. Boot: backend (`uv run uvicorn app.main:app --port 8000`, setsid pattern — `/tmp/opencode/uvicorn.pid`, currently PID 70599 running + seeded DB) and `npm run dev` in `frontend/`; open `/overview` and verify real data renders (metric counts 5/2/3/5, P-101 critical rows, 5-event feed, threshold horizon on P-101 vibration). Browser check via agent-browser skill: desktop 1440 + mobile 390 screenshots into `.impeccable/review/`.
6. Impeccable finish: `impeccable detect --json` on changed targets → finish reviewer subagent → documenter (DESIGN.md).
7. Write plan.md **§13 Phase 3 Results** and tick the progress log.

### Design/contract notes for later phases
- Chart ranges are capped at 7d on Overview (page_size max 500 ⇒ 6 pages); wide-range aggregation belongs to Phase 4 Sensor Explorer (`/readings` has no `metric` param — frontend selects the column; no aggregate endpoint yet).
- Sidebar alert badge uses `useDashboard('24h')` as its stable key (active_alerts is period-independent) — Overview's period-scoped query is a separate cache entry by design.
- `react-router` v8 unified package is imported directly (`react-router-dom` not installed).
- Dark default justified by use scene (24/7 control-room monitoring); light mode available via toggle; anti-FOUC script in `index.html`.

## 13. Phase 3 Results (completed)

### Pause-point fixes (both confirmed present, then fixed)
1. `sensor-trend-chart.tsx`: removed unused `useEffect` import (would have failed `noUnusedLocals`).
2. `sensor-trend-chart.tsx` anomaly `ReferenceArea`: replaced impure `Date.now()` (react-hooks/purity) with data already in scope — `event.resolved_at ? … : (windowEndMs ?? points.at(-1)?.t ?? 0)`.

### Cleanups (all three confirmed pending, then fixed)
- `errorMessage` unexported from `components/feedback.tsx` (local-only; fixed its `react-refresh` warning).
- `PERIOD_LABEL` moved from `period-control.tsx` → `src/lib/format.ts`; importers updated (`metric-strip.tsx`, `pages/Overview.tsx`).
- `eslint.config.js` `allowExportNames` extended with `badgeVariants`, `tabsListVariants`, `useSidebar`.

### Final gates (all green, run after every change batch)
- `npx prettier --check .` ✔ · `npx tsc -b --force` ✔ · `npx eslint .` ✔ (**0 errors, 0 warnings**) · `npm run build` ✔ (6.1s; only the informational >500 kB chunk notice — single-bundle SPA, code-splitting deferred)

### Live verification (browser: agent-browser, session-scoped, `--no-sandbox`)
- Backend `uv run uvicorn` on :8000 (setsid, `/tmp/opencode/uvicorn.pid`) + Vite :5173 with `/api` proxy; API proxy verified via curl before browser use.
- **Seed refreshed:** dev DB data was 2 days stale (24h chart window empty on first load) → re-ran `uv run python -m scripts.seed --force` → 10,085 readings regenerated, newest at current hour, still exactly 5 designed events. (Anchor = `datetime.now(UTC)` in `services/seeding.py`; seeded RNG keeps scenarios deterministic.)
- Overview renders real data end-to-end: metric strip **5 / 2 / 3 / 5** (+5 anomalies delta, 1 overdue / 1 upcoming), fleet-health table with C-401 + P-101 Critical, B-501 Warning, F-301/M-204 Healthy, 5-event feed with value-vs-limit lines, last-reading ages live.
- Threshold horizon verified on P-101 vibration: dashed `warn 4.50` + `crit 7.10` rules, tinted bands, drift crossing into critical, footnote `P-101 · Pump · last 24h · 273 readings`.
- Empty-state path also exercised pre-reseed (honest "No readings in this window" copy) — states behave.

### Impeccable finish flow
1. `impeccable context` loaded (PRODUCT.md + surface brief); `detect --json` on changed source files → **0 findings**.
2. `detect --json` on live `/overview` → **13 warnings** (tiny-text ×4, undersized-ui-text ×2, low-contrast ×2, nested-cards ×4, flat-type-hierarchy ×1).
3. **Finish reviewer** batched fixes in one pass:
   - New `--destructive-fill: oklch(0.55 0.195 25)` token (light + dark) for count badges → contrast 2.9:1 → **4.98:1 dark / 5.11:1 light**; applied to bell badge + sidebar alert badge.
   - Page `h1` 14→20px (`text-xl`) → role steps now 14→16→20, largest adjacent step 1.25:1 (target met).
   - All 11px tertiary text → 12px (metric-strip contexts, chart footnote, table unit suffixes, anomaly timestamps, sidebar tagline); 10px footer/avatar text → 12px, footer button `size="lg"`, avatar box grown.
   - nested-cards ×4 triaged as **false positives** (DOM trace: single card-like ancestor = the SidebarInset shell wrapper; no `Card` inside `Card`) — structure kept, reason recorded.
4. Re-detect on live page: **4 findings, all the nested-cards false positives**; zero low-contrast / undersized / tiny-text / flat-hierarchy. Gates re-run: prettier/tsc/eslint all 0.
5. Screenshots (desktop 1440, mobile 390, P-101 threshold horizon) in `.impeccable/review/`; layout, theme, and hierarchy verified post-fix at both widths.
6. **Documenter:** `DESIGN.md` (root) — Stitch spec frontmatter (15 real colors, type, radius, spacing; dark values canonical, keys ⊆ schema) + 8 canonical sections; `.impeccable/design.json` sidecar (schemaVersion 2) with tonal meta, real transition/breakpoint extensions, 10 self-contained `ds-*` components incl. the signature **Threshold Horizon**, and narrative (North Star: **"The Control Room Console"**; voice: instrument-panel precision; components: restrained & instrumental — user-confirmed). Both parse; no other files touched.

### Phase 3 → Phase 4 handoff notes
- The eight non-Overview routes remain honest `PageStub`s — Phase 4 replaces them (machines list/detail, sensor explorer, anomalies, maintenance, CSV import, analytics; settings can stay scoped-stub).
- `/readings` has no `metric`/aggregate param — Sensor Explorer wide-range aggregation may need a backend endpoint (decide in Phase 4 planning).
- Refresh pattern for demos: `uv run python -m scripts.seed --force` regenerates data ending at the current hour.

## 14. Phase 4 — Sub-checkpoint 4a Results (backend API completion)

Phase 4 is split into five approved sub-checkpoints; user gives "go" at each: **4a backend API** ✅ → 4b–4e frontend features (machines list/detail + charts, anomalies, maintenance, import wizard, analytics/settings pages) → final Phase-4 gates.

### 4a delivered (all spec §13 contract paths now exist — 21 OpenAPI paths)

| Area | What shipped | Tests |
|---|---|---|
| Anomalies (gap-fill) | `q` search (explanation/identifier/name ILIKE) + `sort` (`detected_at\|severity\|metric\|observed_value\|status`; severity CASE-ordered so desc = critical first) | 17 in `test_api_anomalies.py` |
| Dashboard activity | `GET /dashboard/activity` — merged events/acks/resolves + imports + work-order lifecycle, desc, capped (was §5E gap folded into Phase 4) | 8 in `test_api_dashboard.py` |
| Maintenance | Full `/maintenance` CRUD: machine/status/priority/type + `overdue`/`upcoming` filters, sort map, `WO-%04d` numbering, lifecycle 409 `invalid_state` (terminal = completed/cancelled), same-status PATCH idempotent field update, anomaly linking (404 missing / 422 other-machine), 404 machine, 422 title, pagination | 11 in `test_api_maintenance.py` |
| CSV imports | `POST /imports/preview` (headers, 5 sample rows, synonym-based mapping candidates), `POST /imports/csv?dry_run=` (row-numbered validation: timestamp/numeric/range/in-file+DB duplicates, blank optional pressure OK; one transaction for job+readings+detection — rollback = no partial imports), `GET /imports` + `/imports/{id}` (history, mapping, errors, `errors_truncated`); hard limits 422 (size/rows/empty/unparseable/missing-mapping); **`python-multipart` added** (uv); sample asset `frontend/public/sample-sensor-data.csv` | 9 in `test_api_imports.py` |
| Simulation | `POST /simulation/step` (generate→persist→detect→event via single write path; inactive = 409; timestamps anchored `max(last+5min, now)` — rapid clicks advance simulated time, not wall µs), `POST /demo/generate` (fleet-or-one, skipped-inactive report, atomic batch, `simulation_max_batch` guard → 422, IntegrityError → 409 retry); `READ_INTERVAL` moved to `simulation/generator.py` (seeding re-exports) | 8 in `test_api_simulation.py` |
| Analytics | `GET /analytics/trends` — SQL-side equal-width buckets (floor(epoch/start)), per-machine series + fleet summary incl. **`percentile_cont(0.95)` p95**; metric+unit map, `machine_id`/`start`/`end`/`buckets(2..500)` filters, naive=UTC, empty window = zero summary, NULL pressure excluded | 6 in `test_api_analytics.py` |
| Configuration | `GET /configuration` — read-only public settings (pagination, import limits, simulation seed/batch/interval); **never** db URLs/credentials/cors/log | 2 in `test_api_configuration.py` |

### 4a gates (verified)
`uv run ruff check .` ✔ · `uv run ruff format --check .` ✔ · `uv run pytest` → **124 passed** (80 at Phase-3 end + 44 new). Live uvicorn restart smoke: `/health`, `/configuration`, `/analytics/trends` (real P-101 data, p95 9.95 mm/s), `/imports`, `POST /simulation/step` → reading 40345 + anomaly 146 (detection chain live) ✔.

### Decisions worth keeping
- Import = row-level accepted/rejected (not all-or-nothing), but the accepted set commits **atomically** with its job + detection — matches spec "accepted or rejected" + "avoid partial imports".
- Step timestamps: `max(last + READ_INTERVAL, now)` → stale machines jump to present, current machines continue the 5-min grid deterministically (no µs pileups from polling).
- Trends live at `/analytics/trends` (spec §13 starting contract); `/readings` stays a raw row endpoint — the Phase-3 handoff note above is resolved.
- No Alembic changes in 4a (models/tables all existed from Phase 2 migrations).

### Next: 4b–4e (frontend)
4b machines list/detail + sensor explorer charts → 4c anomalies UI → 4d maintenance + import wizard → 4e analytics + settings (+ demo controls), gates after each.

## 15. Phase 4 — Sub-checkpoint 4b Results (machines + explorer frontend)

Three stubs replaced with real pages; gates green; live-verified in the browser (agent-browser session, `--no-sandbox`).

### 4b delivered

| Page / piece | What shipped |
|---|---|
| `/machines` (`Machines.tsx`) | Debounced search + status/health/equipment filters + sort (5 keys) + asc/desc, paginated table (25/page) with health/status chips, vibration/temperature snapshot, open-anomaly badges, last reading, latest alert, per-row links; empty/error/loading states; honors `?create=1` from the Quick-actions header |
| `machines/*` components | `machine-filters.tsx` (debounce keeps latest filters via ref so a mid-timer status change isn't clobbered; Reset clears draft inline — no setState-in-effect), `machines-table.tsx`, `machine-form-dialog.tsx` (shared create/edit, RHF+zod, identifier regex, API `details[]` → field errors, `conflict` → identifier error), `thresholds-dialog.tsx` (5 metrics × warning/critical, full-replace payload, critical>warning cross-field error, float32 noise trimmed for display) |
| `/machines/:id` (`MachineDetail.tsx`) | Identity header + Edit / Thresholds / Deactivate-or-Activate (AlertDialog confirm via `PATCH {status}`); current-readings strip (5 metrics, pressure "not sensed" when null) with **Simulate reading** button (`POST /simulation/step` → toast; anomaly ids → warning toast); `MetricChart fixedMachineId` (raw ranges, no machine select); latest-alert card (severity/status chips, metric vs threshold, explanation, link `?machine_id=`); maintenance-history card (top 5, links to `/maintenance?machine_id=`); asset details; configured-thresholds card; `EngineeringContext` (spec §7 copy + disclaimers) |
| `/explorer` (`SensorExplorer.tsx`) | `MetricChart machines={all}` with ranges 1h/6h/24h/7d/**30d**, machine select (defaults to worst-health machine), CSV export of current selection, engineering context |
| Shared | `charts/metric-chart.tsx` generalized (fixed/select modes; 30d via `/analytics/trends` → 60×12h buckets, avg line + min–max band + "aggregated" caption; threshold horizon + anomaly `ReferenceArea`s; per-metric y-axis only), `sensor-trend-chart.tsx` thin wrapper (Overview parity), `domain/engineering-context.tsx`, chips (`MachineStatusChip`/`WorkOrderStatusChip`/`PriorityChip`), `lib/export.ts` `downloadCsv`, queries (`useMaintenance`/`useLatestReading`/`useTrends`/`useMachineTrends`/`useCreateMachine`/`useUpdateMachine`/`useSimulationStep`, `AnomaliesQuery` +`q`/`sort`), types (`ReadingIngestResponse`, maintenance/machine payloads, trends) |

### 4b gates (verified)
`npm run format:check` ✔ · `npm run lint` ✔ (0 problems) · `npm run typecheck` ✔ · `npm run build` ✔ (only the pre-existing >500 kB chunk warning). No `npm test` yet (vitest lands in the test phase).

### Live verification (browser)
List renders 5 seeded machines with chips/badges/filters ✔ · detail header + readings + chart (warn 4.50 / crit 7.10 horizons) ✔ · **Simulate reading** → reading updated + toast "Anomaly detected — Event 146 created or extended" ✔ · thresholds dialog prefills, critical≤warning rejected inline, cancel leaves data untouched ✔ · edit dialog prefills, bad identifier rejected, cancel ✔ · `?create=1` opens register dialog, min-length error shown ✔ · explorer 30d → "last 30d · 15 buckets · avg with min–max range (aggregated from raw readings)" ✔ · Overview wrapper still works ✔.

### Decisions worth keeping
- **Detail has no health chip** — `MachineRead` carries no `health_status` (list summaries only); showing one would contradict the list. Header shows status + the latest-alert card instead.
- **30d uses `/analytics/trends`** (bucketed avg/min/max) rather than raw rows — the 30-day window at 5-min cadence (8 640 rows) exceeds the 3 000-row page cap. Explorer caption states the aggregation honestly.
- **Explorer = single-machine select** (not a cross-machine overlay): honest UI; multi-series overlay stays a possible follow-up.
- **Thresholds are full-replace** (backend `as_storage()`): dialog always submits all five metrics from its form state; blanks → cleared.
- **Simulate reading lives on the detail page** (Phase-3 decision "simulation UI on machine detail"); Settings gets demo-batch controls in 4e.
- No `DELETE /machines` exists → smoke tests never create machines (only dialogs exercised, cancelled) to keep demo data clean.
- Latest-alert/maintenance links pre-agree on query params for 4c/4d: `/anomalies?machine_id=`, `/maintenance?machine_id=`.

### Next: 4c–4e
4c anomalies UI (honor `?machine_id=`, filters incl. `q`/`sort`, acknowledge/resolve) → 4d maintenance CRUD + import wizard → 4e analytics + settings (+ demo controls), gates after each.

## 16. Phase 4 — Sub-checkpoint 4c Status (anomalies UI) — PAUSED HERE (end of day)

**State: code complete, all gates green; live smoke + plan documentation still pending. Resume here tomorrow.**

### 4c written so far (frontend only — no backend changes)

| Piece | Status |
|---|---|
| `api/queries.ts` | ✅ `useAcknowledgeAnomaly` / `useResolveAnomaly` (POST `/anomalies/{id}/acknowledge` `/resolve`, body `{notes}` only when non-empty → backend leaves notes intact); shared `invalidateAnomalyViews` (`anomalies`, `anomaly/{id}`, `dashboard`, `machines`, `latest-reading`). `AnomaliesQuery` already had `q`/`sort` from 4b. |
| `components/anomalies/anomaly-filters.tsx` | ✅ debounced search (explanation/machine), severity, method, metric ("All sensors"), machine select, from→to date inputs (sent naive `YYYY-MM-DDT00:00:00` / `T23:59:59` — backend naive-UTC), sort (detected_at/severity/metric/observed_value/status) + asc/desc + Reset (keeps status tab + sort). |
| `components/anomalies/anomalies-table.tsx` | ✅ Severity (link→detail), machine link, sensor, observed+limit, status chip + notes icon (`StickyNote`), method, detected (timeAgo), **row quick actions** (`RowActions`: Acknowledge for open, Resolve for open/acknowledged; toast + invalidation), chevron→detail, pagination footer hidden on error. |
| `pages/Anomalies.tsx` | ✅ lifecycle **status tabs** (All/Open/Acknowledged/Resolved), honors **`?machine_id=`** from machine detail link (banner + "clear machine filter"), table wiring, page size 25. |
| `pages/AnomalyDetail.tsx` | ✅ route `/anomalies/:anomalyId`; header (severity/status chips, machine link, Open machine); "Detected condition" card (observed vs limit by severity, explanation block, detected/lastseen/ack/resolved timeline, lifecycle caption); "Contributing reading" card (5 metrics, **View sensor history** → `/explorer?machine_id=&metric=`); "Investigation notes" card — notes display + textarea; actions per status: open → Acknowledge+Resolve, acknowledged → Resolve+Update note, resolved → Update note (note update rides the idempotent action endpoint). |
| `routes.tsx` / `stubs.tsx` / `route-meta.ts` | ✅ `AnomaliesStub` removed (also `TriangleAlert` icon), routes added, meta `{title: 'Anomaly event', breadcrumb: 'Anomaly Events'}`. |
| `SensorExplorer.tsx` + `metric-chart.tsx` | ✅ deep-link support: `?machine_id=`/`?metric=` → new `initialMachineId`/`initialMetric` props on `MetricChart` (useState initializers). |

### 4c gates (verified)
`format:check` ✔ · `lint` ✔ (0 problems) · `typecheck` ✔ · `build` ✔ (only pre-existing chunk-size warning).

### ⏳ 4c remaining (do first on resume)
1. **Live smoke (browser, `--no-sandbox`, named session):**
   - `/anomalies` renders; status tabs filter; search q; severity/method/metric/machine/date filters; sort + order.
   - Machine-detail "Open in anomalies" → `/anomalies?machine_id=1` banner + filtered table.
   - Open an event detail: cards, timeline, reading, note textarea.
   - Explorer deep link `View sensor history` → chart preselects machine+metric.
   - **Action test:** acknowledge + resolve one event (with a note) in the UI.
   - **Data restore:** DB is **Postgres** (`DATABASE_URL=postgresql+psycopg://shahbaz@/mechsense?host=/var/run/postgresql`, local socket) — snapshot the event's `status/acknowledged_at/resolved_at/notes` via `psql mechsense -c "SELECT ... FROM anomaly_events WHERE id=X"` **before** acting, then `UPDATE` back after the smoke so seeded demo counts (open alerts, health chips) stay as seeded. (No PATCH endpoint exists — DB restore is the only rollback.)
2. **Append §17** to plan.md with 4c results + decisions (this section is the handoff, §17 = post-smoke results).
3. Report + await user **"go"** for 4d.

### Next sub-checkpoints (unchanged)
- **4d** — Maintenance CRUD UI (`/maintenance`, honor `?machine_id=` from machine detail; WO form, status lifecycle transitions, anomaly linking) + CSV **import wizard** (`/import`: upload → preview/mapping → dry-run validation report → commit; history list). Sample CSV: `frontend/public/sample-sensor-data.csv`.
- **4e** — Analytics page (`/analytics` — trends endpoint, fleet health, per-machine stats) + Settings (`/settings` — theme/density, demo controls: `POST /demo/generate`, `POST /simulation/step` batch, `GET /configuration` display) + swap last stubs.
- Then Phase 5 (statistical detection) and Phase 6 (tests: Vitest/RTL per spec §testing, Playwright if practical, final gates).
