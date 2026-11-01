import { useMemo, useState } from 'react'
import { format } from 'date-fns'
import { Download } from 'lucide-react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  XAxis,
  YAxis,
} from 'recharts'

import type { MachineSummary, MetricName, ReadingRead } from '@/api/types'
import {
  useAnomalies,
  useMachine,
  useMachineReadings,
  useMachineTrends,
  type ReadRange,
} from '@/api/queries'
import { ChartContainer, ChartTooltip, type ChartConfig } from '@/components/ui/chart'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { EmptyState, ErrorState } from '@/components/feedback'
import { METRIC_META, METRIC_ORDER, healthRank, titleCase } from '@/lib/format'
import { downloadCsv } from '@/lib/export'
import { cn } from '@/lib/utils'

/** Raw ranges fetch exact readings; 30d goes through the bucketed trends API
 *  (8 640 rows at 5-minute cadence would exceed the 3 000-row page cap). */
export type ChartRange = ReadRange | '30d'

const X_TICK_PATTERN: Record<ChartRange, string> = {
  '1h': 'HH:mm',
  '6h': 'HH:mm',
  '24h': 'HH:mm',
  '7d': 'MMM d',
  '30d': 'MMM d',
}

interface PlotPoint {
  t: number
  v: number
  min?: number
  max?: number
  count?: number
}

function toPoints(readings: ReadingRead[], metric: MetricName): PlotPoint[] {
  const points: PlotPoint[] = []
  for (const reading of readings) {
    const value = metric === 'pressure' ? reading.pressure : reading[metric]
    if (value === null || value === undefined) continue
    points.push({ t: new Date(reading.timestamp).getTime(), v: value })
  }
  return points
}

function defaultMachineId(machines: MachineSummary[]): number | null {
  if (machines.length === 0) return null
  const sorted = [...machines].sort((a, b) => {
    const byHealth = healthRank(a.health_status) - healthRank(b.health_status)
    if (byHealth !== 0) return byHealth
    return a.identifier.localeCompare(b.identifier)
  })
  return sorted[0]?.id ?? null
}

export interface MetricChartProps {
  /** Options for the machine select; omit together with `fixedMachineId`. */
  machines?: MachineSummary[]
  /** Single-machine mode (machine detail): hides the machine select. */
  fixedMachineId?: number
  /** Defaults to the raw ranges (Overview parity); pass 30d for the explorer. */
  allowRanges?: readonly ChartRange[]
  /** Initial machine selection for select mode (deep links from event details). */
  initialMachineId?: number
  /** Initial metric selection (deep links from event details). */
  initialMetric?: MetricName
  className?: string
}

/**
 * Time-series explorer chart: one metric, one machine, threshold horizon and
 * detected-interval markers, with CSV export of the displayed selection.
 * Metrics never share a y-axis — each selection renders its own unit scale.
 */
