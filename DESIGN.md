---
name: MechSense
description: Machine health intelligence — an industrial monitoring console for fleet condition, threshold semantics, and anomaly response.
colors:
  console-ground: "oklch(0.165 0.021 264.5)"
  panel-surface: "oklch(0.205 0.024 265.5)"
  rail-surface: "oklch(0.148 0.019 264.5)"
  charcoal-surface: "oklch(0.27 0.03 262)"
  cool-ink: "oklch(0.975 0.004 250)"
  slate-label: "oklch(0.68 0.022 262)"
  signal-teal: "oklch(0.74 0.125 172)"
  teal-ink: "oklch(0.155 0.022 264.5)"
  health-green: "oklch(0.735 0.155 153)"
  alert-amber: "oklch(0.79 0.15 85)"
  critical-red: "oklch(0.68 0.19 25)"
  badge-critical-fill: "oklch(0.55 0.195 25)"
  info-cyan: "oklch(0.76 0.115 215)"
  plot-violet: "oklch(0.72 0.13 265)"
  hairline: "oklch(1 0 0 / 10%)"
typography:
  display:
    fontFamily: "Geist Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.025em"
    fontFeature: "tabular-nums"
  headline:
    fontFamily: "Geist Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Geist Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.375
  body:
    fontFamily: "Geist Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.43
  label:
    fontFamily: "Geist Variable, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.33
  mono:
    fontFamily: "ui-monospace, SF Mono, Cascadia Mono, monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    fontFeature: "tabular-nums"
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
  xl: "14px"
  "4xl": "26px"
  full: "9999px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "6": "24px"
  "8": "32px"
components:
  button-primary:
    backgroundColor: "{colors.signal-teal}"
    textColor: "{colors.teal-ink}"
    rounded: "{rounded.lg}"
    height: "32px"
    padding: "0 10px"
    typography: "0.875rem Geist 500"
  button-primary-hover:
    backgroundColor: "oklch(0.74 0.125 172 / 0.8)"
  button-outline:
    backgroundColor: "{colors.console-ground}"
    textColor: "{colors.cool-ink}"
    rounded: "{rounded.lg}"
    height: "32px"
    padding: "0 10px"
    typography: "0.875rem Geist 500"
  button-outline-hover:
    backgroundColor: "{colors.charcoal-surface}"
  button-ghost-hover:
    backgroundColor: "oklch(0.27 0.03 262 / 0.5)"
  button-destructive:
    backgroundColor: "oklch(0.68 0.19 25 / 0.1)"
    textColor: "{colors.critical-red}"
    rounded: "{rounded.lg}"
    height: "32px"
    padding: "0 10px"
    typography: "0.875rem Geist 500"
  input:
    backgroundColor: "transparent"
    textColor: "{colors.cool-ink}"
    rounded: "{rounded.lg}"
    height: "32px"
    padding: "4px 10px"
    typography: "0.875rem Geist 400"
  status-chip-healthy:
    backgroundColor: "oklch(0.735 0.155 153 / 0.1)"
    textColor: "{colors.health-green}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
    typography: "0.75rem Geist 500"
  status-chip-warning:
    backgroundColor: "oklch(0.79 0.15 85 / 0.1)"
    textColor: "{colors.alert-amber}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
    typography: "0.75rem Geist 500"
  status-chip-critical:
    backgroundColor: "oklch(0.68 0.19 25 / 0.1)"
    textColor: "{colors.critical-red}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
    typography: "0.75rem Geist 500"
---

# Design System: MechSense

## Overview

**Creative North Star: "The Control Room Console"**

MechSense is a monitoring console judged on state readability first: the engineer opens the app and reads fleet condition in one glance. The Overview voice is instrument-panel precision — dense, tabular numerals, status-lamp color, and copy that reads like gauges and nameplates rather than marketing. It refuses the generic equal-size metric-card grid as its structure: health leads as a dense status table sorted problems-first, summary metrics support it, and the sensor trend with its threshold horizon closes the story.

