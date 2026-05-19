import { cn } from '@/lib/utils'

type BadgeVariant = 'bull' | 'bear' | 'neutral' | 'congress' | 'insider' | 'darkpool' | 'alert'

const VARIANT_STYLES: Record<BadgeVariant, { color: string; glow: string; border: string }> = {
  bull:     { color: 'var(--color-bull)',     glow: 'var(--color-bull)',     border: '#00ff4140' },
  bear:     { color: 'var(--color-bear)',     glow: 'var(--color-bear)',     border: '#ff222240' },
  neutral:  { color: 'var(--color-neutral)',  glow: 'transparent',           border: '#3a4a3a40' },
  congress: { color: 'var(--color-congress)', glow: 'var(--color-congress)', border: '#00aaff40' },
  insider:  { color: 'var(--color-insider)',  glow: 'var(--color-insider)',  border: '#cc44ff40' },
  darkpool: { color: 'var(--color-darkpool)', glow: 'var(--color-darkpool)', border: '#00ffcc40' },
  alert:    { color: 'var(--color-alert)',    glow: 'var(--color-alert)',    border: '#ffaa0040' },
}

interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
}

export function Badge({ variant = 'neutral', children, className }: BadgeProps) {
  const { color, glow, border } = VARIANT_STYLES[variant]
  return (
    <span
      className={cn('inline-flex items-center text-[11px] font-bold tracking-[0.15em] px-1.5 py-0.5', className)}
      style={{
        color,
        border: `1px solid ${border}`,
        textShadow: glow !== 'transparent' ? `0 0 6px ${glow}` : 'none',
        background: `${color}0d`,
      }}>
      {children}
    </span>
  )
}
