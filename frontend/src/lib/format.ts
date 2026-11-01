import { format, formatDistanceToNow } from 'date-fns'
import type { AnomalySeverity, DashboardPeriod, HealthStatus, MetricName } from '@/api/types'

export interface MetricMeta {
  label: string
  shortLabel: string
  unit: string
  decimals: number
}

export const METRIC_META: Record<MetricName, MetricMeta> = {
  vibration_rms: { label: 'Vibration RMS', shortLabel: 'Vibration', unit: 'mm/s', decimals: 2 },
  temperature: { label: 'Temperature', shortLabel: 'Temp', unit: '°C', decimals: 1 },
  rpm: { label: 'Rotational speed', shortLabel: 'Speed', unit: 'rpm', decimals: 0 },
  load_pct: { label: 'Machine load', shortLabel: 'Load', unit: '%', decimals: 1 },
  pressure: { label: 'Pressure', shortLabel: 'Pressure', unit: 'bar', decimals: 2 },
}

export const METRIC_ORDER: MetricName[] = [
  'vibration_rms',
  'temperature',
  'rpm',
  'load_pct',
  'pressure',
]

export function formatMetric(metric: MetricName, value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const meta = METRIC_META[metric]
  return value.toFixed(meta.decimals)
}

export const HEALTH_LABEL: Record<HealthStatus, string> = {
  healthy: 'Healthy',
  warning: 'Warning',
  critical: 'Critical',
  inactive: 'Inactive',
  no_data: 'No data',
}

/** Display order for health rows: act on problems first. */
const HEALTH_RANK: Record<HealthStatus, number> = {
  critical: 0,
  warning: 1,
  no_data: 2,
  inactive: 3,
  healthy: 4,
}

export function healthRank(health: HealthStatus): number {
  return HEALTH_RANK[health]
}

export const SEVERITY_LABEL: Record<AnomalySeverity, string> = {
  warning: 'Warning',
  critical: 'Critical',
}

export const ANOMALY_STATUS_LABEL = {
  open: 'Open',
  acknowledged: 'Acknowledged',
  resolved: 'Resolved',
} as const

export const PERIOD_LABEL: Record<DashboardPeriod, string> = {
  '1h': 'last hour',
  '6h': 'last 6 hours',
  '24h': 'last 24 hours',
  '7d': 'last 7 days',
  '30d': 'last 30 days',
}

export function titleCase(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return 'never'
  return formatDistanceToNow(new Date(iso), { addSuffix: true })
}

export function formatTimestamp(iso: string, pattern = 'MMM d, HH:mm:ss'): string {
  return format(new Date(iso), pattern)
}
