import { useEffect, useState } from 'react'
import { CongressCard } from '@/components/ui/TradeCard'
import { api } from '@/lib/api'
import type { CongressTrade } from '@/types'

type Chamber = 'ALL' | 'HOUSE' | 'SENATE'
type Party   = 'ALL' | 'D' | 'R'

export function CongressPage() {
  const [trades, setTrades]   = useState<CongressTrade[]>([])
  const [loading, setLoading] = useState(true)
  const [chamber, setChamber] = useState<Chamber>('ALL')
  const [party, setParty]     = useState<Party>('ALL')

  useEffect(() => {
    const params: Record<string, string> = { pageSize: '50' }
    if (chamber !== 'ALL') params.chamber = chamber.toLowerCase()
    if (party !== 'ALL') params.party = party

    setLoading(true)
    api.congress.list(params)
      .then((r) => setTrades(r.data))
      .catch(() => setTrades([]))
      .finally(() => setLoading(false))
  }, [chamber, party])

  // Stats
  const lateCount = trades.filter((t) => t.daysToDisclose > 30).length
  const buyCount  = trades.filter((t) => t.transactionType === 'buy').length

  return (
    <div>
      <div className="px-4 pt-3 pb-2" style={{ borderBottom: '1px solid var(--color-border-dim)' }}>
        <div className="text-[9px] tracking-[0.3em]" style={{ color: 'var(--color-text-muted)' }}>
          STOCK ACT // CONGRESSIONAL DISCLOSURES
        </div>
      </div>

      {/* Stats bar */}
      {!loading && (
        <div className="flex px-4 py-2 gap-4" style={{ borderBottom: '1px solid var(--color-border-dim)', background: 'var(--color-surface-1)' }}>
          <div>
            <div className="text-[8px] tracking-wider" style={{ color: 'var(--color-text-muted)' }}>TOTAL</div>
            <div className="text-sm font-bold" style={{ color: 'var(--color-congress)' }}>{trades.length}</div>
          </div>
          <div>
            <div className="text-[8px] tracking-wider" style={{ color: 'var(--color-text-muted)' }}>BUY</div>
            <div className="text-sm font-bold" style={{ color: 'var(--color-bull)' }}>{buyCount}</div>
          </div>
          <div>
            <div className="text-[8px] tracking-wider" style={{ color: 'var(--color-text-muted)' }}>SELL</div>
            <div className="text-sm font-bold" style={{ color: 'var(--color-bear)' }}>{trades.length - buyCount}</div>
          </div>
          {lateCount > 0 && (
            <div>
              <div className="text-[8px] tracking-wider" style={{ color: 'var(--color-alert)' }}>LATE</div>
              <div className="text-sm font-bold" style={{ color: 'var(--color-alert)' }}>{lateCount}</div>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="px-4 py-2 space-y-2" style={{ borderBottom: '1px solid var(--color-border)' }}>
        <div className="flex gap-px">
          {(['ALL', 'HOUSE', 'SENATE'] as Chamber[]).map((c) => {
            const active = chamber === c
            return (
              <button key={c} onClick={() => setChamber(c)}
                className="flex-1 py-1 text-[9px] tracking-[0.2em] transition-all"
                style={{
                  color: active ? 'var(--color-congress)' : 'var(--color-text-muted)',
                  background: active ? 'var(--color-congress)10' : 'var(--color-surface-1)',
                  border: `1px solid ${active ? 'var(--color-congress)40' : 'var(--color-border)'}`,
                  textShadow: active ? '0 0 6px var(--color-congress)' : 'none',
                }}>
                {c}
              </button>
            )
          })}
        </div>
        <div className="flex gap-px">
          {(['ALL', 'D', 'R'] as Party[]).map((p) => {
            const active = party === p
            const color  = p === 'D' ? 'var(--color-congress)' : p === 'R' ? 'var(--color-bear)' : 'var(--color-phosphor)'
            return (
              <button key={p} onClick={() => setParty(p)}
                className="flex-1 py-1 text-[9px] tracking-[0.2em] transition-all"
                style={{
                  color: active ? color : 'var(--color-text-muted)',
                  background: active ? `${color}10` : 'var(--color-surface-1)',
                  border: `1px solid ${active ? `${color}40` : 'var(--color-border)'}`,
                  textShadow: active ? `0 0 6px ${color}` : 'none',
                }}>
                {p === 'ALL' ? 'ALL PARTIES' : p === 'D' ? '[D] DEM' : '[R] REP'}
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-px">
        {loading && Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse"
            style={{ background: 'var(--color-surface-1)', borderLeft: '3px solid var(--color-border)' }} />
        ))}
        {!loading && trades.map((t) => <CongressCard key={t.id} trade={t} />)}
        {!loading && trades.length === 0 && (
          <div className="py-16 text-center text-[11px] tracking-wider"
            style={{ color: 'var(--color-text-muted)' }}>
            NO RECORDS FOUND
          </div>
        )}
      </div>
    </div>
  )
}
