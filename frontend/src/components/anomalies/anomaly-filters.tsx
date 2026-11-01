import { useEffect, useRef, useState } from 'react'
import { RotateCcw, Search } from 'lucide-react'

import type { AnomalyMethod, AnomalySeverity, MachineSummary } from '@/api/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { METRIC_META, METRIC_ORDER, titleCase } from '@/lib/format'

export interface AnomalyFilterValue {
  search: string
  status: 'all' | 'open' | 'acknowledged' | 'resolved'
  severity: 'all' | AnomalySeverity
  method: 'all' | AnomalyMethod
  metric: 'all' | string
  machine_id: 'all' | number
  /** UTC calendar dates (inclusive): '' = open-ended. */
  from: string
  to: string
  sort: string
  order: 'asc' | 'desc'
}

const SORT_OPTIONS: { value: string; label: string }[] = [
  { value: 'detected_at', label: 'Detected' },
  { value: 'severity', label: 'Severity' },
  { value: 'metric', label: 'Metric' },
  { value: 'observed_value', label: 'Value' },
  { value: 'status', label: 'Status' },
]

const METHODS: AnomalyMethod[] = ['threshold', 'statistical']

function hasActiveFilters(value: AnomalyFilterValue): boolean {
  return (
    value.search !== '' ||
    value.status !== 'all' ||
    value.severity !== 'all' ||
    value.method !== 'all' ||
    value.metric !== 'all' ||
    value.machine_id !== 'all' ||
    value.from !== '' ||
    value.to !== ''
  )
}

/**
 * Search + severity/method/metric/machine + date-range + sort controls for
 * the anomaly table. Lifecycle status lives in tabs on the page itself.
 */
export function AnomalyFilters({
  value,
  onChange,
  machines,
}: {
  value: AnomalyFilterValue
  onChange: (next: AnomalyFilterValue) => void
  machines: MachineSummary[]
}) {
  const [searchDraft, setSearchDraft] = useState(value.search)

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
          placeholder="Search explanations or machines…"
          className="h-9 pl-8 text-sm"
          aria-label="Search anomaly events"
        />
      </div>

      <Select
        value={value.severity}
        onValueChange={(next) =>
          onChange({ ...value, severity: next as AnomalyFilterValue['severity'] })
        }
      >
        <SelectTrigger className="h-9 w-32 text-sm" aria-label="Severity filter">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All severities</SelectItem>
          <SelectItem value="warning">Warning</SelectItem>
          <SelectItem value="critical">Critical</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={value.method}
        onValueChange={(next) =>
          onChange({ ...value, method: next as AnomalyFilterValue['method'] })
        }
      >
        <SelectTrigger className="h-9 w-36 text-sm" aria-label="Method filter">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All methods</SelectItem>
          {METHODS.map((method) => (
            <SelectItem key={method} value={method}>
              {titleCase(method)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={value.metric} onValueChange={(next) => onChange({ ...value, metric: next })}>
        <SelectTrigger className="h-9 w-36 text-sm" aria-label="Sensor metric filter">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All sensors</SelectItem>
          {METRIC_ORDER.map((metric) => (
            <SelectItem key={metric} value={metric}>
              {METRIC_META[metric].shortLabel}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={value.machine_id === 'all' ? 'all' : String(value.machine_id)}
        onValueChange={(next) =>
          onChange({ ...value, machine_id: next === 'all' ? 'all' : Number(next) })
        }
      >
        <SelectTrigger className="h-9 w-44 text-sm" aria-label="Machine filter">
          <SelectValue placeholder="All machines" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All machines</SelectItem>
          {machines.map((machine) => (
            <SelectItem key={machine.id} value={String(machine.id)}>
              <span className="font-mono">{machine.identifier}</span>
              <span className="text-muted-foreground"> — {machine.name}</span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <div className="flex items-center gap-1.5">
        <Input
          type="date"
          value={value.from}
          onChange={(event) => onChange({ ...value, from: event.target.value })}
          className="h-9 w-36 text-sm"
          aria-label="Detected from date (UTC)"
          title="Detected from (UTC date)"
        />
        <span className="text-xs text-muted-foreground">→</span>
        <Input
          type="date"
          value={value.to}
          onChange={(event) => onChange({ ...value, to: event.target.value })}
          className="h-9 w-36 text-sm"
          aria-label="Detected to date (UTC)"
          title="Detected to (UTC date)"
        />
      </div>

      <div className="ml-auto flex items-center gap-1.5">
        <Select value={value.sort} onValueChange={(next) => onChange({ ...value, sort: next })}>
          <SelectTrigger className="h-9 w-32 text-sm" aria-label="Sort events by">
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
                status: value.status,
                severity: 'all',
                method: 'all',
                metric: 'all',
                machine_id: 'all',
                from: '',
                to: '',
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
