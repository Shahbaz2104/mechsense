/**
 * Types mirroring the FastAPI/Pydantic schemas under backend/app/schemas.
 * Keep this file in sync with the API contract (see plan.md §11).
 */

export type EquipmentType =
  'pump' | 'motor' | 'fan' | 'compressor' | 'bearing' | 'gearbox' | 'conveyor' | 'other'

export type MachineStatus = 'active' | 'inactive'
export type HealthStatus = 'healthy' | 'warning' | 'critical' | 'inactive' | 'no_data'

export type MetricName = 'vibration_rms' | 'temperature' | 'rpm' | 'load_pct' | 'pressure'

export type AnomalySeverity = 'warning' | 'critical'
export type AnomalyStatus = 'open' | 'acknowledged' | 'resolved'
export type AnomalyMethod = 'threshold' | 'statistical'
export type ReadingSource = 'simulated' | 'imported' | 'live'

export type DashboardPeriod = '1h' | '6h' | '24h' | '7d' | '30d'

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface MetricThresholds {
  warning: number | null
  critical: number | null
}

/** Per-machine threshold configuration keyed by metric name (JSONB on the backend). */
export type MachineThresholds = Partial<Record<MetricName, MetricThresholds>>

export interface AnomalyBrief {
  id: number
  metric: string
  severity: AnomalySeverity
  detected_at: string
  status: AnomalyStatus
}

export interface MachineSummary {
  id: number
  identifier: string
  name: string
  equipment_type: EquipmentType
  status: MachineStatus
  health_status: HealthStatus
  latest_reading_at: string | null
  vibration_rms: number | null
  temperature: number | null
  latest_anomaly: AnomalyBrief | null
  open_anomaly_count: number
}

export interface MachineRead {
  id: number
  identifier: string
  name: string
  equipment_type: EquipmentType
  location: string | null
  manufacturer: string | null
  model: string | null
  installation_date: string | null
  status: MachineStatus
  description: string | null
  thresholds: MachineThresholds
  created_at: string
  updated_at: string
}

export interface ReadingRead {
  id: number
  machine_id: number
  timestamp: string
  vibration_rms: number
  temperature: number
  rpm: number
  load_pct: number
  pressure: number | null
  source: ReadingSource
  import_job_id: number | null
}

export interface AnomalyMachineRef {
  id: number
  identifier: string
  name: string
}

export interface AnomalyReadingRef {
  id: number
  timestamp: string
  vibration_rms: number
  temperature: number
  rpm: number
  load_pct: number
  pressure: number | null
}

export interface AnomalyRead {
  id: number
  machine: AnomalyMachineRef
  reading_id: number
  reading: AnomalyReadingRef | null
  metric: string
  observed_value: number
  threshold_value: number | null
  severity: AnomalySeverity
  method: AnomalyMethod
  status: AnomalyStatus
  detected_at: string
  last_seen_at: string
  acknowledged_at: string | null
  resolved_at: string | null
  explanation: string
  notes: string | null
}

export interface PeriodCount {
  current: number
  previous: number
  period_start: string
  period_end: string
}

export interface DashboardSummary {
  total_machines: number
  active_machines: number
  healthy_machines: number
  attention_machines: number
  inactive_machines: number
  active_alerts: number
  anomalies_period: PeriodCount
  overdue_work_orders: number
  upcoming_work_orders: number
  generated_at: string
}

export interface DashboardResponse {
  summary: DashboardSummary
  machines: MachineSummary[]
}

export interface ApiErrorBody {
  code: string
  message: string
  details?: Record<string, unknown>[] | null
}

/* ------------------------------------------------------------------ *
 * Maintenance (work orders) — mirrors backend/app/schemas/maintenance
 * ------------------------------------------------------------------ */

export type MaintenanceType = 'preventive' | 'corrective' | 'inspection' | 'other'
export type MaintenancePriority = 'low' | 'medium' | 'high' | 'urgent'
export type WorkOrderStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled'

export interface MachineRef {
  id: number
  identifier: string
  name: string
}

export interface LinkedAnomalyRef {
  id: number
  metric: string
  severity: string
  status: string
  detected_at: string
}

export interface WorkOrderRead {
  id: number
  work_order_number: string
  machine: MachineRef
  title: string
  description: string | null
  maintenance_type: MaintenanceType
  priority: MaintenancePriority
  status: WorkOrderStatus
  scheduled_date: string | null
  started_at: string | null
  completed_at: string | null
  technician: string | null
  findings: string | null
  actions_taken: string | null
  anomaly_events: LinkedAnomalyRef[]
  created_at: string
  updated_at: string
}

export interface MachineCreatePayload {
  identifier: string
  name: string
  equipment_type: EquipmentType
  location?: string | null
  manufacturer?: string | null
  model?: string | null
  installation_date?: string | null
  description?: string | null
  thresholds?: MachineThresholds
}

export type MachineUpdatePayload = Partial<MachineCreatePayload> & { status?: MachineStatus }

/* ------------------------------------------------------------------ *
 * Trend analytics — mirrors backend/app/schemas/analytics
 * ------------------------------------------------------------------ */

export interface TrendPoint {
  bucket_start: string
  avg: number | null
  min: number
  max: number
  count: number
}

export interface TrendSeries {
  machine_id: number
  machine_identifier: string
  machine_name: string
  points: TrendPoint[]
}

export interface TrendsResponse {
  metric: MetricName
  unit: string
  start: string
  end: string
  machine_id: number | null
  buckets: number
  bucket_seconds: number
  summary: {
    reading_count: number
    avg: number | null
    min: number | null
    max: number | null
    p95: number | null
  }
  series: TrendSeries[]
}

/* ------------------------------------------------------------------ *
 * Simulation — mirrors backend/app/schemas/reading.ReadingIngestResponse
 * ------------------------------------------------------------------ */

export interface ReadingIngestResponse {
  reading: ReadingRead
  affected_anomaly_ids: number[]
}
