import { useEffect, useRef, useState } from 'react'
import { RotateCcw, Search } from 'lucide-react'

import type { EquipmentType, HealthStatus, MachineStatus } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { titleCase } from '@/lib/format'

export interface MachineFilterValue {
  search: string
  status: 'all' | MachineStatus
  health: 'all' | HealthStatus
  equipment_type: 'all' | EquipmentType
  sort: string
  order: 'asc' | 'desc'
}

const SORT_OPTIONS: { value: string; label: string }[] = [
  { value: 'identifier', label: 'Identifier' },
  { value: 'name', label: 'Name' },
  { value: 'equipment_type', label: 'Equipment type' },
  { value: 'created_at', label: 'Registered' },
  { value: 'status', label: 'Status' },
]

const EQUIPMENT_TYPES: EquipmentType[] = [
  'pump',
  'motor',
  'fan',
  'compressor',
  'bearing',
  'gearbox',
  'conveyor',
  'other',
]

const HEALTH_OPTIONS: HealthStatus[] = ['healthy', 'warning', 'critical', 'no_data', 'inactive']

function hasActiveFilters(value: MachineFilterValue): boolean {
  return (
    value.search !== '' ||
    value.status !== 'all' ||
    value.health !== 'all' ||
    value.equipment_type !== 'all'
  )
}

/**
 * Search + status/health/type filters + sort controls for the machines table.
 * Search input is debounced so typing does not hammer the API.
 */
export function MachineFilters({
  value,
  onChange,
}: {
  value: MachineFilterValue
  onChange: (next: MachineFilterValue) => void
}) {
  const [searchDraft, setSearchDraft] = useState(value.search)

  // Keep the latest filters for the debounce timer so a status/health change
  // made while the search is pending is not overwritten with a stale object.
  const valueRef = useRef(value)
  useEffect(() => {
    valueRef.current = value
  })

  useEffect(() => {
    if (searchDraft === value.search) return
    const timer = window.setTimeout(
      () => onChange({ ...valueRef.current, search: searchDraft }),
      300,
    )
    return () => window.clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchDraft])

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative min-w-56 grow sm:max-w-72">
        <Search
          className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <Input
          value={searchDraft}
          onChange={(event) => setSearchDraft(event.target.value)}
          placeholder="Search name or identifier…"
          className="h-9 pl-8 text-sm"
          aria-label="Search machines"
        />
      </div>

      <Select
        value={value.status}
        onValueChange={(next) =>
          onChange({ ...value, status: next as MachineFilterValue['status'] })
        }
      >
        <SelectTrigger className="h-9 w-32 text-sm" aria-label="Status filter">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All statuses</SelectItem>
          <SelectItem value="active">Active</SelectItem>
          <SelectItem value="inactive">Inactive</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={value.health}
        onValueChange={(next) =>
          onChange({ ...value, health: next as MachineFilterValue['health'] })
        }
      >
        <SelectTrigger className="h-9 w-36 text-sm" aria-label="Health filter">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All conditions</SelectItem>
          {HEALTH_OPTIONS.map((health) => (
            <SelectItem key={health} value={health}>
              {titleCase(health)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={value.equipment_type}
        onValueChange={(next) =>
          onChange({ ...value, equipment_type: next as MachineFilterValue['equipment_type'] })
        }
      >
        <SelectTrigger className="h-9 w-40 text-sm" aria-label="Equipment type filter">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All equipment</SelectItem>
          {EQUIPMENT_TYPES.map((type) => (
            <SelectItem key={type} value={type}>
              {titleCase(type)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <div className="ml-auto flex items-center gap-1.5">
        <Select value={value.sort} onValueChange={(next) => onChange({ ...value, sort: next })}>
          <SelectTrigger className="h-9 w-36 text-sm" aria-label="Sort machines by">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                Sort: {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          size="icon"
          className="size-9"
          aria-label={`Sort ${value.order === 'asc' ? 'descending' : 'ascending'}`}
          title={
            value.order === 'asc'
              ? 'Ascending — switch to descending'
              : 'Descending — switch to ascending'
          }
          onClick={() => onChange({ ...value, order: value.order === 'asc' ? 'desc' : 'asc' })}
        >
          <span aria-hidden className="text-sm leading-none">
            {value.order === 'asc' ? '↑' : '↓'}
          </span>
        </Button>
        {hasActiveFilters(value) ? (
          <Button
            variant="ghost"
            size="sm"
            className="h-9 gap-1.5 text-xs"
            onClick={() => {
              setSearchDraft('')
              onChange({
                search: '',
                status: 'all',
                health: 'all',
                equipment_type: 'all',
                sort: value.sort,
                order: value.order,
              })
            }}
          >
            <RotateCcw className="size-3.5" aria-hidden />
            Reset
          </Button>
        ) : null}
      </div>
    </div>
  )
}
