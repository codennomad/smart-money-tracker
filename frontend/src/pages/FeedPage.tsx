import { useEffect, useState } from 'react'
import { InsiderCard, CongressCard } from '@/components/ui/TradeCard'
import { useAppStore } from '@/store/app'
import { api } from '@/lib/api'
import type { InsiderTrade, CongressTrade } from '@/types'

type FeedItem =
  | { kind: 'insider'; data: InsiderTrade }
  | { kind: 'congress'; data: CongressTrade }

function SectionHeader({ label, count }: { label: string; count?: number }) {
  return (
    <div className="flex items-center gap-3 py-2 px-4"
      style={{ borderBottom: '1px solid var(--color-border)' }}>
      <span className="text-[9px] tracking-[0.25em]" style={{ color: 'var(--color-phosphor-lo)' }}>▶</span>
      <span className="text-[10px] tracking-[0.2em] font-bold" style={{ color: 'var(--color-text-secondary)' }}>
        {label}
      </span>
      {count !== undefined && (
        <span className="text-[9px] ml-auto" style={{ color: 'var(--color-text-muted)' }}>
          [{count} RECORDS]
        </span>
      )}
    </div>
  )
}

function AlertBanner({ count }: { count: number }) {
  const alerts = useAppStore((s) => s.alerts)
  if (!alerts.length) return null
  return (
    <div style={{ background: '#0a0800', border: '1px solid #ffaa0030', borderLeft: '3px solid var(--color-alert)' }}
      className="mx-4 mt-4">
      <div className="px-3 py-2">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[9px] tracking-[0.25em] font-bold glow-alert"
            style={{ color: 'var(--color-alert)' }}>
            ⚠ ACTIVE INTELLIGENCE ALERTS
          </span>
          <span className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>
            {count} ALERT{count > 1 ? 'S' : ''}
          </span>
        </div>
        <div className="space-y-2">
          {alerts.slice(0, 3).map((a) => (
            <div key={a.id} className="flex items-start gap-2">
              <span className="text-[9px] mt-0.5" style={{ color: 'var(--color-alert)' }}>◆</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold" style={{ color: 'var(--color-alert)' }}>
                    {a.ticker}
                  </span>
                  <span className="text-[9px] tracking-wider" style={{ color: 'var(--color-text-muted)' }}>
                    {a.alertType.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <span className="text-[9px] ml-auto" style={{ color: 'var(--color-text-muted)' }}>
                    CONF:{(a.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-[10px] mt-0.5" style={{ color: 'var(--color-text-secondary)' }}>
                  {a.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="h-20 mx-0 animate-pulse"
      style={{ background: 'var(--color-surface-1)', borderLeft: '3px solid var(--color-border)' }} />
  )
}

export function FeedPage() {
  const [items, setItems]   = useState<FeedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState<string | null>(null)
  const alerts              = useAppStore((s) => s.alerts)

  useEffect(() => {
    async function load() {
      try {
        const [insiders, congress] = await Promise.all([
          api.insiders.list({ pageSize: '20' }),
          api.congress.list({ pageSize: '20' }),
        ])
        const merged: FeedItem[] = [
          ...insiders.data.map((d) => ({ kind: 'insider' as const, data: d })),
          ...congress.data.map((d) => ({ kind: 'congress' as const, data: d })),
        ].sort((a, b) => {
          const aDate = a.kind === 'insider' ? a.data.filedAt : a.data.disclosedAt
          const bDate = b.kind === 'insider' ? b.data.filedAt : b.data.disclosedAt
          return new Date(bDate).getTime() - new Date(aDate).getTime()
        })
        setItems(merged)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'FEED ACQUISITION FAILED')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="pb-4">
      {/* Intel brief header */}
      <div className="px-4 pt-3 pb-2"
        style={{ borderBottom: '1px solid var(--color-border-dim)' }}>
        <div className="text-[9px] tracking-[0.3em]" style={{ color: 'var(--color-text-muted)' }}>
          INTEL BRIEF // REAL-TIME FLOW
        </div>
      </div>

      <AlertBanner count={alerts.length} />

      <SectionHeader label="LATEST FLOW" count={items.length || undefined} />

      <div className="space-y-px">
        {loading && Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}

        {error && (
          <div className="px-4 py-8 text-center">
            <span className="text-[11px] tracking-wider" style={{ color: 'var(--color-bear)' }}>
              ✕ {error}
            </span>
          </div>
        )}

        {!loading && !error && items.map((item) =>
          item.kind === 'insider'
            ? <InsiderCard key={item.data.id} trade={item.data} />
            : <CongressCard key={item.data.id} trade={item.data} />
        )}
      </div>
    </div>
  )
}
