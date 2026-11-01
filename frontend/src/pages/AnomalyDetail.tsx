import { useState } from 'react'
import { Link, Navigate, useParams } from 'react-router'
import { ArrowLeft, ExternalLink, LineChart, MessageSquareText, StickyNote } from 'lucide-react'
import { toast } from 'sonner'

import { ApiError } from '@/api/client'
import { useAcknowledgeAnomaly, useAnomaly, useResolveAnomaly } from '@/api/queries'
import type { MetricName } from '@/api/types'
import { AnomalyStatusChip, SeverityChip } from '@/components/domain/chips'
import { ErrorState, PageLoading } from '@/components/feedback'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { METRIC_META, METRIC_ORDER, formatMetric, formatTimestamp, titleCase } from '@/lib/format'

function asMetric(metric: string): MetricName {
  return metric as MetricName
}

function ReadingRow({ metric, value }: { metric: MetricName; value: number | null }) {
  const meta = METRIC_META[metric]
  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <span className="text-sm">{meta.label}</span>
      <span className="text-sm tabular-nums">
        {formatMetric(metric, value)}
        <span className="ml-1 text-xs text-muted-foreground">{meta.unit}</span>
      </span>
    </div>
  )
}

export default function AnomalyDetailPage() {
  const params = useParams<{ anomalyId: string }>()
  const anomalyId = Number(params.anomalyId)
  const valid = Number.isInteger(anomalyId) && anomalyId > 0

  const anomalyQuery = useAnomaly(anomalyId, valid)
  const acknowledge = useAcknowledgeAnomaly(anomalyId)
  const resolve = useResolveAnomaly(anomalyId)
  const [noteDraft, setNoteDraft] = useState('')

  const anomaly = anomalyQuery.data
  const pending = acknowledge.isPending || resolve.isPending

  if (!valid) return <Navigate to="/anomalies" replace />
  if (anomalyQuery.isPending) return <PageLoading label="Loading anomaly event" />
  if (anomalyQuery.error || !anomaly) {
    return (
      <div className="space-y-4">
        <ErrorState
          title="Anomaly event unavailable"
          error={anomalyQuery.error}
          onRetry={() => void anomalyQuery.refetch()}
        />
        <div className="flex justify-center">
          <Button variant="outline" size="sm" asChild>
            <Link to="/anomalies">
              <ArrowLeft className="size-3.5" aria-hidden />
              Back to anomaly events
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  const metric = asMetric(anomaly.metric)
  const meta = METRIC_META[metric]
  const severityLabel = anomaly.severity === 'critical' ? 'Critical limit' : 'Warning limit'
  const status = anomaly.status

  async function act(kind: 'acknowledge' | 'resolve' | 'note') {
    const notes = noteDraft.trim() || undefined
    try {
      if (kind === 'acknowledge') {
        await acknowledge.mutateAsync(notes)
        toast.success('Anomaly acknowledged', {
          description: 'Acknowledgment timestamp recorded — the event stays open until resolved.',
        })
      } else if (kind === 'resolve') {
        await resolve.mutateAsync(notes)
        toast.success('Anomaly resolved', { description: 'Resolution timestamp recorded.' })
      } else {
        if (!notes) return
        if (status === 'acknowledged') await acknowledge.mutateAsync(notes)
        else if (status === 'resolved') await resolve.mutateAsync(notes)
        else return
        toast.success('Investigation note saved')
      }
      setNoteDraft('')
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Action failed')
    }
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <Button variant="ghost" size="sm" className="-ml-2 gap-1.5 text-xs" asChild>
            <Link to="/anomalies">
              <ArrowLeft className="size-3.5" aria-hidden />
              All anomaly events
            </Link>
          </Button>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            <h1 className="text-lg font-semibold tracking-tight">Event #{anomaly.id}</h1>
            <SeverityChip severity={anomaly.severity} />
            <AnomalyStatusChip status={anomaly.status} />
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">
            <Link
              to={`/machines/${anomaly.machine.id}`}
              className="font-mono font-medium text-foreground hover:underline"
            >
              {anomaly.machine.identifier}
            </Link>{' '}
            · {anomaly.machine.name} · {meta.label} · {titleCase(anomaly.method)} method
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-1.5" asChild>
            <Link to={`/machines/${anomaly.machine.id}`}>
              Open machine
              <ExternalLink className="size-3.5" aria-hidden />
            </Link>
          </Button>
        </div>
      </header>

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="border-b py-4">
            <CardTitle className="text-sm">Detected condition</CardTitle>
            <CardDescription className="text-xs">
              Threshold events compare the reading to your configured per-machine limits;
              statistical events have no fixed limit.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 p-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg border bg-muted/25 p-3">
                <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  Observed
                </p>
                <p className="mt-1 text-2xl font-semibold tabular-nums">
                  {formatMetric(metric, anomaly.observed_value)}
                  <span className="ml-1.5 text-sm font-normal text-muted-foreground">
                    {meta.unit}
                  </span>
                </p>
              </div>
              <div className="rounded-lg border bg-muted/25 p-3">
                <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  {anomaly.threshold_value !== null ? severityLabel : 'Configured limit'}
                </p>
                <p className="mt-1 text-2xl font-semibold tabular-nums">
                  {anomaly.threshold_value !== null ? (
                    <>
                      {formatMetric(metric, anomaly.threshold_value)}
                      <span className="ml-1.5 text-sm font-normal text-muted-foreground">
                        {meta.unit}
                      </span>
                    </>
                  ) : (
                    <span className="text-base font-normal text-muted-foreground">
                      none — {titleCase(anomaly.method)} detection
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div className="rounded-lg border-l-2 border-primary bg-muted/40 px-3 py-2.5">
              <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                <MessageSquareText className="size-3" aria-hidden />
                Explanation
              </p>
              <p className="mt-1 text-sm leading-relaxed">{anomaly.explanation}</p>
            </div>

            <dl className="grid gap-x-6 gap-y-2.5 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Detected</dt>
                <dd className="mt-0.5">
                  {formatTimestamp(anomaly.detected_at, 'MMM d, yyyy HH:mm:ss')}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Last seen</dt>
                <dd className="mt-0.5">
                  {formatTimestamp(anomaly.last_seen_at, 'MMM d, yyyy HH:mm:ss')}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                  Acknowledged
                </dt>
                <dd className="mt-0.5">
                  {anomaly.acknowledged_at
                    ? formatTimestamp(anomaly.acknowledged_at, 'MMM d, yyyy HH:mm:ss')
                    : '—'}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">Resolved</dt>
                <dd className="mt-0.5">
                  {anomaly.resolved_at
                    ? formatTimestamp(anomaly.resolved_at, 'MMM d, yyyy HH:mm:ss')
                    : '—'}
                </dd>
              </div>
            </dl>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Acknowledgment and resolution are separate: acknowledging records that the alert was
              reviewed, resolving closes the event. Both timestamps are kept on the history.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b py-4">
            <CardTitle className="text-sm">Contributing reading</CardTitle>
            <CardDescription className="text-xs">
              Reading #{anomaly.reading_id}
              {anomaly.reading
                ? ` · ${formatTimestamp(anomaly.reading.timestamp, 'MMM d, yyyy HH:mm:ss')}`
                : ''}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4">
            {anomaly.reading ? (
              <div className="divide-y">
                {METRIC_ORDER.map((name) => (
                  <ReadingRow key={name} metric={name} value={anomaly.reading?.[name] ?? null} />
                ))}
              </div>
            ) : (
              <p className="py-4 text-sm text-muted-foreground">
                The contributing reading is no longer available.
              </p>
            )}
            <Button variant="outline" size="sm" className="mt-4 w-full gap-1.5 text-xs" asChild>
              <Link
                to={`/explorer?machine_id=${anomaly.machine.id}&metric=${encodeURIComponent(anomaly.metric)}`}
              >
                <LineChart className="size-3.5" aria-hidden />
                View sensor history
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="border-b py-4">
          <div className="flex items-center gap-2">
            <StickyNote className="size-4 text-muted-foreground" aria-hidden />
            <div>
              <CardTitle className="text-sm">Investigation notes</CardTitle>
              <CardDescription className="text-xs">
                Notes are stored on the event when you acknowledge, resolve, or save them.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 p-4">
          {anomaly.notes ? (
            <div className="rounded-lg border bg-muted/30 p-3">
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{anomaly.notes}</p>
              <p className="mt-2 text-[11px] text-muted-foreground">
                Last updated on event history ·{' '}
                {anomaly.resolved_at
                  ? `resolved ${formatTimestamp(anomaly.resolved_at)}`
                  : anomaly.acknowledged_at
                    ? `acknowledged ${formatTimestamp(anomaly.acknowledged_at)}`
                    : `detected ${formatTimestamp(anomaly.detected_at)}`}
              </p>
            </div>
          ) : (
            <p className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
              No investigation notes yet.
            </p>
          )}

          <div className="grid gap-3">
            <Textarea
              value={noteDraft}
              onChange={(event) => setNoteDraft(event.target.value)}
              rows={3}
              placeholder="What did you check? What is the plan? (optional)"
              aria-label="Investigation note"
              disabled={pending}
            />
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-muted-foreground">
                {status === 'open'
                  ? 'Attach the note to your acknowledgment or resolution.'
                  : 'Updating a note keeps the existing lifecycle timestamps.'}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                {status === 'open' ? (
                  <>
                    <Button
                      size="sm"
                      className="gap-1.5"
                      disabled={pending}
                      onClick={() => void act('acknowledge')}
                    >
                      {acknowledge.isPending ? 'Saving…' : 'Acknowledge'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5"
                      disabled={pending}
                      onClick={() => void act('resolve')}
                    >
                      {resolve.isPending ? 'Saving…' : 'Resolve'}
                    </Button>
                  </>
                ) : null}
                {status === 'acknowledged' ? (
                  <>
                    <Button size="sm" disabled={pending} onClick={() => void act('resolve')}>
                      {resolve.isPending ? 'Saving…' : 'Resolve'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5"
                      disabled={pending || noteDraft.trim() === ''}
                      onClick={() => void act('note')}
                    >
                      {acknowledge.isPending ? 'Saving…' : 'Update note'}
                    </Button>
                  </>
                ) : null}
                {status === 'resolved' ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    disabled={pending || noteDraft.trim() === ''}
                    onClick={() => void act('note')}
                  >
                    {resolve.isPending ? 'Saving…' : 'Update note'}
                  </Button>
                ) : null}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
