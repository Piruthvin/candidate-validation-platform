import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopHeader } from './TopHeader'
import { cn } from '@/utils/cn'

const routeTitles: Record<string, string> = {
  '/': 'Chat',
  '/reports': 'Reports',
  '/settings': 'Settings',
  '/about': 'About',
}

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const title = routeTitles[location.pathname] ?? 'Candidate Validation Platform'

  return (
    <div className="flex h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="flex flex-1 flex-col md:ml-0">
        <TopHeader
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen((p) => !p)}
          title={title}
        />
        <main
          className={cn(
            'flex-1 overflow-hidden',
            'mt-14'
          )}
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}
