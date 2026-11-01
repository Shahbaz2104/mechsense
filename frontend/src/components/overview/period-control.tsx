import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { DashboardPeriod } from '@/api/types'

const PERIODS: { value: DashboardPeriod; label: string }[] = [
  { value: '1h', label: '1h' },
  { value: '6h', label: '6h' },
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
  { value: '30d', label: '30d' },
]

export function PeriodControl({
  value,
  onChange,
}: {
  value: DashboardPeriod
  onChange: (period: DashboardPeriod) => void
}) {
  return (
    <Tabs value={value} onValueChange={(next) => onChange(next as DashboardPeriod)}>
      <TabsList className="h-8 rounded-md bg-muted/60 p-[3px]" aria-label="Summary period">
        {PERIODS.map((period) => (
          <TabsTrigger
            key={period.value}
            value={period.value}
            className="h-6 rounded-[5px] px-2.5 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm"
          >
            {period.label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  )
}
