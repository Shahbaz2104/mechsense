import { ArrowDownRight, ArrowUpRight } from 'lucide-react'

import type { DashboardPeriod, DashboardSummary } from '@/api/types'
import { Skeleton } from '@/components/ui/skeleton'
import { PERIOD_LABEL } from '@/lib/format'
import { cn } from '@/lib/utils'

interface Cell {
  key: string
  label: string
  value: string | number
  context: string
  tone?: 'default' | 'success' | 'warning' | 'danger'
  /** Real period-over-period delta (only where the API provides previous counts). */
  delta?: number
  deltaLabel?: string
}

function buildCells(summary: DashboardSummary, period: DashboardPeriod): Cell[] {
  const anomaliesDelta = summary.anomalies_period.current - summary.anomalies_period.previous
  return [
    {
      key: 'total',
      label: 'Registered machines',
      value: summary.total_machines,
      context: `${summary.active_machines} active${
        summary.inactive_machines > 0 ? ` · ${summary.inactive_machines} inactive` : ''
      }`,
    },
    {
      key: 'healthy',
      label: 'Healthy',
      value: summary.healthy_machines,
      context:
        summary.total_machines > 0
          ? `${Math.round((summary.healthy_machines / summary.total_machines) * 100)}% of fleet`
          : 'no machines yet',
      tone: summary.healthy_machines === summary.total_machines ? 'success' : 'default',
    },
    {
      key: 'attention',
      label: 'Needs attention',
      value: summary.attention_machines,
      context: 'warning or critical condition',
      tone: summary.attention_machines > 0 ? 'warning' : 'success',
    },
    {
      key: 'alerts',
      label: 'Active alerts',
      value: summary.active_alerts,
      context: 'unacknowledged, awaiting action',
      tone: summary.active_alerts > 0 ? 'danger' : 'default',
    },
    {
      key: 'anomalies',
      label: `Anomalies · ${PERIOD_LABEL[period]}`,
      value: summary.anomalies_period.current,
      context: `${summary.anomalies_period.previous} in previous window`,
      delta: anomaliesDelta,
      deltaLabel: `vs previous ${period}`,
      tone: summary.anomalies_period.current > 0 ? 'warning' : 'success',
    },
    {
      key: 'work-orders',
      label: 'Overdue work orders',
      value: summary.overdue_work_orders,
      context: `${summary.upcoming_work_orders} upcoming`,
      tone: summary.overdue_work_orders > 0 ? 'danger' : 'default',
    },
  ]
}

const TONE_TEXT: Record<NonNullable<Cell['tone']>, string> = {
  default: 'text-foreground',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
}

export function MetricStrip({
  summary,
  period,
}: {
  summary: DashboardSummary
  period: DashboardPeriod
}) {
  const cells = buildCells(summary, period)
  return (
    <div className="overflow-hidden rounded-lg border bg-card">
      <dl className="grid grid-cols-2 gap-px bg-border/70 sm:grid-cols-3 xl:grid-cols-6">
        {cells.map((cell) => (
          <div key={cell.key} className="bg-card px-4 py-3.5">
            <dt className="truncate text-xs font-medium text-muted-foreground">{cell.label}</dt>
            <dd className="mt-1.5 flex items-baseline gap-1.5">
              <span
                className={cn(
                  'text-2xl font-semibold leading-none tracking-tight tabular-nums',
                  cell.tone ? TONE_TEXT[cell.tone] : 'text-foreground',
                )}
              >
                {cell.value}
              </span>
              {cell.delta !== undefined && cell.delta !== 0 ? (
                <span
                  className={cn(
                    'flex items-center text-xs font-medium',
                    cell.delta > 0 ? 'text-danger' : 'text-success',
                  )}
                >
                  {cell.delta > 0 ? (
                    <ArrowUpRight className="size-3" aria-hidden />
                  ) : (
                    <ArrowDownRight className="size-3" aria-hidden />
                  )}
                  {Math.abs(cell.delta)}
                </span>
              ) : null}
            </dd>
            <p className="mt-1 truncate text-xs text-muted-foreground">
              {cell.delta !== undefined
                ? cell.delta === 0
                  ? `same as previous window`
                  : cell.deltaLabel
                : cell.context}
            </p>
          </div>
        ))}
      </dl>
    </div>
  )
}

export function MetricStripSkeleton() {
  return (
    <div className="overflow-hidden rounded-lg border bg-card" aria-hidden>
      <div className="grid grid-cols-2 gap-px bg-border/70 sm:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }, (_, i) => (
          <div key={i} className="space-y-2 bg-card px-4 py-3.5">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-6 w-12" />
            <Skeleton className="h-3 w-28" />
          </div>
        ))}
      </div>
    </div>
  )
}
