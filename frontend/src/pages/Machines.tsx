import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import { Plus } from 'lucide-react'

import { useMachines } from '@/api/queries'
import { Button } from '@/components/ui/button'
import { MachineFormDialog } from '@/components/machines/machine-form-dialog'
import { MachineFilters, type MachineFilterValue } from '@/components/machines/machine-filters'
import { MachinesTable } from '@/components/machines/machines-table'

const PAGE_SIZE = 25

const INITIAL_FILTERS: MachineFilterValue = {
  search: '',
  status: 'all',
  health: 'all',
  equipment_type: 'all',
  sort: 'identifier',
  order: 'asc',
}

export default function MachinesPage() {
  const [filters, setFilters] = useState<MachineFilterValue>(INITIAL_FILTERS)
  const [page, setPage] = useState(1)
  const [searchParams, setSearchParams] = useSearchParams()

  // Quick actions header links to /machines?create=1 — honor it here.
  const createOpen = searchParams.get('create') === '1'
  function setCreateOpen(open: boolean) {
    const next = new URLSearchParams(searchParams)
    if (open) next.set('create', '1')
    else next.delete('create')
    setSearchParams(next, { replace: true })
  }

  const query = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
      search: filters.search || undefined,
      status: filters.status === 'all' ? undefined : filters.status,
      health: filters.health === 'all' ? undefined : filters.health,
      equipment_type: filters.equipment_type === 'all' ? undefined : filters.equipment_type,
      sort: filters.sort,
      order: filters.order,
    }),
    [filters, page],
  )
  const { data, isLoading, error, refetch } = useMachines(query)

  function handleFilters(next: MachineFilterValue) {
    setFilters(next)
    setPage(1)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="max-w-2xl text-sm text-muted-foreground">
          The asset registry — condition is derived from the latest readings and open anomaly events
          for each machine.
        </p>
        <Button size="sm" className="gap-1.5" onClick={() => setCreateOpen(true)}>
          <Plus className="size-4" aria-hidden />
          Register machine
        </Button>
      </div>

      <MachineFilters value={filters} onChange={handleFilters} />

      <MachinesTable
        machines={data?.items}
        isLoading={isLoading}
        error={error}
        onRetry={() => void refetch()}
        page={page}
        pages={data?.pages ?? 0}
        total={data?.total ?? 0}
        onPageChange={setPage}
      />

      <MachineFormDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  )
}