export function MetricChart({
  machines,
  fixedMachineId,
  allowRanges = ['1h', '6h', '24h', '7d'],
  initialMachineId,
  initialMetric,
  className,
}: MetricChartProps) {
  const fixed = fixedMachineId !== undefined
  const [selectedId, setSelectedId] = useState<number | null>(initialMachineId ?? null)
  const [metricChoice, setMetricChoice] = useState<MetricName>(initialMetric ?? 'vibration_rms')
  const [range, setRange] = useState<ChartRange>(
    allowRanges.includes('24h') ? '24h' : allowRanges[0],
  )

  const machineId = fixed ? fixedMachineId : (selectedId ?? defaultMachineId(machines ?? []))

  const machineQuery = useMachine(machineId ?? 0, machineId !== null)

  const metric: MetricName =
    metricChoice === 'pressure' && !machineQuery.data?.thresholds.pressure
      ? 'vibration_rms'
      : metricChoice

  const rawRange = range === '30d' ? undefined : (range as ReadRange)
  const readingsQuery = useMachineReadings(
    machineId ?? 0,
    rawRange ?? '7d',
    machineId !== null && rawRange !== undefined,
  )
  const trendsQuery = useMachineTrends(
    machineId ?? 0,
    metric,
    machineId !== null && rawRange === undefined,
  )

  const thresholds = machineQuery.data?.thresholds?.[metric]
  const warn = thresholds?.warning ?? null
  const crit = thresholds?.critical ?? null

  const rawWindow = rawRange !== undefined ? readingsQuery.data : undefined
  const trendWindow = rawRange === undefined ? trendsQuery.data : undefined
  const windowStart = rawWindow?.start ?? trendWindow?.start
  const windowEnd = rawWindow?.end ?? trendWindow?.end
  const windowEndMs = windowEnd?.getTime()

  const anomalyQuery = useAnomalies(
    {
      machine_id: machineId ?? undefined,
      metric,
      page_size: 100,
      start: windowStart?.toISOString(),
      end: windowEnd?.toISOString(),
    },
    windowStart !== undefined && machineId !== null,
  )

  const points = useMemo<PlotPoint[]>(() => {
    if (rawWindow) return toPoints(rawWindow.items, metric)
    if (trendWindow) {
      const series = trendWindow.data.series.find((item) => item.machine_id === machineId)
      const bucketed: PlotPoint[] = []
      for (const point of series?.points ?? []) {
        if (point.avg === null) continue
        bucketed.push({
          t: new Date(point.bucket_start).getTime(),
          v: point.avg,
          min: point.min,
          max: point.max,
          count: point.count,
        })
      }
      return bucketed
    }
    return []
  }, [rawWindow, trendWindow, metric, machineId])

  const bucketed = rawRange === undefined && points.length > 0

  const { yMin, yMax } = useMemo(() => {
    if (points.length === 0) return { yMin: 0, yMax: 1 }
    let min = Math.min(...points.map((p) => p.v))
    let max = Math.max(...points.map((p) => p.v))
    if (bucketed) {
      for (const p of points) {
        if (p.min !== undefined) min = Math.min(min, p.min)
        if (p.max !== undefined) max = Math.max(max, p.max)
      }
    }
    for (const bound of [warn, crit]) {
      if (bound !== null) {
        min = Math.min(min, bound)
        max = Math.max(max, bound)
      }
    }
    const pad = Math.max((max - min) * 0.12, 0.5)
    return { yMin: Math.max(0, min - pad), yMax: max + pad }
  }, [points, warn, crit, bucketed])

  const meta = METRIC_META[metric]
  const chartConfig = {
    v: { label: `${meta.label} (${meta.unit})`, color: 'var(--chart-1)' },
  } satisfies ChartConfig

  const selectedMachine = fixed
    ? machineQuery.data
    : (machines ?? []).find((machine) => machine.id === machineId)
  const metricTabs = METRIC_ORDER.filter(
    (name) => name !== 'pressure' || machineQuery.data?.thresholds.pressure !== undefined,
  )

  const isLoading = rawRange !== undefined ? readingsQuery.isLoading : trendsQuery.isLoading
  const queryError = rawRange !== undefined ? readingsQuery.error : trendsQuery.error
  const retry = () => (rawRange !== undefined ? readingsQuery.refetch() : trendsQuery.refetch())

  function handleExport() {
    if (!selectedMachine || points.length === 0) return
    const stamp = `${selectedMachine.identifier}-${metric}-${range}`
    if (bucketed) {
      downloadCsv(
        `trend-${stamp}`,
        ['bucket_start', 'avg', 'min', 'max', 'count'],
        points.map((p) => [
          new Date(p.t).toISOString(),
          p.v,
          p.min ?? null,
          p.max ?? null,
          p.count ?? null,
        ]),
      )
    } else if (rawWindow) {
      downloadCsv(
        `trend-${stamp}`,
        ['timestamp', metric],
        rawWindow.items
          .map((reading) => {
            const value = metric === 'pressure' ? reading.pressure : reading[metric]
            return value === null ? null : ([reading.timestamp, value] as const)
          })
          .filter((row): row is readonly [string, number] => row !== null)
          .map((row) => [row[0], row[1]]),
      )
    }
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="gap-3 border-b py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-sm">Sensor trend</CardTitle>
            <CardDescription className="text-xs">
              Threshold horizon — configured limits and detected intervals over the window
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Tabs value={metric} onValueChange={(value) => setMetricChoice(value as MetricName)}>
              <TabsList className="h-8 rounded-md bg-muted/60 p-[3px]" aria-label="Sensor metric">
                {metricTabs.map((name) => (
                  <TabsTrigger
                    key={name}
                    value={name}
                    className="h-6 rounded-[5px] px-2.5 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"
                  >
                    {METRIC_META[name].shortLabel}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
            <Tabs
              value={range}
              onValueChange={(value) => {
                const next = value as ChartRange
                if (allowRanges.includes(next)) setRange(next)
              }}
            >
              <TabsList
                className="h-8 rounded-md bg-muted/60 p-[3px]"
                aria-label="Chart time range"
              >
                {allowRanges.map((item) => (
                  <TabsTrigger
                    key={item}
                    value={item}
                    className="h-6 rounded-[5px] px-2.5 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"
                  >
                    {item}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
            {fixed ? null : (
              <Select
                value={machineId !== null ? String(machineId) : undefined}
                onValueChange={(value) => setSelectedId(Number(value))}
              >
                <SelectTrigger className="h-8 w-56 text-xs" aria-label="Machine">
                  <SelectValue placeholder="Select machine" />
                </SelectTrigger>
                <SelectContent>
                  {(machines ?? []).map((machine) => (
                    <SelectItem key={machine.id} value={String(machine.id)}>
                      <span className="font-mono">{machine.identifier}</span>
                      <span className="text-muted-foreground"> — {machine.name}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-1.5 text-xs"
              onClick={handleExport}
              disabled={points.length === 0}
              aria-label="Export selection as CSV"
            >
              <Download className="size-3.5" aria-hidden />
              CSV
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4">
        {machineId === null ? (
          <EmptyState
            title="No machine selected"
            description="Register a machine to plot its sensor history against configured thresholds."
          />
        ) : isLoading ? (
          <Skeleton className="h-[300px] w-full" role="status" aria-label="Loading sensor trend" />
        ) : queryError ? (
          <ErrorState title="Sensor trend unavailable" error={queryError} onRetry={() => retry()} />
        ) : points.length === 0 ? (
          <EmptyState
            title={`No ${meta.label.toLowerCase()} readings in this window`}
            description="Widen the time range or check that this machine is reporting data."
          />
        ) : (
          <ChartContainer config={chartConfig} className="h-[300px] w-full">
            <LineChart data={points} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--border)" strokeOpacity={0.6} />
              <XAxis
                dataKey="t"
                type="number"
                domain={['dataMin', 'dataMax']}
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={64}
                tickFormatter={(tick: number) => format(new Date(tick), X_TICK_PATTERN[range])}
                tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
              />
              <YAxis
                domain={[yMin, yMax]}
                tickLine={false}
                axisLine={false}
                width={46}
                tickMargin={4}
                tickFormatter={(tick: number) =>
                  tick.toFixed(meta.decimals > 1 ? 1 : meta.decimals)
                }
                tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }}
              />
              <ChartTooltip
                content={(props) => {
                  const { active, payload, label } = props
                  if (!active || !payload || payload.length === 0) return null
                  const row = payload[0]
                  const value = row?.value
                  if (typeof value !== 'number') return null
                  const point = row.payload as PlotPoint
                  return (
                    <div className="rounded-md border bg-popover px-3 py-2 text-xs shadow-md">
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(Number(label)), 'MMM d, HH:mm:ss')}
                      </p>
                      <p className="mt-0.5 font-medium tabular-nums">
                        {value.toFixed(meta.decimals)}{' '}
                        <span className="font-normal text-muted-foreground">{meta.unit}</span>
                      </p>
                      {point.count !== undefined ? (
                        <p className="mt-0.5 text-xs text-muted-foreground tabular-nums">
                          {(point.min ?? value).toFixed(meta.decimals)}–
                          {(point.max ?? value).toFixed(meta.decimals)} · n={point.count}
                        </p>
                      ) : null}
                    </div>
                  )
                }}
              />
              {/* Threshold horizon: tinted limit bands, then the limit rules. */}
              {warn !== null && crit !== null ? (
                <ReferenceArea
                  y1={warn}
                  y2={crit}
                  fill="var(--warning)"
                  fillOpacity={0.07}
                  ifOverflow="extendDomain"
                />
              ) : null}
              {crit !== null ? (
                <ReferenceArea
                  y1={crit}
                  y2={yMax}
                  fill="var(--danger)"
                  fillOpacity={0.07}
                  ifOverflow="extendDomain"
                />
              ) : null}
              {(anomalyQuery.data?.items ?? []).map((event) => (
                <ReferenceArea
                  key={`anomaly-${event.id}`}
                  x1={new Date(event.detected_at).getTime()}
                  x2={
                    event.resolved_at
                      ? new Date(event.resolved_at).getTime()
                      : (windowEndMs ?? points.at(-1)?.t ?? 0)
                  }
                  y1={yMin}
                  y2={yMax}
                  fill={event.severity === 'critical' ? 'var(--danger)' : 'var(--warning)'}
                  fillOpacity={0.1}
                  stroke={event.severity === 'critical' ? 'var(--danger)' : 'var(--warning)'}
                  strokeOpacity={0.35}
                  strokeDasharray="3 3"
                  ifOverflow="extendDomain"
                />
              ))}
              {warn !== null ? (
                <ReferenceLine
                  y={warn}
                  stroke="var(--warning)"
                  strokeDasharray="6 4"
                  strokeWidth={1}
                  label={{
                    value: `warn ${warn.toFixed(meta.decimals)}`,
                    position: 'insideTopRight',
                    fill: 'var(--warning)',
                    fontSize: 10,
                  }}
                />
              ) : null}
              {crit !== null ? (
                <ReferenceLine
                  y={crit}
                  stroke="var(--danger)"
                  strokeDasharray="6 4"
                  strokeWidth={1}
                  label={{
                    value: `crit ${crit.toFixed(meta.decimals)}`,
                    position: 'insideBottomRight',
                    fill: 'var(--danger)',
                    fontSize: 10,
                  }}
                />
              ) : null}
              <Line
                dataKey="v"
                type="monotone"
                stroke="var(--color-v)"
                strokeWidth={1.75}
                dot={false}
                isAnimationActive={false}
                name={meta.label}
              />
            </LineChart>
          </ChartContainer>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          {selectedMachine
            ? `${titleCase(selectedMachine.equipment_type)} · last ${range} · ${
                bucketed
                  ? `${points.length} buckets · avg with min–max range (aggregated from raw readings)`
                  : `${points.length} readings`
              }`
            : null}
          {warn === null && crit === null && machineId !== null
            ? ' · no thresholds configured for this metric'
            : ''}
        </p>
      </CardContent>
    </Card>
  )
}
