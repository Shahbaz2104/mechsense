import { METRIC_META } from '@/lib/format'

const METRIC_NOTES: { metric: keyof typeof METRIC_META; meaning: string }[] = [
  {
    metric: 'vibration_rms',
    meaning:
      'Vibration RMS is an indicator of vibration severity — a common early sign of imbalance, misalignment, looseness, or bearing wear when it trends upward.',
  },
  {
    metric: 'temperature',
    meaning:
      'Rising temperature at a bearing or housing may indicate friction, lubrication problems, or other developing issues; compare it against vibration, not in isolation.',
  },
  {
    metric: 'rpm',
    meaning:
      'Unexpected RPM changes usually reflect operating changes (speed, load, drive) rather than faults on their own.',
  },
  {
    metric: 'load_pct',
    meaning:
      'Load provides operating context — a vibration rise at constant load is more suspicious than one that tracks load.',
  },
  {
    metric: 'pressure',
    meaning:
      'Pressure adds process context for pumps and compressors; it helps explain other measurements, not diagnose on its own.',
  },
]

/**
 * Engineering-context copy required by spec §7 — interpretation guidance with
 * an explicit non-diagnostic, non-safety-limit disclaimer.
 */
export function EngineeringContext({ className }: { className?: string }) {
  return (
    <section className={className} aria-label="Engineering context">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold tracking-tight">How to read these measurements</h2>
        <span className="text-[11px] uppercase tracking-wide text-muted-foreground">
          Interpretation guide
        </span>
      </div>
      <dl className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">
        {METRIC_NOTES.map((note) => (
          <div key={note.metric} className="rounded-lg border bg-muted/25 p-3">
            <dt className="flex items-baseline gap-1.5 text-xs font-medium">
              {METRIC_META[note.metric].label}
              <span className="font-normal text-muted-foreground">
                ({METRIC_META[note.metric].unit})
              </span>
            </dt>
            <dd className="mt-1 text-xs leading-relaxed text-muted-foreground">{note.meaning}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
        These are possible interpretations, not definitive diagnoses. Readings depend on machine
        type, operating conditions, sensor placement, and your configured thresholds. Configured
        thresholds are per-machine operating limits for this application —{' '}
        <span className="font-medium text-foreground/80">
          not official safety limits or universal industrial standards
        </span>
        .
      </p>
    </section>
  )
}
