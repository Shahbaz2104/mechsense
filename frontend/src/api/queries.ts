import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'

import { api, buildQuery, fetchAllPages } from './client'
import type {
  AnomalyRead,
  DashboardPeriod,
  DashboardResponse,
  MachineCreatePayload,
  MachineRead,
  MachineSummary,
  MachineUpdatePayload,
  MetricName,
  Page,
  ReadingIngestResponse,
  ReadingRead,
  TrendsResponse,
  WorkOrderRead,
} from './types'

export interface MachinesQuery {
  page?: number
  page_size?: number
  search?: string
  status?: string
  health?: string
  sort?: string
  order?: 'asc' | 'desc'
  equipment_type?: string
}

export interface AnomaliesQuery {
  page?: number
  page_size?: number
  machine_id?: number
  status?: string
  severity?: string
  method?: string
  metric?: string
  start?: string
  end?: string
  q?: string
  sort?: string
  order?: 'asc' | 'desc'
}

export type ReadRange = '1h' | '6h' | '24h' | '7d'

export const queryKeys = {
  dashboard: (period: DashboardPeriod) => ['dashboard', period] as const,
  machines: (params: MachinesQuery) => ['machines', params] as const,
  machine: (id: number) => ['machine', id] as const,
  machineReadings: (id: number, range: ReadRange) => ['machine-readings', id, range] as const,
  anomalies: (params: AnomaliesQuery) => ['anomalies', params] as const,
  anomaly: (id: number) => ['anomaly', id] as const,
}

export function useDashboard(period: DashboardPeriod) {
  return useQuery({
    queryKey: queryKeys.dashboard(period),
    queryFn: () => api.get<DashboardResponse>(`/dashboard/summary${buildQuery({ period })}`),
    refetchInterval: 60_000,
    staleTime: 10_000,
  })
}

export function useMachines(params: MachinesQuery = {}, enabled = true) {
  return useQuery({
    queryKey: queryKeys.machines(params),
    enabled,
    queryFn: () => api.get<Page<MachineSummary>>(`/machines${buildQuery(params)}`),
    staleTime: 15_000,
  })
}

export function useMachine(id: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.machine(id),
    queryFn: () => api.get<MachineRead>(`/machines/${id}`),
    enabled,
    staleTime: 30_000,
  })
}

const RANGE_MS: Record<ReadRange, number> = {
  '1h': 60 * 60 * 1000,
  '6h': 6 * 60 * 60 * 1000,
  '24h': 24 * 60 * 60 * 1000,
  '7d': 7 * 24 * 60 * 60 * 1000,
}

/**
 * Readings over a trailing window, following pagination up to 6×500 rows so the
 * 7-day range stays a single query (7d @ 5min ≈ 2 016 points).
 */
export function useMachineReadings(id: number, range: ReadRange, enabled = true) {
  return useQuery({
    queryKey: queryKeys.machineReadings(id, range),
    enabled,
    staleTime: 15_000,
    queryFn: async () => {
      const end = new Date()
      const start = new Date(end.getTime() - RANGE_MS[range])
      const path = `/machines/${id}/readings${buildQuery({
        start: start.toISOString(),
        end: end.toISOString(),
        order: 'asc',
      })}`
      const { items, total } = await fetchAllPages<ReadingRead>(path)
      return { items, total, start, end }
    },
  })
}

export function useAnomalies(params: AnomaliesQuery = {}, enabled = true) {
  return useQuery({
    queryKey: queryKeys.anomalies(params),
    enabled,
    queryFn: () => api.get<Page<AnomalyRead>>(`/anomalies${buildQuery(params)}`),
    staleTime: 10_000,
  })
}

export function useAnomaly(id: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.anomaly(id),
    queryFn: () => api.get<AnomalyRead>(`/anomalies/${id}`),
    enabled,
    staleTime: 10_000,
  })
}

/**
 * Acknowledge (reviewed) vs resolve (closed) are distinct lifecycle actions
 * per spec §10. Omitting `notes` leaves existing investigation notes intact
 * on the backend; an empty string is treated the same way here.
 */
function invalidateAnomalyViews(queryClient: QueryClient, id: number) {
  void queryClient.invalidateQueries({ queryKey: ['anomalies'] })
  void queryClient.invalidateQueries({ queryKey: ['anomaly', id] })
  void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  void queryClient.invalidateQueries({ queryKey: ['machines'] })
  void queryClient.invalidateQueries({ queryKey: ['latest-reading'] })
}

