import type { AnomalySeverity, AnomalyStatus, HealthStatus } from '@/api/types'
import { ANOMALY_STATUS_LABEL, HEALTH_LABEL, SEVERITY_LABEL } from '@/lib/format'
import { cn } from '@/lib/utils'

const HEALTH_TONE: Record<HealthStatus, string> = {
  healthy: 'border-success/30 bg-success/10 text-success',
  warning: 'border-warning/40 bg-warning/10 text-warning',
  critical: 'border-danger/40 bg-danger/10 text-danger',
  inactive: 'border-border bg-muted text-muted-foreground',
  no_data: 'border-border bg-muted text-muted-foreground',
}

const HEALTH_DOT: Record<HealthStatus, string> = {
  healthy: 'bg-success',
  warning: 'bg-warning',
  critical: 'bg-danger',
  inactive: 'bg-muted-foreground/50',
  no_data: 'bg-muted-foreground/50',
}

export function HealthChip({ health, className }: { health: HealthStatus; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium',
        HEALTH_TONE[health],
        className,
      )}
    >
      <span className={cn('size-1.5 rounded-full', HEALTH_DOT[health])} aria-hidden />
      {HEALTH_LABEL[health]}
    </span>
  )
}

const SEVERITY_TONE: Record<AnomalySeverity, string> = {
  warning: 'border-warning/40 bg-warning/10 text-warning',
  critical: 'border-danger/40 bg-danger/10 text-danger',
}

export function SeverityChip({
  severity,
  className,
}: {
  severity: AnomalySeverity
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium',
        SEVERITY_TONE[severity],
        className,
      )}
    >
      <span
        className={cn(
          'size-1.5 rounded-full',
          severity === 'critical' ? 'bg-danger' : 'bg-warning',
        )}
        aria-hidden
      />
      {SEVERITY_LABEL[severity]}
    </span>
  )
}

const STATUS_TONE: Record<AnomalyStatus, string> = {
  open: 'border-danger/35 bg-danger/10 text-danger',
  acknowledged: 'border-info/35 bg-info/10 text-info',
  resolved: 'border-success/30 bg-success/10 text-success',
}

export function AnomalyStatusChip({
  status,
  className,
}: {
  status: AnomalyStatus
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
        STATUS_TONE[status],
        className,
      )}
    >
      {ANOMALY_STATUS_LABEL[status]}
    </span>
  )
}

const MACHINE_STATUS_TONE: Record<string, string> = {
  active: 'border-success/30 bg-success/10 text-success',
  inactive: 'border-border bg-muted text-muted-foreground',
}

export function MachineStatusChip({ status }: { status: 'active' | 'inactive' }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
        MACHINE_STATUS_TONE[status],
      )}
    >
      {status === 'active' ? 'Active' : 'Inactive'}
    </span>
  )
}

const WORK_ORDER_STATUS_TONE: Record<string, string> = {
  scheduled: 'border-border bg-muted text-muted-foreground',
  in_progress: 'border-info/35 bg-info/10 text-info',
  completed: 'border-success/30 bg-success/10 text-success',
  cancelled: 'border-border bg-muted text-muted-foreground',
}

const WORK_ORDER_STATUS_LABEL: Record<string, string> = {
  scheduled: 'Scheduled',
  in_progress: 'In progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

export function WorkOrderStatusChip({ status }: { status: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium',
        WORK_ORDER_STATUS_TONE[status] ?? WORK_ORDER_STATUS_TONE.scheduled,
      )}
    >
      {WORK_ORDER_STATUS_LABEL[status] ?? status}
    </span>
  )
}

const PRIORITY_TONE: Record<string, string> = {
  low: 'border-border bg-muted text-muted-foreground',
  medium: 'border-border bg-muted text-muted-foreground',
  high: 'border-warning/40 bg-warning/10 text-warning',
  urgent: 'border-danger/40 bg-danger/10 text-danger',
}

export function PriorityChip({ priority }: { priority: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
        PRIORITY_TONE[priority] ?? PRIORITY_TONE.medium,
      )}
    >
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
    </span>
  )
}
