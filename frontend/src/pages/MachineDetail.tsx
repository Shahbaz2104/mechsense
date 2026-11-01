import { useMemo, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router'
import { ArrowLeft, Factory, Gauge, Pencil, TriangleAlert, Wrench, Zap } from 'lucide-react'
import { toast } from 'sonner'

import { ApiError } from '@/api/client'
import {
  useAnomalies,
  useLatestReading,
  useMachine,
  useMaintenance,
  useSimulationStep,
  useUpdateMachine,
} from '@/api/queries'
import type { MetricName } from '@/api/types'
import {
  AnomalyStatusChip,
  MachineStatusChip,
  PriorityChip,
  SeverityChip,
  WorkOrderStatusChip,
} from '@/components/domain/chips'
import { EngineeringContext } from '@/components/domain/engineering-context'
import { CardSkeleton, EmptyState, ErrorState, PageLoading } from '@/components/feedback'
import { MetricChart } from '@/components/charts/metric-chart'
import { MachineFormDialog } from '@/components/machines/machine-form-dialog'
import { ThresholdsDialog } from '@/components/machines/thresholds-dialog'
import { Button } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  METRIC_META,
  METRIC_ORDER,
  formatMetric,
  formatTimestamp,
  titleCase,
  timeAgo,
} from '@/lib/format'

function ReadingCell({ metric, value }: { metric: MetricName; value: number | null | undefined }) {
  const meta = METRIC_META[metric]
  return (
    <div className="bg-background px-4 py-3.5">
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {meta.shortLabel}
      </p>
      <p className="mt-1 text-xl font-semibold tabular-nums">
        {formatMetric(metric, value)}
        <span className="ml-1 text-xs font-normal text-muted-foreground">{meta.unit}</span>
      </p>
      {metric === 'pressure' && (value === null || value === undefined) ? (
        <p className="mt-0.5 text-[11px] text-muted-foreground">not sensed</p>
      ) : null}
    </div>
  )
}

