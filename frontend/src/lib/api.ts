import type {
  InsiderTrade, CongressTrade, OptionsFlow,
  DarkPoolPrint, AnomalyAlert, PaginatedResponse
} from '@/types'

const BASE = '/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  insiders: {
    list: (params?: Record<string, string>) => {
      const qs = params ? '?' + new URLSearchParams(params) : ''
      return request<PaginatedResponse<InsiderTrade>>(`/insiders${qs}`)
    },
    byTicker: (ticker: string) =>
      request<PaginatedResponse<InsiderTrade>>(`/insiders?ticker=${ticker}`),
  },
  congress: {
    list: (params?: Record<string, string>) => {
      const qs = params ? '?' + new URLSearchParams(params) : ''
      return request<PaginatedResponse<CongressTrade>>(`/congress${qs}`)
    },
  },
  options: {
    unusual: () => request<PaginatedResponse<OptionsFlow>>('/options/unusual'),
  },
  darkpool: {
    list: (ticker?: string) =>
      request<PaginatedResponse<DarkPoolPrint>>(
        ticker ? `/darkpool?ticker=${ticker}` : '/darkpool'
      ),
  },
  alerts: {
    list: () => request<AnomalyAlert[]>('/alerts'),
  },
}

export function createWebSocket(onMessage: (data: unknown) => void): WebSocket {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${proto}://${window.location.host}/api/v1/ws/feed`)
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)) } catch { /* ignore malformed */ }
  }
  return ws
}
