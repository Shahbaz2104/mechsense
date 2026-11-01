# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Maintenance engineers, plant operators, and reliability engineers monitoring industrial equipment (pumps, motors, fans, compressors) during daily health checks and incident response. Secondary audience: evaluators/reviewers of this portfolio project (the user's stated success criterion).

## Product Purpose

MechSense is an industrial machine-health monitoring platform: it ingests vibration, temperature, rotational speed, load, and pressure readings, stores them as time-series history, detects unusual machine behavior, visualizes trends, raises alerts, and lets engineers record maintenance activities. Success means a maintenance engineer can run the complete workflow — notice P-101's abnormal vibration and bearing temperature, inspect readings, examine the detected anomaly and its contributing signals, acknowledge the alert, review maintenance history, and create a work order — entirely in the app.

## Positioning

A full-stack predictive-maintenance product built with mechanical-engineering domain expertise as the competitive advantage: physically correlated synthetic data (load↔speed↔vibration, thermal lag, pressure), threshold semantics grounded in engineering practice (critical beats warning, `>=` triggers), and an end-to-end signal→detection→human decision→maintenance record chain. Not a generic CRUD dashboard; every chart, threshold, and unit is real application data.

## Operating Context

Two modes: (1) **Demo mode** — deterministic synthetic sensor data (5 seeded machines, ~10k readings over 7 days, pre-planted anomaly scenarios incl. P-101 fault ramp) so anyone can explore without hardware; (2) **Data import mode** — CSV upload, validation, analysis. Local development: FastAPI on :8000, Vite dev server with `/api` proxy, PostgreSQL on a Unix socket. Delivery artifacts: Docker Compose + GitHub Actions CI (written and lint-verified; only local run verified in this environment).

## Capabilities and Constraints

- Nine pages: Overview, Machines, Machine Details, Sensor Explorer, Anomaly Events, Maintenance, Data Import, Analytics, Settings (§4 of brief).
- Detection scope (agreed): Phase 1 threshold + Phase 2 rolling statistical detection; scikit-learn Isolation Forest is optional/future.
- **No authentication** (agreed scope cut).
- Stack: FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic + PostgreSQL; React 19 + Vite + TypeScript + Tailwind v4 + shadcn/ui + TanStack Query/Table + Recharts + React Router + Motion + Sonner + React Hook Form/Zod (confirmed by existing code).
- API: versioned `/api/v1`, uniform error envelope `{"error":{code,message,details}}`, cursor/offset pagination (`page`/`page_size`), UTC ISO timestamps.
- Visual rules the brief makes binding: every chart real data; every button/filter/table/form meaningful; loading/error/empty/populated states on every page; responsive desktop/tablet/mobile; status semantics green=healthy, amber=warning, red=critical; large readable engineering values with proper units; restrained motion.
- Decided open: analytics-page statistical depth and light-mode default are deferred to Phase 5 / theming pass respectively.

## Brand Commitments

Name **MechSense** (binding). Voice: industrial, precise, engineering-focused — "machine health intelligence", not marketing fluff. Status color semantics above are binding. Inspiration reference named by the user: modern SaaS dashboards / professional monitoring tools; shadcn/ui is the primary component system.

## Evidence on Hand

Real backend data exists and is verified: 5 machines (P-101, M-204, F-301, C-401, B-501), 10,085 seeded readings, exactly 5 deterministic anomaly events, 3 work orders, dashboard summary counts — all served by a live API with 80 passing tests. No customer testimonials, logos, pricing, or third-party benchmarks exist; future work must not fabricate any.

## Product Principles

1. **Provenance over decoration** — every displayed number, chart, and percentage traces to real backend data; no fake trend arrows or invented comparisons.
2. **Workflow integrity** — a finding is only valuable when it ends in an engineering decision: detect → inspect → acknowledge → resolve → maintenance record.
3. **Domain credibility** — engineering units (mm/s, °C, RPM, %, bar), correct threshold precedence, and physically consistent demo data are product features, not garnish.
4. **Production-minded craft** — typed end-to-end, tested, linted, migrated; portfolio-grade scrutiny on both sides of the API.
5. **Demo completeness** — the product must tell a true story with zero hardware via deterministic, reproducible synthetic data.

## Accessibility & Inclusion

Keyboard accessibility is required (explicit for the command palette and navigation). Full responsive coverage at mobile, tablet, and desktop widths. Standard semantic/contrast expectations apply as the baseline default.
