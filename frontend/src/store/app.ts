import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AnomalyAlert } from '@/types'

interface AppState {
  watchlist: string[]
  alerts: AnomalyAlert[]
  activeTab: 'feed' | 'insiders' | 'congress' | 'watchlist'
  wsConnected: boolean

  addToWatchlist: (ticker: string) => void
  removeFromWatchlist: (ticker: string) => void
  setActiveTab: (tab: AppState['activeTab']) => void
  setWsConnected: (v: boolean) => void
  pushAlert: (alert: AnomalyAlert) => void
  clearAlerts: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      watchlist: [],
      alerts: [],
      activeTab: 'feed',
      wsConnected: false,

      addToWatchlist: (ticker) =>
        set((s) => ({
          watchlist: s.watchlist.includes(ticker) ? s.watchlist : [...s.watchlist, ticker]
        })),
      removeFromWatchlist: (ticker) =>
        set((s) => ({ watchlist: s.watchlist.filter((t) => t !== ticker) })),
      setActiveTab: (tab) => set({ activeTab: tab }),
      setWsConnected: (v) => set({ wsConnected: v }),
      pushAlert: (alert) =>
        set((s) => ({ alerts: [alert, ...s.alerts].slice(0, 50) })),
      clearAlerts: () => set({ alerts: [] }),
    }),
    {
      name: 'smt-app',
      partialize: (s) => ({ watchlist: s.watchlist, activeTab: s.activeTab }),
    }
  )
)
