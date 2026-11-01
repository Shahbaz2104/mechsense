import { Link } from 'react-router'
import { ChevronLeft, ChevronRight, StickyNote } from 'lucide-react'
import { toast } from 'sonner'

import { ApiError } from '@/api/client'
import { useAcknowledgeAnomaly, useResolveAnomaly } from '@/api/queries'
import type { AnomalyRead, MetricName } from '@/api/types'
import { AnomalyStatusChip, SeverityChip } from '@/components/domain/chips'
import { EmptyState, ErrorState } from '@/components/feedback'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { METRIC_META, formatMetric, timeAgo, titleCase } from '@/lib/format'

const METHOD_CELL = 'hidden text-xs text-muted-foreground md:table-cell'
const DETECTED_CELL = 'hidden text-right text-xs text-muted-foreground lg:table-cell'

function asMetric(metric: string): MetricName {
  return metric as MetricName
}

function metricLabel(metric: string): string {
  return METRIC_META[asMetric(metric)]?.label ?? titleCase(metric)
}

function metricUnit(metric: string): string | null {
  return METRIC_META[asMetric(metric)]?.unit ?? null
}

/** Acknowledge/Resolve quick actions for one row (spec §10 lifecycle). */
function RowActions({ anomaly }: { anomaly: AnomalyRead }) {
  const acknowledge = useAcknowledgeAnomaly(anomaly.id)
  const resolve = useResolveAnomaly(anomaly.id)
  const pending = acknowledge.isPending || resolve.isPending

  async function act(kind: 'acknowledge' | 'resolve') {
    try {
      if (kind === 'acknowledge') await acknowledge.mutateAsync()
      else await resolve.mutateAsync()
      toast.success(kind === 'acknowledge' ? 'Anomaly acknowledged' : 'Anomaly resolved', {
        description: `${anomaly.machine.identifier} · ${metricLabel(anomaly.metric)}`,
      })
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Action failed')
    }
  }

  return (
    <div className="flex items-center justify-end gap-1.5">
      {anomaly.status === 'open' ? (
        <Button
          variant="ghost"
          size="sm"
          className="h-7 gap-1 px-2 text-xs"
          disabled={pending}
          onClick={() => void act('acknowledge')}
        >
          {acknowledge.isPending ? '…' : 'Acknowledge'}
        </Button>
      ) : null}
      {anomaly.status !== 'resolved' ? (
        <Button
          variant="ghost"
          size="sm"
          className="h-7 gap-1 px-2 text-xs"
          disabled={pending}
          onClick={() => void act('resolve')}
        >
          {resolve.isPending ? '…' : 'Resolve'}
        </Button>
      ) : null}
    </div>
  )
}

export function AnomaliesTable({
  anomalies,
  isLoading,
  error,
  onRetry,
  page,
  pages,
  total,
  onPageChange,
}: {
  anomalies: AnomalyRead[] | undefined
  isLoading: boolean
  error: unknown
  onRetry: () => void
  page: number
  pages: number
  total: number
  onPageChange: (page: number) => void
}) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-3 p-4" role="status" aria-label="Loading anomaly events">
            <span className="sr-only">Loading anomaly events…</span>
            {Array.from({ length: 6 }, (_, index) => (
              <div key={index} className="h-5 w-full animate-pulse rounded bg-muted" />
            ))}
          </div>
        ) : error ? (
          <div className="p-4">
            <ErrorState title="Anomaly events unavailable" error={error} onRetry={onRetry} />
          </div>
        ) : !anomalies || anomalies.length === 0 ? (
          <EmptyState
            title="No anomaly events match this view"
            description="Adjust the filters, or generate readings to see detection events here."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="pl-4">Severity</TableHead>
                <TableHead>Machine</TableHead>
                <TableHead>Sensor</TableHead>
                <TableHead className="text-right">Observed</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className={METHOD_CELL}>Method</TableHead>
                <TableHead className={DETECTED_CELL}>Detected</TableHead>
                <TableHead className="text-right">Actions</TableHead>
                <TableHead className="w-8" aria-label="Open" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {anomalies.map((anomaly) => {
                const unit = metricUnit(anomaly.metric)
                return (
                  <TableRow key={anomaly.id} className="cursor-pointer">
                    <TableCell className="pl-4">
                      <Link
                        to={`/anomalies/${anomaly.id}`}
                        className="inline-flex rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        aria-label={`Open event ${anomaly.id}`}
                      >
                        <SeverityChip severity={anomaly.severity} />
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link
                        to={`/machines/${anomaly.machine.id}`}
                        className="grid gap-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <span className="font-mono text-xs font-medium">
                          {anomaly.machine.identifier}
                        </span>
                        <span className="truncate text-xs text-muted-foreground">
                          {anomaly.machine.name}
                        </span>
                      </Link>
                    </TableCell>
                    <TableCell className="text-xs">{metricLabel(anomaly.metric)}</TableCell>
                    <TableCell className="text-right text-sm tabular-nums">
                      {formatMetric(asMetric(anomaly.metric), anomaly.observed_value)}
                      {unit ? (
                        <span className="ml-1 text-xs text-muted-foreground">{unit}</span>
                      ) : null}
                      <span className="block text-[11px] font-normal text-muted-foreground">
                        {anomaly.threshold_value !== null
                          ? `limit ${formatMetric(asMetric(anomaly.metric), anomaly.threshold_value)}`
                          : 'no limit'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1.5">
                        <AnomalyStatusChip status={anomaly.status} />
                        {anomaly.notes ? (
                          <StickyNote
                            className="size-3.5 text-muted-foreground"
                            aria-label="Has investigation notes"
                          />
                        ) : null}
                      </span>
                    </TableCell>
                    <TableCell className={METHOD_CELL}>{titleCase(anomaly.method)}</TableCell>
                    <TableCell className={DETECTED_CELL}>{timeAgo(anomaly.detected_at)}</TableCell>
                    <TableCell>
                      <RowActions anomaly={anomaly} />
                    </TableCell>
                    <TableCell className="pr-3 text-right text-muted-foreground">
                      <Link
                        to={`/anomalies/${anomaly.id}`}
                        aria-label={`Open event ${anomaly.id}`}
                        className="inline-flex rounded-md p-1 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <ChevronRight className="size-4" aria-hidden />
                      </Link>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        )}

        {error ? null : (
          <div className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3">
            <p className="text-xs text-muted-foreground">
              {total} event{total === 1 ? '' : 's'}
              {pages > 1 ? ` · page ${page} of ${pages}` : ''}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1 text-xs"
                disabled={page <= 1 || isLoading}
                onClick={() => onPageChange(page - 1)}
              >
                <ChevronLeft className="size-3.5" aria-hidden />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1 text-xs"
                disabled={page >= pages || isLoading}
                onClick={() => onPageChange(page + 1)}
              >
                Next
                <ChevronRight className="size-3.5" aria-hidden />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