export function useAcknowledgeAnomaly(anomalyId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (notes?: string) =>
      api.post<AnomalyRead>(`/anomalies/${anomalyId}/acknowledge`, notes ? { notes } : {}),
    onSuccess: () => invalidateAnomalyViews(queryClient, anomalyId),
  })
}

export function useResolveAnomaly(anomalyId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (notes?: string) =>
      api.post<AnomalyRead>(`/anomalies/${anomalyId}/resolve`, notes ? { notes } : {}),
    onSuccess: () => invalidateAnomalyViews(queryClient, anomalyId),
  })
}

/* ------------------------------------------------------------------ *
 * Maintenance, latest reading, trends, machine mutations (Phase 4b)
 * ------------------------------------------------------------------ */

export interface MaintenanceQuery {
  page?: number
  page_size?: number
  machine_id?: number
  status?: string
  priority?: string
  sort?: string
  order?: 'asc' | 'desc'
  overdue?: boolean
  upcoming?: boolean
}

export interface TrendsQuery {
  machine_id?: number
  metric?: MetricName
  start?: string
  end?: string
  buckets?: number
}

export const queryKeysExtras = {
  maintenance: (params: MaintenanceQuery) => ['maintenance', params] as const,
  latestReading: (machineId: number) => ['latest-reading', machineId] as const,
  trends: (params: TrendsQuery) => ['trends', params] as const,
}

export function useMaintenance(params: MaintenanceQuery = {}, enabled = true) {
  return useQuery({
    queryKey: queryKeysExtras.maintenance(params),
    enabled,
    queryFn: () => api.get<Page<WorkOrderRead>>(`/maintenance${buildQuery(params)}`),
    staleTime: 10_000,
  })
}

/** Most recent reading for a machine (current-readings strip on detail). */
export function useLatestReading(machineId: number, enabled = true) {
  return useQuery({
    queryKey: queryKeysExtras.latestReading(machineId),
    enabled,
    staleTime: 15_000,
    queryFn: async () => {
      const page = await api.get<Page<ReadingRead>>(
        `/machines/${machineId}/readings${buildQuery({ order: 'desc', page_size: 1 })}`,
      )
      return page.items[0] ?? null
    },
  })
}

/** Bucketed trends for wide windows (30d) where raw rows exceed the page cap. */
export function useTrends(params: TrendsQuery, enabled = true) {
  return useQuery({
    queryKey: queryKeysExtras.trends(params),
    enabled,
    staleTime: 30_000,
    queryFn: () => api.get<TrendsResponse>(`/analytics/trends${buildQuery(params)}`),
  })
}

export function useCreateMachine() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: MachineCreatePayload) => api.post<MachineRead>('/machines', payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['machines'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useUpdateMachine(machineId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: MachineUpdatePayload) =>
      api.patch<MachineRead>(`/machines/${machineId}`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['machines'] })
      void queryClient.invalidateQueries({ queryKey: ['machine', machineId] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['latest-reading', machineId] })
    },
  })
}

/**
 * Bucketed 30-day trend for one machine + metric (60 × 12h buckets). The
 * window is resolved inside queryFn so the query key stays stable across
 * renders while still moving forward on refetch.
 */
/**
 * Demo interaction (spec §8): generate one reading for a machine server-side
 * and surface any anomaly events it created or extended.
 */
export function useSimulationStep(machineId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () =>
      api.post<ReadingIngestResponse>('/simulation/step', { machine_id: machineId }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['latest-reading', machineId] })
      void queryClient.invalidateQueries({ queryKey: ['machine-readings', machineId] })
      void queryClient.invalidateQueries({ queryKey: ['anomalies'] })
      void queryClient.invalidateQueries({ queryKey: ['machines'] })
      void queryClient.invalidateQueries({ queryKey: ['machine', machineId] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['machine-trends', machineId] })
    },
  })
}

export function useMachineTrends(machineId: number, metric: MetricName, enabled = true) {
  return useQuery({
    queryKey: ['machine-trends', machineId, metric],
    enabled,
    staleTime: 60_000,
    queryFn: async () => {
      const end = new Date()
      const start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000)
      const data = await api.get<TrendsResponse>(
        `/analytics/trends${buildQuery({
          machine_id: machineId,
          metric,
          start: start.toISOString(),
          end: end.toISOString(),
          buckets: 60,
        })}`,
      )
      return { data, start, end }
    },
  })
}
