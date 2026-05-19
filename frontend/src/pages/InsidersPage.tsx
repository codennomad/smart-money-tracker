import { useEffect, useState } from 'react'
import { InsiderCard } from '@/components/ui/TradeCard'
import { api } from '@/lib/api'
import type { InsiderTrade } from '@/types'

type Filter = 'ALL' | 'BUY' | 'SELL'

export function InsidersPage() {
  const [trades, setTrades]   = useState<InsiderTrade[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')
  const [filter, setFilter]   = useState<Filter>('ALL')

  useEffect(() => {
    const params: Record<string, string> = { pageSize: '50' }
    if (filter !== 'ALL') params.type = filter.toLowerCase()
    if (search.length >= 1) params.ticker = search.toUpperCase()

    setLoading(true)
    api.insiders.list(params)
      .then((r) => setTrades(r.data))
      .catch(() => setTrades([]))
      .finally(() => setLoading(false))
  }, [filter, search])

  return (
    <div>
      {/* Header */}
      <div className="px-4 pt-3 pb-2" style={{ borderBottom: '1px solid var(--color-border-dim)' }}>
        <div className="text-[13px] tracking-[0.3em]" style={{ color: 'var(--color-text-muted)' }}>
          FORM 4 // INSIDER TRANSACTIONS
        </div>
      </div>

      {/* Controls */}
      <div className="px-4 py-2 space-y-2" style={{ borderBottom: '1px solid var(--color-border)' }}>
        {/* Search */}
        <div className="flex items-center gap-2"
          style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border)', padding: '6px 10px' }}>
          <span className="text-[12px]" style={{ color: 'var(--color-phosphor-lo)' }}>TICKER:</span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value.toUpperCase())}
            placeholder="AAPL_"
            maxLength={10}
            className="flex-1 bg-transparent text-[13px] outline-none placeholder:opacity-30"
            style={{ color: 'var(--color-phosphor)', fontFamily: 'var(--font-mono)', caretColor: 'var(--color-phosphor)' }}
          />
          {search && (
            <button onClick={() => setSearch('')} className="text-[12px]"
              style={{ color: 'var(--color-text-muted)' }}>✕</button>
          )}
        </div>

        {/* Filter tabs */}
        <div className="flex gap-px">
          {(['ALL', 'BUY', 'SELL'] as Filter[]).map((f) => {
            const active = filter === f
            const color = f === 'BUY' ? 'var(--color-bull)' : f === 'SELL' ? 'var(--color-bear)' : 'var(--color-phosphor)'
            return (
              <button key={f} onClick={() => setFilter(f)}
                className="flex-1 py-1 text-[13px] tracking-[0.2em] transition-all"
                style={{
                  color: active ? color : 'var(--color-text-muted)',
                  background: active ? `${color}10` : 'var(--color-surface-1)',
                  border: `1px solid ${active ? `${color}40` : 'var(--color-border)'}`,
                  textShadow: active ? `0 0 6px ${color}` : 'none',
                }}>
                {f}
              </button>
            )
          })}
        </div>
      </div>

      {/* List */}
      <div className="space-y-px">
        {loading && Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse"
            style={{ background: 'var(--color-surface-1)', borderLeft: '3px solid var(--color-border)' }} />
        ))}
        {!loading && trades.map((t) => <InsiderCard key={t.id} trade={t} />)}
        {!loading && trades.length === 0 && (
          <div className="py-16 text-center text-[13px] tracking-wider"
            style={{ color: 'var(--color-text-muted)' }}>
            NO RECORDS FOUND
          </div>
        )}
      </div>

      {/* Count footer */}
      {!loading && trades.length > 0 && (
        <div className="px-4 py-2 text-[13px] tracking-wider"
          style={{ color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)' }}>
          DISPLAYING {trades.length} TRANSACTIONS
        </div>
      )}
    </div>
  )
}
