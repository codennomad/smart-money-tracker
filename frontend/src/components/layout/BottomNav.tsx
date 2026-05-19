import { useNavigate, useLocation } from 'react-router-dom'
import { Activity, Users, Building2, Star } from 'lucide-react'

const TABS = [
  { path: '/',          label: 'FEED',      code: 'F1', Icon: Activity  },
  { path: '/insiders',  label: 'INSIDERS',  code: 'F2', Icon: Users     },
  { path: '/congress',  label: 'CONGRESS',  code: 'F3', Icon: Building2 },
  { path: '/watchlist', label: 'WATCHLIST', code: 'F4', Icon: Star      },
] as const

export function BottomNav() {
  const navigate    = useNavigate()
  const { pathname } = useLocation()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 safe-bottom"
      style={{
        background: 'var(--color-void)',
        borderTop: '1px solid var(--color-border)',
      }}>

      {/* Key hints bar */}
      <div className="flex" style={{ borderBottom: '1px solid var(--color-border-dim)' }}>
        {TABS.map(({ path, code }) => {
          const active = pathname === path
          return (
            <div key={path} className="flex-1 text-center py-0.5 text-[10px] tracking-wider"
              style={{ color: active ? 'var(--color-phosphor)' : 'var(--color-text-muted)' }}>
              [{code}]
            </div>
          )
        })}
      </div>

      <div className="flex items-stretch h-14">
        {TABS.map(({ path, label, Icon }) => {
          const active = pathname === path
          return (
            <button key={path} onClick={() => navigate(path)}
              className="flex-1 flex flex-col items-center justify-center gap-1 transition-all"
              style={{
                color: active ? 'var(--color-phosphor)' : 'var(--color-text-muted)',
                background: active ? 'var(--color-phosphor-mist)' : 'transparent',
                borderRight: '1px solid var(--color-border-dim)',
              }}>
              <Icon size={16} strokeWidth={active ? 2 : 1.5} />
              <span className="text-[10px] tracking-widest"
                style={{ textShadow: active ? '0 0 8px var(--color-phosphor)' : 'none' }}>
                {label}
              </span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
