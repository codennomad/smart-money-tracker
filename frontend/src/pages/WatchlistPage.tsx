import { useState } from 'react'
import { useAppStore } from '@/store/app'
import { api } from '@/lib/api'
import { InsiderCard, CongressCard } from '@/components/ui/TradeCard'
import { formatCurrency } from '@/lib/utils'
import type { InsiderTrade, CongressTrade } from '@/types'

function TerminalInput({
  value, onChange, onSubmit
}: { value: string; onChange: (v: string) => void; onSubmit: () => void }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2"
      style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border)', borderLeft: '3px solid var(--color-phosphor)' }}>
      <span className="text-[13px]" style={{ color: 'var(--color-phosphor)' }}>$</span>
      <span className="text-[13px]" style={{ color: 'var(--color-text-muted)' }}>ADD_TICKER</span>
      <span className="text-[13px]" style={{ color: 'var(--color-phosphor-lo)' }}> ─</span>
      <input
        type="text"
        value={value}
        maxLength={10}
        onChange={(e) => onChange(e.target.value.toUpperCase())}
        onKeyDown={(e) => e.key === 'Enter' && onSubmit()}
        placeholder="AAPL"
        className="flex-1 bg-transparent text-[12px] font-bold outline-none placeholder:opacity-20"
        style={{ color: 'var(--color-phosphor)', fontFamily: 'var(--font-mono)', caretColor: 'var(--color-phosphor)' }}
        autoFocus
      />
      <button onClick={onSubmit}
        className="text-[13px] tracking-wider px-2 py-0.5 transition-all"
        style={{ background: 'var(--color-phosphor-mist)', border: '1px solid var(--color-phosphor-lo)', color: 'var(--color-phosphor)' }}>
        ADD
      </button>
    </div>
  )
}

function WatchlistItem({ ticker, onRemove }: { ticker: string; onRemove: () => void }) {
  const [insiders, setInsiders] = useState<InsiderTrade[]>([])
  const [congress, setCongress] = useState<CongressTrade[]>([])
  const [open, setOpen]         = useState(false)
  const [loading, setLoading]   = useState(false)

  async function loadData() {
    if (insiders.length || loading) { setOpen((o) => !o); return }
    setOpen(true)
    setLoading(true)
    const [ins, con] = await Promise.all([
      api.insiders.byTicker(ticker),
      api.congress.list({ ticker }),
    ])
    setInsiders(ins.data.slice(0, 5))
    setCongress(con.data.slice(0, 3))
    setLoading(false)
  }

  const totalBuy = insiders.filter((t) => t.transactionType === 'buy')
    .reduce((s, t) => s + t.totalValue, 0)

  return (
    <div style={{ border: '1px solid var(--color-border)', borderLeft: '3px solid var(--color-phosphor)' }}>
      {/* Header row */}
      <div className="flex items-center px-3 py-2.5 cursor-pointer" onClick={loadData}
        style={{ background: 'var(--color-surface-1)' }}>
        <span className="text-sm font-bold glow" style={{ color: 'var(--color-phosphor)' }}>{ticker}</span>
        {totalBuy > 0 && (
          <span className="ml-3 text-[12px]" style={{ color: 'var(--color-bull)' }}>
            ▲ {formatCurrency(totalBuy)}
          </span>
        )}
        <div className="ml-auto flex items-center gap-3">
          <span className="text-[13px] tracking-wider" style={{ color: 'var(--color-text-muted)' }}>
            {open ? '▲ CLOSE' : '▼ EXPAND'}
          </span>
          <button onClick={(e) => { e.stopPropagation(); onRemove() }}
            className="text-[12px] px-1.5 py-0.5 transition-all"
            style={{ color: 'var(--color-bear)', border: '1px solid var(--color-bear)30' }}>
            ✕
          </button>
        </div>
      </div>

      {/* Expanded */}
      {open && (
        <div style={{ borderTop: '1px solid var(--color-border)' }}>
          {loading && (
            <div className="py-4 text-center text-[12px] tracking-wider"
              style={{ color: 'var(--color-text-muted)' }}>
              ACQUIRING INTEL...
            </div>
          )}
          {!loading && insiders.length === 0 && congress.length === 0 && (
            <div className="py-4 text-center text-[12px]" style={{ color: 'var(--color-text-muted)' }}>
              NO RECENT FLOW
            </div>
          )}
          <div className="space-y-px">
            {insiders.map((t) => <InsiderCard key={t.id} trade={t} />)}
            {congress.map((t) => <CongressCard key={t.id} trade={t} />)}
          </div>
        </div>
      )}
    </div>
  )
}

export function WatchlistPage() {
  const watchlist         = useAppStore((s) => s.watchlist)
  const addToWatchlist    = useAppStore((s) => s.addToWatchlist)
  const removeFromWatchlist = useAppStore((s) => s.removeFromWatchlist)
  const [input, setInput] = useState('')

  function handleAdd() {
    const ticker = input.trim().toUpperCase()
    if (ticker.length >= 1) {
      addToWatchlist(ticker)
      setInput('')
    }
  }

  return (
    <div>
      <div className="px-4 pt-3 pb-2" style={{ borderBottom: '1px solid var(--color-border-dim)' }}>
        <div className="text-[13px] tracking-[0.3em]" style={{ color: 'var(--color-text-muted)' }}>
          WATCHLIST // TARGET TRACKING
        </div>
      </div>

      <div className="px-4 py-3" style={{ borderBottom: '1px solid var(--color-border)' }}>
        <TerminalInput value={input} onChange={setInput} onSubmit={handleAdd} />
      </div>

      {watchlist.length === 0 ? (
        <div className="px-4 py-16 text-center space-y-3">
          <div className="text-[13px] tracking-widest" style={{ color: 'var(--color-text-muted)' }}>
            NO TARGETS ACQUIRED
          </div>
          <div className="text-[13px] tracking-wider" style={{ color: 'var(--color-text-muted)' }}>
            ADD A TICKER TO TRACK INSIDER FLOW
          </div>
        </div>
      ) : (
        <div className="px-4 py-3 space-y-px">
          {watchlist.map((ticker) => (
            <WatchlistItem key={ticker} ticker={ticker} onRemove={() => removeFromWatchlist(ticker)} />
          ))}
        </div>
      )}

      {watchlist.length > 0 && (
        <div className="px-4 py-2 text-[13px] tracking-wider"
          style={{ color: 'var(--color-text-muted)', borderTop: '1px solid var(--color-border)' }}>
          {watchlist.length} TARGET{watchlist.length > 1 ? 'S' : ''} TRACKED
        </div>
      )}
    </div>
  )
}
