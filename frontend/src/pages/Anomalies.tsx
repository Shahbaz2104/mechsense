import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'

import { useAnomalies, useMachines } from '@/api/queries'
import { AnomalyFilters, type AnomalyFilterValue } from '@/components/anomalies/anomaly-filters'
import { AnomaliesTable } from '@/components/anomalies/anomalies-table'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'

const PAGE_SIZE = 25

type StatusTab = AnomalyFilterValue['status']

const STATUS_TABS: { value: StatusTab; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'resolved', label: 'Resolved' },
]

export default function AnomaliesPage() {
  const [searchParams] = useSearchParams()

  const [filters, setFilters] = useState<AnomalyFilterValue>(() => {
    const machineParam = Number(searchParams.get('machine_id'))
    const initialMachine = Number.isInteger(machineParam) && machineParam > 0 ? machineParam : 'all'
    return {
      search: '',
      status: 'all',
      severity: 'all',
      method: 'all',
      metric: 'all',
      machine_id: initialMachine as 'all' | number,
      from: '',
      to: '',
      sort: 'detected_at',
      order: 'desc',
    }
  })
  const [page, setPage] = useState(1)

  const machinesQuery = useMachines({ page_size: 100, sort: 'identifier' })

  const query = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
      q: filters.search || undefined,
      status: filters.status === 'all' ? undefined : filters.status,
      severity: filters.severity === 'all' ? undefined : filters.severity,
      method: filters.method === 'all' ? undefined : filters.method,
      metric: filters.metric === 'all' ? undefined : filters.metric,
      machine_id: filters.machine_id === 'all' ? undefined : filters.machine_id,
      start: filters.from ? `${filters.from}T00:00:00` : undefined,
      end: filters.to ? `${filters.to}T23:59:59` : undefined,
      sort: filters.sort,
      order: filters.order,
    }),
    [filters, page],
  )
  const { data, isLoading, error, refetch } = useAnomalies(query)

  function handleFilters(next: AnomalyFilterValue) {
    setFilters(next)
    setPage(1)
  }

  const activeMachine =
    filters.machine_id === 'all'
      ? null
      : (machinesQuery.data?.items.find((machine) => machine.id === filters.machine_id) ?? null)

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="max-w-2xl text-sm text-muted-foreground">
          The detection feed — acknowledgment records review, resolution closes the event; both
          timestamps are kept on the event history.
        </p>
        <Tabs
          value={filters.status}
          onValueChange={(next) => handleFilters({ ...filters, status: next as StatusTab })}
        >
          <TabsList className="h-9" aria-label="Event lifecycle status">
            {STATUS_TABS.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value} className="text-xs">
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {activeMachine ? (
        <p className="text-xs text-muted-foreground">
          Showing events for{' '}
          <span className="font-mono font-medium text-foreground">{activeMachine.identifier}</span>{' '}
          — {activeMachine.name}
          <button
            type="button"
            className="ml-2 underline underline-offset-2 hover:text-foreground"
            onClick={() => handleFilters({ ...filters, machine_id: 'all' })}
          >
            clear machine filter
          </button>
        </p>
      ) : null}

      <AnomalyFilters
        value={filters}
        onChange={handleFilters}
        machines={machinesQuery.data?.items ?? []}
      />

      <AnomaliesTable
        anomalies={data?.items}
        isLoading={isLoading}
        error={error}
        onRetry={() => void refetch()}
        page={page}
        pages={data?.pages ?? 0}
        total={data?.total ?? 0}
        onPageChange={setPage}
      />
    </div>
  )
}
