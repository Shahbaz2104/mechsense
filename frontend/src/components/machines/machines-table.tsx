import { Link } from 'react-router'
import { ChevronLeft, ChevronRight, TriangleAlert } from 'lucide-react'

import type { MachineSummary } from '@/api/types'
import { Badge } from '@/components/ui/badge'
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
import { EmptyState, ErrorState } from '@/components/feedback'
import { HealthChip, MachineStatusChip } from '@/components/domain/chips'
import { formatMetric, timeAgo } from '@/lib/format'
import { cn } from '@/lib/utils'

const TYPE_CELL = 'hidden capitalize text-xs text-muted-foreground md:table-cell'
const HEALTH_CELL = 'hidden lg:table-cell'
const TEMP_CELL = 'hidden text-right text-sm tabular-nums sm:table-cell'
const LAST_CELL = 'hidden text-right text-xs text-muted-foreground lg:table-cell'
const ALERT_CELL = 'hidden xl:table-cell'

export function MachinesTable({
  machines,
  isLoading,
  error,
  onRetry,
  page,
  pages,
  total,
  onPageChange,
  className,
}: {
  machines: MachineSummary[] | undefined
  isLoading: boolean
  error: unknown
  onRetry: () => void
  page: number
  pages: number
  total: number
  onPageChange: (page: number) => void
  className?: string
}) {
  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-3 p-4" role="status" aria-label="Loading machines">
            <span className="sr-only">Loading machines…</span>
            {Array.from({ length: 6 }, (_, index) => (
              <div key={index} className="h-5 w-full animate-pulse rounded bg-muted" />
            ))}
          </div>
        ) : error ? (
          <div className="p-4">
            <ErrorState title="Machines unavailable" error={error} onRetry={onRetry} />
          </div>
        ) : !machines || machines.length === 0 ? (
          <EmptyState
            title="No machines match this view"
            description="Adjust the filters, or register a new machine to start monitoring it."
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="pl-4">Machine</TableHead>
                <TableHead className={TYPE_CELL}>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className={HEALTH_CELL}>Condition</TableHead>
                <TableHead className="text-right">Vibration</TableHead>
                <TableHead className={TEMP_CELL}>Temperature</TableHead>
                <TableHead className={LAST_CELL}>Last reading</TableHead>
                <TableHead className={ALERT_CELL}>Latest alert</TableHead>
                <TableHead className="w-8" aria-label="Open" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {machines.map((machine) => (
                <TableRow key={machine.id} className="cursor-pointer">
                  <TableCell className="pl-4">
                    <Link
                      to={`/machines/${machine.id}`}
                      className="grid gap-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <span className="flex items-center gap-2 font-mono text-xs font-medium">
                        {machine.identifier}
                        {machine.open_anomaly_count > 0 ? (
                          <Badge
                            variant="outline"
                            className={cn(
                              'gap-1 px-1.5 text-[10px] font-medium',
                              machine.health_status === 'critical'
                                ? 'border-danger/40 bg-danger/10 text-danger'
                                : 'border-warning/40 bg-warning/10 text-warning',
                            )}
                          >
                            <TriangleAlert className="size-2.5" aria-hidden />
                            {machine.open_anomaly_count}
                          </Badge>
                        ) : null}
                      </span>
                      <span className="truncate text-xs text-muted-foreground">{machine.name}</span>
                    </Link>
                  </TableCell>
                  <TableCell className={TYPE_CELL}>{machine.equipment_type}</TableCell>
                  <TableCell>
                    <MachineStatusChip status={machine.status} />
                  </TableCell>
                  <TableCell className={HEALTH_CELL}>
                    <HealthChip health={machine.health_status} />
                  </TableCell>
                  <TableCell className="text-right text-sm tabular-nums">
                    {formatMetric('vibration_rms', machine.vibration_rms)}
                    <span className="ml-1 text-xs text-muted-foreground">mm/s</span>
                  </TableCell>
                  <TableCell className={TEMP_CELL}>
                    {formatMetric('temperature', machine.temperature)}
                    <span className="ml-1 text-xs text-muted-foreground">°C</span>
                  </TableCell>
                  <TableCell className={LAST_CELL}>{timeAgo(machine.latest_reading_at)}</TableCell>
                  <TableCell className={ALERT_CELL}>
                    {machine.latest_anomaly ? (
                      <span className="flex items-center gap-1.5 text-xs">
                        <span
                          className={cn(
                            'size-1.5 rounded-full',
                            machine.latest_anomaly.severity === 'critical'
                              ? 'bg-danger'
                              : 'bg-warning',
                          )}
                          aria-hidden
                        />
                        <span className="text-muted-foreground">
                          {timeAgo(machine.latest_anomaly.detected_at)}
                        </span>
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="pr-3 text-right text-muted-foreground">
                    <Link
                      to={`/machines/${machine.id}`}
                      aria-label={`Open ${machine.identifier}`}
                      className="inline-flex rounded-md p-1 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <ChevronRight className="size-4" aria-hidden />
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}

        {error ? null : (
          <div className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3">
            <p className="text-xs text-muted-foreground">
              {total} machine{total === 1 ? '' : 's'}
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
