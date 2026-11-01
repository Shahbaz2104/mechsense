---
version: 1
slug: "frontend-src-app-tsx"
primary_target: "frontend/src/App.tsx"
related_targets: ["frontend/src/pages/Overview.tsx"]
---

# Surface brief — MechSense app shell + Overview (Phase 3)

Mode: Operate. Code-led (no image generation; app screens build code-first).

## Scope

Primary target: `frontend/src/App.tsx` (shell root) and `frontend/src/pages/Overview.tsx`.
Persistent sidebar + header + router; Overview dashboard reading only real API data.
Established world inherited from `frontend/src/index.css` tokens (brief-pinned industrial
navy/teal direction from prompt.md §3). Audience: maintenance/plant/reliability engineers
in a monitoring session; success = fleet health, active alerts, and a suspect machine
findable within seconds, then one click from drilling in.

Constraints: prompt.md §3–§5 are binding (real data only, full loading/error/empty
states, responsive desktop/tablet/mobile, status semantics green/amber/red, shadcn/ui
primary, keyboard accessible, command palette). Undecided: theme default flips to dark
at first paint only if the shell proves it; Analytics depth is Phase 5.

## Direction contract

THESIS: A monitoring console judged on state readability first — the engineer reads
fleet condition in one glance — and it refuses the generic equal-size metric-card grid
as its structure: health leads as a dense status table, metrics support it, never the
other way around.

OWN-WORLD: Deep navy/charcoal ground with teal accent from the Phase-1 tokens; amber
and red strictly reserved for warning/critical meaning; Geist with tabular numerals
for every sensor readout and count; 1px borders as the only elevation (no soft
drop-shadow cards); shadcn v4 component grammar (small radii, restrained surfaces),
dense information rhythm with generous section separation; state chips and count
badges carry color, surfaces stay neutral.

STORY: The engineer opens Overview, sees total/healthy/attention counts and active
unacknowledged alerts for the selected period, scans the machine health table for the
red rows, reads the recent anomaly feed (P-101 vibration+temperature critical), and
leaves through a drill-down link already knowing which machine to inspect.

FIRST VIEWPORT: Left sidebar rail (MechSense mark + wordmark, nine nav items with
active-route indicator and live alert count badge, collapses to icon rail/hamburger on
narrow widths) · top header (page title with breadcrumb, global machine search input,
alert bell with active count, theme toggle, demo profile menu) · content column at
1440: period segmented control (1h/6h/24h/7d/30d) over a six-metric summary strip
with real deltas and period context; below it a two-column band — machine health table
(columns: machine, type, location, status chip, latest vibration, last reading age)
left, recent anomalies feed (severity chip, machine, metric, value vs threshold,
detected-ago) right; full-width sensor trend chart beneath with machine selector and
metric tabs.

FORM: Spec-pinned side-rail console (prompt.md §4 mandates the persistent sidebar;
navigation model is not open). Position: only form considered — brief-pinned layout
under the inherited world. seed: none (unavailable — brief-pinned direction, no roll).

SIGNATURE: "Threshold horizon" — every sensor trend chart draws that machine's real
configured warning and critical limits as dashed rules with a tinted threshold band
and shades detected anomaly intervals as vertical columns, so a chart is legible as
engineered condition data, not a generic line plot.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish
review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.
