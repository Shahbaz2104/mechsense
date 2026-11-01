import { Link } from 'react-router'
import { ArrowRight, TriangleAlert } from 'lucide-react'

import type { MachineSummary } from '@/api/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { EmptyState, ErrorState } from '@/components/feedback'
import { HealthChip } from '@/components/domain/chips'
import { formatMetric, healthRank, timeAgo } from '@/lib/format'
import { cn } from '@/lib/utils'

function sortFleet(machines: MachineSummary[]): MachineSummary[] {
  return [...machines].sort((a, b) => {
    const byHealth = healthRank(a.health_status) - healthRank(b.health_status)
    if (byHealth !== 0) return byHealth
    return a.identifier.localeCompare(b.identifier)
  })
}

export function MachineHealthTable({
  machines,
  isLoading,
  error,
  onRetry,
  className,
}: {
  machines: MachineSummary[] | undefined
  isLoading: boolean
  error: unknown
  onRetry: () => void
  className?: string
}) {
  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="flex flex-row items-start justify-between gap-4 border-b py-4">
        <div>
          <CardTitle className="text-sm">Fleet health</CardTitle>
          <CardDescription className="text-xs">
            Derived from latest readings and open events · problems first
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" className="gap-1 text-xs" asChild>
          <Link to="/machines">
            All machines
            <ArrowRight className="size-3.5" aria-hidden />
          </Link>
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-3 p-4" role="status" aria-label="Loading fleet health">
            <span className="sr-only">Loading fleet health…</span>
            <div className="h-4 w-full animate-pulse rounded bg-muted" />
            <div className="h-4 w-5/6 animate-pulse rounded bg-muted" />
            <div className="h-4 w-4/6 animate-pulse rounded bg-muted" />
          </div>
        ) : error ? (
          <div className="p-4">
            <ErrorState title="Fleet health unavailable" error={error} onRetry={onRetry} />
          </div>
        ) : !machines || machines.length === 0 ? (
          <EmptyState
            title="No machines registered"
            description="Register your first machine or import a CSV to start monitoring fleet condition."
            icon={<TriangleAlert className="size-5" aria-hidden />}
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="pl-4">Machine</TableHead>
                <TableHead className="hidden md:table-cell">Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Vibration</TableHead>
                <TableHead className="hidden text-right sm:table-cell">Temperature</TableHead>
                <TableHead className="hidden text-right lg:table-cell">Last reading</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortFleet(machines).map((machine) => (
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
                  <TableCell className="hidden capitalize text-xs text-muted-foreground md:table-cell">
                    {machine.equipment_type}
                  </TableCell>
                  <TableCell>
                    <HealthChip health={machine.health_status} />
                  </TableCell>
                  <TableCell className="text-right text-sm tabular-nums">
                    {formatMetric('vibration_rms', machine.vibration_rms)}
                    <span className="ml-1 text-xs text-muted-foreground">mm/s</span>
                  </TableCell>
                  <TableCell className="hidden text-right text-sm tabular-nums sm:table-cell">
                    {formatMetric('temperature', machine.temperature)}
                    <span className="ml-1 text-xs text-muted-foreground">°C</span>
                  </TableCell>
                  <TableCell className="hidden text-right text-xs text-muted-foreground lg:table-cell">
                    {timeAgo(machine.latest_reading_at)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
