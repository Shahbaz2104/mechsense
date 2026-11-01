import type { ApiErrorBody, Page } from './types'

const API_BASE: string = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export class ApiError extends Error {
  readonly code: string
  readonly status: number
  readonly details: Record<string, unknown>[] | null

  constructor(status: number, body: ApiErrorBody) {
    super(body.message)
    this.name = 'ApiError'
    this.code = body.code
    this.status = status
    this.details = body.details ?? null
  }
}

export function buildQuery(params: object): string {
  const search = new URLSearchParams()
  for (const [key, raw] of Object.entries(params)) {
    if (raw === undefined || raw === null || raw === '') continue
    search.set(key, String(raw))
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { Accept: 'application/json', ...init?.headers },
    })
  } catch {
    throw new ApiError(0, {
      code: 'network_error',
      message: 'Cannot reach the MechSense API. Check that the backend is running on port 8000.',
    })
  }

  if (!response.ok) {
    const parsed = (await response.json().catch(() => null)) as { error?: ApiErrorBody } | null
    throw new ApiError(
      response.status,
      parsed?.error ?? {
        code: 'http_error',
        message: `Request failed with status ${response.status}.`,
      },
    )
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'POST',
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
}

/** Follows the backend pagination envelope across pages (readings over wide ranges). */
export async function fetchAllPages<T>(
  path: string,
  maxPages = 6,
): Promise<{ items: T[]; total: number }> {
  const first = await api.get<Page<T>>(
    `${path}${path.includes('?') ? '&' : '?'}page=1&page_size=500`,
  )
  const items = [...first.items]
  const pages = Math.min(first.pages, maxPages)
  for (let page = 2; page <= pages; page += 1) {
    const next = await api.get<Page<T>>(
      `${path}${path.includes('?') ? '&' : '?'}page=${page}&page_size=500`,
    )
    items.push(...next.items)
  }
  return { items, total: first.total }
}
