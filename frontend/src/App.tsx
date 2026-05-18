import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { FeedPage } from '@/pages/FeedPage'
import { InsidersPage } from '@/pages/InsidersPage'
import { CongressPage } from '@/pages/CongressPage'
import { WatchlistPage } from '@/pages/WatchlistPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/"          element={<FeedPage />} />
          <Route path="/insiders"  element={<InsidersPage />} />
          <Route path="/congress"  element={<CongressPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
