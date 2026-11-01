import { useSearchParams } from 'react-router'

import { useMachines } from '@/api/queries'
import type { MetricName } from '@/api/types'
import { MetricChart } from '@/components/charts/metric-chart'
import { EngineeringContext } from '@/components/domain/engineering-context'
import { Card, CardContent } from '@/components/ui/card'

const METRIC_NAMES: MetricName[] = ['vibration_rms', 'temperature', 'rpm', 'load_pct', 'pressure']

/**
 * Cross-machine sensor inspector: pick a machine, a metric, and a window.
 * Deep links from anomaly events arrive as ?machine_id=&metric=.
 */
export default function SensorExplorerPage() {
  const [searchParams] = useSearchParams()
  const machinesQuery = useMachines({ page_size: 100, sort: 'identifier' })

  const paramMachineId = Number(searchParams.get('machine_id'))
  const initialMachineId =
    Number.isInteger(paramMachineId) && paramMachineId > 0 ? paramMachineId : undefined

  const paramMetric = searchParams.get('metric') as MetricName | null
  const initialMetric = paramMetric && METRIC_NAMES.includes(paramMetric) ? paramMetric : undefined

  return (
    <div className="space-y-5">
      <p className="max-w-3xl text-sm text-muted-foreground">
        Inspect any machine's sensor history against its configured thresholds. Ranges up to 7 days
        plot raw readings; 30 days aggregates into 12-hour buckets (avg/min/max).
      </p>

      <MetricChart
        machines={machinesQuery.data?.items ?? []}
        allowRanges={['1h', '6h', '24h', '7d', '30d']}
        initialMachineId={initialMachineId}
        initialMetric={initialMetric}
      />

      <Card>
        <CardContent className="p-4">
          <EngineeringContext />
        </CardContent>
      </Card>
    </div>
  )
}