export default function MachineDetailPage() {
  const params = useParams<{ machineId: string }>()
  const machineId = Number(params.machineId)
  const valid = Number.isInteger(machineId) && machineId > 0

  const machineQuery = useMachine(machineId, valid)
  const latestQuery = useLatestReading(machineId, valid)
  const anomalyQuery = useAnomalies(
    { machine_id: machineId, page_size: 1, sort: 'detected_at', order: 'desc' },
    valid,
  )
  const maintenanceQuery = useMaintenance(
    { machine_id: machineId, page_size: 5, sort: 'scheduled_date', order: 'desc' },
    valid,
  )
  const stepMutation = useSimulationStep(machineId)
  const statusMutation = useUpdateMachine(machineId)

  const [editOpen, setEditOpen] = useState(false)
  const [thresholdsOpen, setThresholdsOpen] = useState(false)
  const [statusConfirm, setStatusConfirm] = useState<'activate' | 'deactivate' | null>(null)

  const machine = machineQuery.data
  const latest = latestQuery.data
  const latestAlert = anomalyQuery.data?.items[0]

  const thresholdRows = useMemo(() => {
    if (!machine) return []
    return METRIC_ORDER.map((metric) => ({ metric, config: machine.thresholds[metric] })).filter(
      (row) =>
        row.config !== undefined && (row.config.warning !== null || row.config.critical !== null),
    )
  }, [machine])

  if (!valid) return <Navigate to="/machines" replace />
  if (machineQuery.isPending) return <PageLoading label="Loading machine" />
  if (machineQuery.error || !machine) {
    return (
      <div className="space-y-4">
        <ErrorState
          title="Machine unavailable"
          error={machineQuery.error}
          onRetry={() => void machineQuery.refetch()}
        />
        <div className="flex justify-center">
          <Button variant="outline" size="sm" asChild>
            <Link to="/machines">
              <ArrowLeft className="size-3.5" aria-hidden />
              Back to machines
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  async function handleSimulate() {
    try {
      const result = await stepMutation.mutateAsync()
      if (result.affected_anomaly_ids.length > 0) {
        toast.warning('Anomaly detected', {
          description: `Event${result.affected_anomaly_ids.length === 1 ? '' : 's'} ${result.affected_anomaly_ids.join(', ')} created or extended.`,
        })
      } else {
        toast.success('Reading simulated', {
          description: `Reading ${result.reading.id} recorded at ${formatTimestamp(result.reading.timestamp)}.`,
        })
      }
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Simulation failed')
    }
  }

  async function handleStatusChange() {
    if (!statusConfirm || !machine) return
    try {
      await statusMutation.mutateAsync({
        status: statusConfirm === 'activate' ? 'active' : 'inactive',
      })
      toast.success(
        statusConfirm === 'activate'
          ? `${machine.identifier} activated`
          : `${machine.identifier} deactivated`,
      )
      setStatusConfirm(null)
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Could not update status')
    }
  }

  const isActive = machine.status === 'active'

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-lg border bg-muted/40 text-muted-foreground">
            <Factory className="size-5" aria-hidden />
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-mono text-lg font-semibold tracking-tight">
                {machine.identifier}
              </h1>
              <MachineStatusChip status={machine.status} />
            </div>
            <p className="text-sm text-muted-foreground">{machine.name}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {titleCase(machine.equipment_type)}
              {machine.location ? ` · ${machine.location}` : ''} · registered{' '}
              {formatTimestamp(machine.created_at, 'MMM d, yyyy')}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" className="gap-1.5" onClick={() => setEditOpen(true)}>
            <Pencil className="size-3.5" aria-hidden />
            Edit
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => setThresholdsOpen(true)}
          >
            <Gauge className="size-3.5" aria-hidden />
            Thresholds
          </Button>
          <Button
            size="sm"
            variant={isActive ? 'destructive' : 'default'}
            onClick={() => setStatusConfirm(isActive ? 'deactivate' : 'activate')}
          >
            {isActive ? 'Deactivate' : 'Activate'}
          </Button>
        </div>
      </header>

      <Card>
        <CardHeader className="gap-3 border-b py-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="text-sm">Current readings</CardTitle>
              <CardDescription className="text-xs">
                {latest
                  ? `Latest sample · ${formatTimestamp(latest.timestamp)} · source: ${titleCase(latest.source)}`
                  : 'The most recent values reported by this machine'}
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-1.5 text-xs"
              onClick={() => void handleSimulate()}
              disabled={stepMutation.isPending}
              title="Generate one server-side reading for this machine (demo)"
            >
              <Zap className="size-3.5" aria-hidden />
              {stepMutation.isPending ? 'Simulating…' : 'Simulate reading'}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {!latest ? (
            <EmptyState
              title="No readings yet"
              description="Simulate a reading above, generate demo data from Settings, or import a CSV to start monitoring this machine."
            />
          ) : (
            <div className="grid grid-cols-2 gap-px bg-border sm:grid-cols-3 lg:grid-cols-5">
              {METRIC_ORDER.map((metric) => (
                <ReadingCell key={metric} metric={metric} value={latest[metric] as number | null} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <MetricChart fixedMachineId={machine.id} />

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader className="border-b py-4">
            <CardTitle className="text-sm">Latest alert</CardTitle>
            <CardDescription className="text-xs">
              Most recent anomaly event for this machine
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4">
            {anomalyQuery.isPending ? (
              <CardSkeleton rows={3} />
            ) : anomalyQuery.error ? (
              <ErrorState
                title="Alerts unavailable"
                error={anomalyQuery.error}
                onRetry={() => void anomalyQuery.refetch()}
              />
            ) : !latestAlert ? (
              <EmptyState
                title="No anomaly events"
                description="Nothing has crossed a configured threshold for this machine yet."
                icon={<TriangleAlert className="size-5" aria-hidden />}
              />
            ) : (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <SeverityChip severity={latestAlert.severity} />
                  <AnomalyStatusChip status={latestAlert.status} />
                  <span className="text-xs text-muted-foreground">
                    {titleCase(latestAlert.method)} · {timeAgo(latestAlert.detected_at)}
                  </span>
                </div>
                <p className="text-sm font-medium">
                  {METRIC_META[latestAlert.metric as MetricName]?.label ??
                    titleCase(latestAlert.metric)}{' '}
                  <span className="font-normal tabular-nums">
                    {formatMetric(latestAlert.metric as MetricName, latestAlert.observed_value)}
                    {latestAlert.threshold_value !== null
                      ? ` (threshold ${formatMetric(latestAlert.metric as MetricName, latestAlert.threshold_value)})`
                      : ' (threshold not set)'}
                  </span>
                </p>
                <p className="line-clamp-4 text-sm leading-relaxed text-muted-foreground">
                  {latestAlert.explanation}
                </p>
                <Button variant="outline" size="sm" className="gap-1.5 text-xs" asChild>
                  <Link to={`/anomalies?machine_id=${machine.id}`}>
                    Open in anomalies
                    <ArrowLeft className="size-3.5 rotate-180" aria-hidden />
                  </Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b py-4">
            <div className="flex items-center gap-2">
              <Wrench className="size-4 text-muted-foreground" aria-hidden />
              <div>
                <CardTitle className="text-sm">Maintenance history</CardTitle>
                <CardDescription className="text-xs">
                  Recent work orders for this machine
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4">
            {maintenanceQuery.isPending ? (
              <CardSkeleton rows={3} />
            ) : maintenanceQuery.error ? (
              <ErrorState
                title="Maintenance history unavailable"
                error={maintenanceQuery.error}
                onRetry={() => void maintenanceQuery.refetch()}
              />
            ) : !maintenanceQuery.data?.items.length ? (
              <EmptyState
                title="No work orders yet"
                description="Maintenance records for this machine will appear here once created."
                icon={<Wrench className="size-5" aria-hidden />}
                action={
                  <Button variant="outline" size="sm" asChild>
                    <Link to={`/maintenance?machine_id=${machine.id}`}>Create work order</Link>
                  </Button>
                }
              />
            ) : (
              <>
                <ul>
                  {maintenanceQuery.data.items.map((order) => (
                    <li
                      key={order.id}
                      className="flex items-start justify-between gap-3 border-b py-2.5 last:border-b-0"
                    >
                      <div className="min-w-0">
                        <p className="flex items-center gap-2 text-xs">
                          <span className="font-mono font-medium">{order.work_order_number}</span>
                          <span className="truncate text-muted-foreground">
                            {titleCase(order.maintenance_type)}
                          </span>
                        </p>
                        <p className="mt-0.5 truncate text-sm">{order.title}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {order.scheduled_date
                            ? `Scheduled ${order.scheduled_date}`
                            : 'Unscheduled'}
                        </p>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1">
                        <WorkOrderStatusChip status={order.status} />
                        <PriorityChip priority={order.priority} />
                      </div>
                    </li>
                  ))}
                </ul>
                <div className="mt-3 flex justify-end">
                  <Button variant="ghost" size="sm" className="gap-1 text-xs" asChild>
                    <Link to={`/maintenance?machine_id=${machine.id}`}>
                      View all
                      <ArrowLeft className="size-3.5 rotate-180" aria-hidden />
                    </Link>
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader className="border-b py-4">
            <CardTitle className="text-sm">Asset details</CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Equipment</dt>
                <dd className="mt-0.5">{titleCase(machine.equipment_type)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Location</dt>
                <dd className="mt-0.5">{machine.location || '—'}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                  Manufacturer
                </dt>
                <dd className="mt-0.5">{machine.manufacturer || '—'}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Model</dt>
                <dd className="mt-0.5">{machine.model || '—'}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Installed</dt>
                <dd className="mt-0.5">{machine.installation_date || '—'}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                  Registered
                </dt>
                <dd className="mt-0.5">{formatTimestamp(machine.created_at, 'MMM d, yyyy')}</dd>
              </div>
              {machine.description ? (
                <div className="sm:col-span-2">
                  <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                    Description
                  </dt>
                  <dd className="mt-0.5 leading-relaxed">{machine.description}</dd>
                </div>
              ) : null}
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b py-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="text-sm">Configured thresholds</CardTitle>
                <CardDescription className="text-xs">
                  Per-machine operating limits — not certified safety limits
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1.5 text-xs"
                onClick={() => setThresholdsOpen(true)}
              >
                <Gauge className="size-3.5" aria-hidden />
                Configure
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-4">
            {thresholdRows.length === 0 ? (
              <EmptyState
                title="No thresholds configured"
                description="Set warning and critical limits so detection and the chart horizon can flag outliers."
                icon={<Gauge className="size-5" aria-hidden />}
                action={
                  <Button size="sm" onClick={() => setThresholdsOpen(true)}>
                    Configure thresholds
                  </Button>
                }
              />
            ) : (
              <ul className="divide-y">
                {thresholdRows.map(({ metric, config }) => (
                  <li key={metric} className="flex items-center justify-between gap-4 py-2.5">
                    <span className="text-sm">
                      {METRIC_META[metric].label}
                      <span className="ml-1.5 text-xs text-muted-foreground">
                        ({METRIC_META[metric].unit})
                      </span>
                    </span>
                    <span className="text-sm tabular-nums text-muted-foreground">
                      <span className="text-warning">
                        W {formatMetric(metric, config?.warning ?? null)}
                      </span>
                      {' · '}
                      <span className="text-danger">
                        C {formatMetric(metric, config?.critical ?? null)}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <EngineeringContext className="rounded-lg border bg-muted/25 p-4" />

      <MachineFormDialog open={editOpen} onOpenChange={setEditOpen} machine={machine} />
      <ThresholdsDialog open={thresholdsOpen} onOpenChange={setThresholdsOpen} machine={machine} />

      <AlertDialog
        open={statusConfirm !== null}
        onOpenChange={(open) => {
          if (!open) setStatusConfirm(null)
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {statusConfirm === 'deactivate' ? 'Deactivate machine?' : 'Activate machine?'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {statusConfirm === 'deactivate'
                ? 'The machine stops counting as active in dashboards and health rollups. Historical readings and events are kept.'
                : 'The machine returns to the active monitored fleet and contributes to health rollups again.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={statusMutation.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              disabled={statusMutation.isPending}
              onClick={(event) => {
                event.preventDefault()
                void handleStatusChange()
              }}
            >
              {statusMutation.isPending
                ? 'Saving…'
                : statusConfirm === 'deactivate'
                  ? 'Deactivate'
                  : 'Activate'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
