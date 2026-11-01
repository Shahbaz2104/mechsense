import type { MachineSummary } from '@/api/types'
import { MetricChart } from '@/components/charts/metric-chart'

/** Overview binding: raw ranges, machine select, worst-condition default. */
export function SensorTrendChart({
  machines,
  className,
}: {
  machines: MachineSummary[]
  className?: string
}) {
  return <MetricChart machines={machines} className={className} />
}
