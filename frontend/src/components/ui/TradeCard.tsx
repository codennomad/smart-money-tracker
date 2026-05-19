import { Badge } from './Badge'
import { formatCurrency, formatRelative } from '@/lib/utils'
import type { InsiderTrade, CongressTrade } from '@/types'

interface InsiderCardProps {
  trade: InsiderTrade
  onClick?: () => void
}

export function InsiderCard({ trade, onClick }: InsiderCardProps) {
  const isBuy    = trade.transactionType === 'buy'
  const isAnomaly = (trade.anomalyScore ?? 0) > 0.7
  const valueColor = isBuy ? 'var(--color-bull)' : 'var(--color-bear)'

  return (
    <button onClick={onClick}
      className="w-full text-left scan-in transition-all"
      style={{
        background: 'var(--color-surface-1)',
        border: `1px solid ${isBuy ? '#00ff4120' : '#ff222220'}`,
        borderLeft: `3px solid ${valueColor}`,
        padding: '10px 12px',
        display: 'block',
      }}>

      {/* Row 1: ticker + badges + value */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-bold glow" style={{ color: 'var(--color-phosphor)' }}>
            {trade.ticker}
          </span>
          <Badge variant={isBuy ? 'bull' : 'bear'}>
            {isBuy ? '▲ BUY' : '▼ SELL'}
          </Badge>
          <Badge variant="insider">INSIDER</Badge>
          {isAnomaly && <Badge variant="alert">⚠ ANOMALY</Badge>}
        </div>
        <span className="font-bold text-sm shrink-0"
          style={{ color: valueColor, textShadow: `0 0 8px ${valueColor}` }}>
          {formatCurrency(trade.totalValue)}
        </span>
      </div>

      {/* Row 2: insider info */}
      <div className="mt-1.5 flex items-center justify-between">
        <div>
          <span className="text-[13px]" style={{ color: 'var(--color-text-secondary)' }}>
            {trade.insiderName}
          </span>
          <span className="text-[11px] ml-2" style={{ color: 'var(--color-text-muted)' }}>
            {trade.insiderTitle}
          </span>
        </div>
        <span className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
          {trade.shares.toLocaleString()} SH
        </span>
      </div>

      {/* Row 3: meta */}
      <div className="mt-1 flex items-center justify-between">
        <span className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
          {trade.company}
        </span>
        <span className="text-[11px]" style={{ color: 'var(--color-phosphor-lo)' }}>
          {formatRelative(trade.filedAt)}
        </span>
      </div>

      {/* Anomaly score bar */}
      {isAnomaly && (
        <div className="mt-2">
          <div className="flex items-center justify-between mb-0.5">
            <span className="text-[10px] tracking-widest" style={{ color: 'var(--color-alert)' }}>
              ANOMALY CONFIDENCE
            </span>
            <span className="text-[10px]" style={{ color: 'var(--color-alert)' }}>
              {((trade.anomalyScore ?? 0) * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-0.5 w-full" style={{ background: '#1a1a1a' }}>
            <div className="h-full" style={{
              width: `${(trade.anomalyScore ?? 0) * 100}%`,
              background: 'var(--color-alert)',
              boxShadow: '0 0 4px var(--color-alert)',
            }} />
          </div>
        </div>
      )}
    </button>
  )
}

interface CongressCardProps {
  trade: CongressTrade
  onClick?: () => void
}

export function CongressCard({ trade, onClick }: CongressCardProps) {
  const isBuy       = trade.transactionType === 'buy'
  const valueColor  = isBuy ? 'var(--color-bull)' : 'var(--color-bear)'
  const partyColor  = trade.party === 'D' ? 'var(--color-congress)' : 'var(--color-bear)'
  const lateFlag    = trade.daysToDisclose > 30

  return (
    <button onClick={onClick}
      className="w-full text-left scan-in transition-all"
      style={{
        background: 'var(--color-surface-1)',
        border: `1px solid #00aaff20`,
        borderLeft: '3px solid var(--color-congress)',
        padding: '10px 12px',
        display: 'block',
      }}>

      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-bold" style={{ color: 'var(--color-congress)', textShadow: '0 0 8px var(--color-congress)' }}>
            {trade.ticker}
          </span>
          <Badge variant={isBuy ? 'bull' : 'bear'}>
            {isBuy ? '▲ BUY' : '▼ SELL'}
          </Badge>
          <Badge variant="congress">CONGRESS</Badge>
          {lateFlag && <Badge variant="alert">LATE {trade.daysToDisclose}D</Badge>}
        </div>
        <div className="text-right shrink-0">
          <div className="text-[13px] font-bold" style={{ color: valueColor }}>
            {formatCurrency(trade.amountMin)}–{formatCurrency(trade.amountMax)}
          </div>
        </div>
      </div>

      <div className="mt-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-bold" style={{ color: partyColor }}>
            [{trade.party}]
          </span>
          <span className="text-[13px]" style={{ color: 'var(--color-text-secondary)' }}>
            {trade.member}
          </span>
        </div>
        <span className="text-[11px] tracking-wider" style={{ color: 'var(--color-text-muted)' }}>
          {trade.chamber.toUpperCase()}
        </span>
      </div>

      <div className="mt-1 flex items-center justify-between">
        <span className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
          {trade.company}
        </span>
        <span className="text-[11px]" style={{ color: 'var(--color-phosphor-lo)' }}>
          {formatRelative(trade.transactionDate)}
        </span>
      </div>
    </button>
  )
}
