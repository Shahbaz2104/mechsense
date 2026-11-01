import { Link } from 'react-router'
import { ArrowRight, CircleCheck } from 'lucide-react'

import { useAnomalies } from '@/api/queries'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState, ErrorState } from '@/components/feedback'
import { AnomalyStatusChip, SeverityChip } from '@/components/domain/chips'
import { METRIC_META, titleCase, timeAgo } from '@/lib/format'
import { cn } from '@/lib/utils'

export function RecentAnomalies({ className }: { className?: string }) {
  const { data, isLoading, error, refetch } = useAnomalies({ page: 1, page_size: 6, order: 'desc' })

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="flex flex-row items-start justify-between gap-4 border-b py-4">
        <div>
          <CardTitle className="text-sm">Recent anomalies</CardTitle>
          <CardDescription className="text-xs">
            {data ? `${data.total} events detected` : 'Latest detections across the fleet'}
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" className="gap-1 text-xs" asChild>
          <Link to="/anomalies">
            All events
            <ArrowRight className="size-3.5" aria-hidden />
          </Link>
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-3 p-4" role="status" aria-label="Loading recent anomalies">
            <span className="sr-only">Loading recent anomalies…</span>
            {Array.from({ length: 4 }, (_, i) => (
              <div key={i} className="h-10 w-full animate-pulse rounded bg-muted" />
            ))}
          </div>
        ) : error ? (
          <div className="p-4">
            <ErrorState title="Anomaly feed unavailable" error={error} onRetry={() => refetch()} />
          </div>
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="No anomaly events"
            description="Every monitored machine is running inside its configured thresholds."
            icon={<CircleCheck className="size-5" aria-hidden />}
          />
        ) : (
          <ul className="divide-y">
            {data.items.map((event) => {
              const meta = METRIC_META[event.metric as keyof typeof METRIC_META]
              return (
                <li key={event.id}>
                  <Link
                    to={`/anomalies?event=${event.id}`}
                    className="grid gap-1.5 px-4 py-3 transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <div className="flex items-center gap-2">
                      <SeverityChip severity={event.severity} />
                      <span className="truncate font-mono text-xs font-medium">
                        {event.machine.identifier}
                      </span>
                      <span className="truncate text-xs text-muted-foreground">
                        {meta ? meta.label : titleCase(event.metric)}
                      </span>
                      <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                        {timeAgo(event.detected_at)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span className="tabular-nums">
                        {event.observed_value.toFixed(2)} {meta?.unit ?? ''}
                        {event.threshold_value !== null ? (
                          <>
                            {' · limit '}
                            <span className="tabular-nums text-foreground/80">
                              {event.threshold_value.toFixed(2)}
                            </span>
                          </>
                        ) : null}
                      </span>
                      {event.status !== 'open' ? (
                        <AnomalyStatusChip status={event.status} className="ml-auto" />
                      ) : null}
                    </div>
                  </Link>
                </li>
              )
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