The world is a deep navy/charcoal ground with a signal-teal accent, inherited from the Phase-1 tokens and pinned by the surface brief. Component philosophy is restrained and instrumental: hairline borders, flat surfaces, no lift or shadow on resting cards — states change color and value, never elevation. Amber and red are reserved for warning and critical machine meaning; they are status lamps, not decoration. Every number, chart, and threshold traces to real backend data (provenance over decoration).

Both themes ship: dark is the default at first paint; the light theme keeps the same hues as print-ink depths on cool paper. Responsive coverage is full — the side rail collapses to an icon rail and then a hamburger sheet, the metric strip reflows 6→3→2 columns, and the fleet table sheds columns on narrow widths.

**Key Characteristics:**
- Instrument-panel precision: dense rhythm, tabular numerals, gauge-and-nameplate copy
- Deep navy ground + signal-teal accent; amber/red strictly reserved for warning/critical
- Flat and layered: 1px hairline borders are the only elevation on resting surfaces
- Geist with tabular figures on every sensor readout, count, and table cell
- Signature "Threshold horizon" charts: dashed warn/crit rules, tinted limit bands, anomaly interval shading
- shadcn v4 grammar: small radii, restrained surfaces, color-only state changes

## Colors

A dual-theme OKLCH palette: a cool navy console ground carrying one teal signal accent, a neutral hierarchy for surfaces and labels, and a tightly latched status trio. Values below are the dark theme (the default at first paint); the light theme swaps in cooler paper depths via the `.dark` scope.

### Primary
- **Signal Teal** (oklch(0.74 0.125 172)): the single interactive accent — primary buttons, focus rings, active nav indicator, brand mark, avatar tint, and the primary chart series. Light theme counterpart is the deeper print-ink teal (oklch(0.52 0.105 178)).
- **Teal Ink** (oklch(0.155 0.022 264.5)): the deep navy that sits on top of Signal Teal fills (primary button label, brand-mark waveform).

### Secondary
- **Info Cyan** (oklch(0.76 0.115 215)): neutral-informational states — the "Acknowledged" anomaly chip, chart series 2. Never a machine-health meaning.
- **Plot Violet** (oklch(0.72 0.13 265)): chart series 3 only; exists so multi-series plots stay separable without borrowing status hues.

### Tertiary (Status Lamps — binding semantics)
- **Health Green** (oklch(0.735 0.155 153)): healthy machine state, resolved anomalies, positive deltas.
- **Alert Amber** (oklch(0.79 0.15 85)): warning state, warn threshold rules and bands, warning-severity anomalies.
- **Critical Red** (oklch(0.68 0.19 25)): critical state, crit threshold rules and bands, open critical anomalies, destructive actions.
- **Badge Critical Fill** (oklch(0.55 0.195 25)): the solid red behind white count-badge digits (alert bell, sidebar anomaly badge) in both themes, so digits clear 4.5:1.

### Neutral
- **Console Ground** (oklch(0.165 0.021 264.5)): the page background — the darkest layer of the console.
- **Panel Surface** (oklch(0.205 0.024 265.5)): cards, popovers, dialogs — one step above the ground.
- **Rail Surface** (oklch(0.148 0.019 264.5)): the sidebar rail, one step below the ground so navigation recedes.
- **Charcoal Surface** (oklch(0.27 0.03 262)): muted fills — secondary buttons, hover washes, segmented-control troughs, skeleton blocks.
- **Cool Ink** (oklch(0.975 0.004 250)): primary text.
- **Slate Label** (oklch(0.68 0.022 262)): secondary text — captions, units, table headers, context lines.
- **Hairline** (oklch(1 0 0 / 10%)): the 1px borders and dividers that separate every surface. Light theme equivalent is a cool grey hairline (oklch(0.915 0.005 255)).

