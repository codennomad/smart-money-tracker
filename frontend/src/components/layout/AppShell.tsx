import { useEffect, useRef } from 'react'
import { Outlet } from 'react-router-dom'
import { BottomNav } from './BottomNav'
import { createWebSocket } from '@/lib/api'
import { useAppStore } from '@/store/app'
import type { AnomalyAlert } from '@/types'

function StatusDot({ active }: { active: boolean }) {
  return (
    <span className="relative flex h-2 w-2">
      {active && (
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
          style={{ backgroundColor: 'var(--color-phosphor)' }} />
      )}
      <span className="relative inline-flex rounded-full h-2 w-2"
        style={{ backgroundColor: active ? 'var(--color-phosphor)' : 'var(--color-bear)' }} />
    </span>
  )
}

export function AppShell() {
  const setWsConnected = useAppStore((s) => s.setWsConnected)
  const pushAlert      = useAppStore((s) => s.pushAlert)
  const wsConnected    = useAppStore((s) => s.wsConnected)
  const alerts         = useAppStore((s) => s.alerts)
  const wsRef          = useRef<WebSocket | null>(null)

  useEffect(() => {
    function connect() {
      const ws = createWebSocket((data) => {
        if (data && typeof data === 'object' && 'alertType' in (data as object)) {
          pushAlert(data as AnomalyAlert)
        }
      })
      ws.onopen  = () => setWsConnected(true)
      ws.onclose = () => { setWsConnected(false); setTimeout(connect, 5000) }
      ws.onerror = () => ws.close()
      wsRef.current = ws
    }
    connect()
    return () => wsRef.current?.close()
  }, [setWsConnected, pushAlert])

  const now = new Date()
  const timeStr = now.toUTCString().replace('GMT', 'UTC')

  return (
    <div className="flex flex-col min-h-dvh" style={{ background: 'var(--color-void)' }}>

      {/* ── Top header bar ── */}
      <header className="sticky top-0 z-40 safe-top"
        style={{
          background: 'var(--color-void)',
          borderBottom: '1px solid var(--color-border)',
        }}>

        {/* Classification banner */}
        <div className="text-center py-0.5 text-[11px] tracking-[0.3em] font-bold"
          style={{ background: '#0a0a00', color: 'var(--color-alert)', borderBottom: '1px solid #1a1a00' }}>
          ◆ UNCLASSIFIED // OPEN SOURCE INTELLIGENCE ◆
        </div>

        <div className="flex items-center justify-between px-3 h-11">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <span className="text-[12px] tracking-widest glow"
              style={{ color: 'var(--color-phosphor)' }}>
              ▶ SMT
            </span>
            <span className="text-[11px] tracking-wider"
              style={{ color: 'var(--color-text-muted)' }}>
              INSIDER FLOW INTEL
            </span>
          </div>

          {/* Status */}
          <div className="flex items-center gap-3">
            {alerts.length > 0 && (
              <span className="text-[11px] tracking-wider glow-alert blink"
                style={{ color: 'var(--color-alert)' }}>
                ⚠ {alerts.length} ALERT{alerts.length > 1 ? 'S' : ''}
              </span>
            )}
            <div className="flex items-center gap-1.5">
              <StatusDot active={wsConnected} />
              <span className="text-[11px] tracking-wider"
                style={{ color: wsConnected ? 'var(--color-phosphor-dim)' : 'var(--color-bear)' }}>
                {wsConnected ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>
          </div>
        </div>

        {/* Timestamp bar */}
        <div className="px-3 pb-1.5 flex justify-between items-center">
          <span className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
            {timeStr}
          </span>
          <span className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
            SRC: SEC/FINRA/HOUSE/SENATE
          </span>
        </div>
      </header>

      {/* ── Main content ── */}
      <main className="flex-1 overflow-y-auto pb-20">
        <Outlet />
      </main>

      <BottomNav />
    </div>
  )
}
