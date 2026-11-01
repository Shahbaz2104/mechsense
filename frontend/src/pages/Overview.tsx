import { useState } from 'react'

import type { DashboardPeriod } from '@/api/types'
import { useDashboard } from '@/api/queries'
import { ErrorState } from '@/components/feedback'
import { MetricStrip, MetricStripSkeleton } from '@/components/overview/metric-strip'
import { MachineHealthTable } from '@/components/overview/machine-health-table'
import { PeriodControl } from '@/components/overview/period-control'
import { RecentAnomalies } from '@/components/overview/recent-anomalies'
import { SensorTrendChart } from '@/components/overview/sensor-trend-chart'
import { formatTimestamp, PERIOD_LABEL } from '@/lib/format'

export default function OverviewPage() {
  const [period, setPeriod] = useState<DashboardPeriod>('7d')
  const { data, isLoading, error, refetch } = useDashboard(period)

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">
            Fleet condition over the {PERIOD_LABEL[period]}
            {data ? ` · updated ${formatTimestamp(data.summary.generated_at, 'HH:mm:ss')}` : ''}
          </p>
        </div>
        <PeriodControl value={period} onChange={setPeriod} />
      </div>

      {error ? (
        <ErrorState title="Dashboard unavailable" error={error} onRetry={() => refetch()} />
      ) : isLoading || !data ? (
        <MetricStripSkeleton />
      ) : (
        <MetricStrip summary={data.summary} period={period} />
      )}

      <div className="grid gap-5 lg:grid-cols-5">
        <MachineHealthTable
          machines={data?.machines}
          isLoading={isLoading}
          error={error}
          onRetry={() => refetch()}
          className="lg:col-span-3"
        />
        <RecentAnomalies className="lg:col-span-2" />
      </div>

      <SensorTrendChart machines={data?.machines ?? []} />
    </div>
  )
}