Light theme, briefly: ground becomes cool paper (oklch(0.975 0.003 245)), ink becomes deep navy (oklch(0.21 0.032 264.5)), panels go pure white, and the status hues keep their chroma while dropping to print-ink lightness (green oklch(0.545 0.13 155), amber oklch(0.66 0.135 72), red oklch(0.55 0.195 25)).

### Named Rules
**The Status Latch Rule.** Green means healthy, amber means warning, red means critical — nothing else, ever. Amber and red are reserved for warning/critical machine meaning; they must never decorate headings, branding, or "positive" emphasis. If a color looks like a status lamp, it must report a status.

**The Teal Monopoly Rule.** Signal Teal is the only interactive accent. Status hues never fill a primary button; teal never fakes a status. Rarity is what makes the accent read as "action" against a field of lamps.

## Typography

**Display Font:** Geist Variable (fallback: ui-sans-serif, system-ui, sans-serif)
**Body Font:** Geist Variable (same stack — one family carries the whole UI)
**Label/Mono Font:** ui-monospace, SF Mono, Cascadia Mono, monospace — for machine identifiers (P-101, M-204) and other asset tags

**Character:** A single crisp neo-grotesque paired with engineering monospace. The pairing reads as nameplate and readout: Geist handles interface voice, the mono stack marks physical asset identity, and tabular numerals lock every measured value into instrument-grade columns.

### Hierarchy
- **Display** (600, 1.5rem, 1.0, tracking -0.025em, tabular): summary metric values in the six-cell strip — the largest numbers on the page.
- **Headline** (600, 1.25rem, 1.4, tracking -0.025em): page titles in the header ("Overview").
- **Title** (500, 1rem, 1.375): card and section titles ("Fleet health", "Sensor trend").
- **Body** (400, 0.875rem, 1.43): default UI copy, table cells, list rows, form values.
- **Label** (500, 0.75rem, 1.33): metric-cell labels, table headers, chips, captions, context lines — often in Slate Label color.
- **Mono** (400, 0.75rem): machine identifiers everywhere they appear (tables, selects, command palette, chart footers).

### Named Rules
**The Tabular Numerals Rule.** Every sensor value, count, delta, threshold, and table cell renders with tabular figures (`font-variant-numeric: tabular-nums`). Columns of numbers must align like a gauge panel; proportional digits are a bug.

## Layout

A spec-pinned side-rail console. A persistent left sidebar (Rail Surface, deeper than the content ground) holds the brand mark, grouped nav (Monitor / Assets / System), a live alert-count badge, and the demo profile; it collapses to an icon rail on tablet and hides behind a hamburger sheet on mobile. The top header carries the page title with breadcrumb, global machine search, alert bell with count, theme toggle, and profile menu. Content sits in a centered column capped at 1440px with 16px page padding on mobile and 24px from tablet up (px-4/px-6, py-6).

Density is high inside panels, generous between them: 4px base rhythm (Tailwind v4 spacing), 12–16px card padding, 24px section gaps. The Overview stacks: period segmented control → six-metric summary strip (2 columns mobile, 3 at sm, 6 at xl, drawn as one bordered panel split by gap-px hairlines) → a two-column band on desktop (fleet health table left, recent anomalies feed right) → full-width sensor trend card. Tables shed columns progressively on narrow widths rather than scrolling sideways at first.

Breakpoints are Tailwind defaults (640 / 768 / 1024 / 1280 / 1536px); the project defines none of its own. Rules of composition: the fleet table is always sorted problems-first (critical, then warning, then healthy), and every chart, table, and feed has real loading, error, and empty states occupying the same frame.

## Elevation & Depth

This system is flat and layered. There are no resting drop-shadow cards; the only elevation language on content surfaces is a 1px Hairline border (plus the card's `ring-1 ring-foreground/10` edge in shadcn grammar). Layering comes from the surface ladder itself: Rail Surface sits below Console Ground, Panel Surface sits above it, and gap-px hairlines divide cells inside a single panel (the metric strip).

### Shadow Vocabulary
Shadows exist only as a handful of Tailwind built-in utilities (the project defines no `--shadow-*` tokens), and only where a layer must visibly detach from the console:
- **Active segment** (`box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05)`): the selected tab in period and metric segmented controls — a 1px lift confirming the pressed cell.
- **Overlay** (`box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)`): popovers, selects, dropdown menus, chart tooltips.
- **Sheet** (`box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)`): side sheets and dialogs.
- **Inset rail** (shadow-sm on the content card of the inset sidebar variant): separates the content column from the rail on wide screens.

### Named Rules
**The Hairline Rule.** Depth is drawn, not cast. Every resting surface is defined by its 1px border and its step on the surface ladder; a shadow on a resting card is a violation. Shadows belong only to transient overlays and the active segment of a control.

## Shapes

Small-radius, squared-off, instrumental. The scale derives from a single base radius of 10px (`--radius: 0.625rem`): sm 6px, md 8px, lg 10px, xl 14px, 4xl 26px, plus full pills. Buttons, inputs, and selects take lg (10px); cards and panels take xl (14px); segmented-control cells take md or a tight 5px; tooltips and chart tooltips take md. Status chips are full pills (9999px) with a 6px dot; count badges are perfect circles. The brand mark is a 32px rounded square (7px corner) with a stroked waveform. Borders are always 1px; checkboxes take a tight 4px corner. No clipping tricks, no nested radii — one silhouette family across the app.

## Components

Component character is restrained and instrumental: flat fills, hairline borders, color-only state changes, no elevation shifts.

### Buttons
- **Shape:** gently rounded (10px), 32px tall, compact horizontal padding (10px), 14px medium-weight label; icons 16px.
- **Primary:** Signal Teal fill with Teal Ink label — the only filled accent button; used for the single affirmative action in a view (e.g. Quick actions, Create work order).
- **Hover / Focus:** primary lightens via an 80%-alpha teal; outline/ghost wash to Charcoal Surface; focus draws a 3px teal ring at 50% alpha plus a teal border. Press translates down 1px. Disabled drops to 50% opacity.
- **Outline:** Console Ground fill, Cool Ink label, Hairline border — the default secondary action.
- **Ghost:** no fill at rest; Charcoal Surface wash on hover — header utilities, row actions.
- **Destructive:** 10% Critical Red wash with Critical Red label (20% wash on hover) — never a solid red fill.

### Chips
- **Style:** full pill, 2px×8px padding, 12px medium label, 6px leading dot. Tinted formula: status color at 10% background, 30–40% border, full-strength text.
- **Health:** Healthy (green), Warning (amber), Critical (red), Inactive/No data (Charcoal Surface + Slate Label).
- **Severity / Anomaly status:** Warning/Critical severity chips reuse the lamp tones; workflow status adds Info Cyan for Acknowledged and Health Green for Resolved.

### Cards / Containers
- **Corner Style:** 14px on outer panels (metric strip uses 10px), 8px on nested chrome.
- **Background:** Panel Surface on Console Ground.
- **Shadow Strategy:** none at rest — Hairline border + ring edge only (see Elevation & Depth).
- **Border:** 1px Hairline; interior dividers use gap-px hairlines so cells read as one machined panel.
- **Internal Padding:** 16px standard (12px in compact/`sm` cards); card headers separated from content by a hairline border.

### Inputs / Fields
- **Style:** 32px tall, 10px radius, transparent fill (a 15%-white wash in dark mode), 1px input border, 10px horizontal padding, 14px text; placeholder in Slate Label.
- **Focus:** border shifts to teal plus a 3px teal ring at 50% alpha.
- **Error / Disabled:** destructive border + red ring at invalid; disabled at 50% opacity with a muted fill. The header search is a compact muted-trough variant (8px radius, Charcoal Surface at 40%) that fills on hover.

### Navigation
- **Style:** persistent sidebar on Rail Surface with grouped sections (Monitor / Assets / System) labeled in 12px Slate Label. Items are 8px-radius rows with a 16px icon and 14px label.
- **States:** hover/active wash to Sidebar Accent; active route keeps medium weight and the accent wash; the Anomaly Events item carries a circular Badge Critical Fill count of unacknowledged alerts. Focus draws a 2px teal ring.
- **Mobile:** rail collapses to icons at tablet (tooltips carry the labels), then hides entirely behind a hamburger sheet; the header condenses to icon buttons.

### Summary Metric Strip
Six instrument cells in one bordered panel divided by gap-px hairlines: 12px Slate Label caption, 24px semibold tabular value (tone-colored green/amber/red only when the count itself carries status meaning), and a 12px context line. Real period deltas appear as 12px up/down arrows colored by direction (more anomalies = red, fewer = green).

### Tables
Fleet health and other domain tables: 12px medium headers, 14px body cells, machine identifier in mono with a secondary name line, status as a chip, measured values in tabular figures with the unit in Slate Label. Rows are divided by hairlines and wash to Charcoal Surface at 50% on hover. Default sort is problems-first.

### Threshold Horizon (Signature Component)
Every sensor trend chart draws that machine's real configured limits as a horizon, so the plot reads as engineered condition data rather than a generic line chart:
- **Limit rules:** warning and critical thresholds as 1px dashed rules (dash 6 4) in Alert Amber and Critical Red, each labeled inline ("warn 4.50", "crit 7.10") in its own color.
- **Tinted bands:** the zone between warn and crit is filled amber at 7% opacity; the zone above crit is filled red at 7% opacity — the danger territory is visible even before the trace enters it.
- **Anomaly intervals:** each detected event is shaded as a vertical column (fill 10%, 1px dashed side strokes at 35%) in its severity color, spanning detected→resolved (or now).
- **Trace:** the sensor series is a 1.75px Signal Teal line with no dots and no draw-on animation — data appears instantly. Axes are hairline-free (no axis lines, no vertical gridlines), ticks in 11px Slate Label.

## Do's and Don'ts

### Do:
- **Do** keep amber and red locked to warning/critical machine meaning — status chips, threshold rules, critical deltas, destructive actions only.
- **Do** render every measured number with tabular numerals and its engineering unit (mm/s, °C, RPM, %, bar).
- **Do** define resting surfaces with a 1px Hairline border and a step on the surface ladder (Rail → Ground → Panel).
- **Do** draw every sensor chart as a Threshold horizon: dashed warn/crit rules, 7% tinted bands, and shaded anomaly intervals from real configured limits.
- **Do** keep copy instrument-panel: nameplates, gauges, counts, and thresholds — no marketing tone.
- **Do** give every data view real loading, error, and empty states inside the same framed panel.
- **Do** sort fleet tables problems-first and keep the worst-condition machine as the default chart selection.
- **Do** use Signal Teal as the sole interactive accent and draw focus as a 3px teal ring at 50% alpha.

### Don't:
- **Don't** put a drop-shadow on a resting card, panel, or table — depth is a 1px border, not a shadow.
- **Don't** use amber, red, or green for decoration, branding, or generic emphasis.
- **Don't** animate chart data draw-on or springy entrances — plots render instantly; motion is reserved for 150ms state transitions and 100ms overlay entrances.
- **Don't** invent trend arrows, comparisons, or percentages that don't trace to backend data (provenance over decoration).
- **Don't** use proportional digits in any sensor value, count, or table cell.
- **Don't** make a filled primary button more than once per view; everything else is outline, ghost, or text.
- **Don't** add a second accent hue outside the chart-series palette (teal, cyan, violet, amber, red).
