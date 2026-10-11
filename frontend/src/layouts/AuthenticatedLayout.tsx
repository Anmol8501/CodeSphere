import { X } from 'lucide-react'
import { Suspense, useEffect, useRef, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Sidebar } from '../components/layout/Sidebar'
import { TopNavbar } from '../components/layout/TopNavbar'
import { PageSkeleton } from '../components/ui/LoadingState'
import { useAuth } from '../hooks/useAuth'

/**
 * Shell for every authenticated page (all roles).
 * Desktop: fixed sidebar + top navbar. Mobile: top navbar + slide-out drawer.
 * Pages render through <Outlet /> so the shell is not re-mounted on navigation.
 */
export function AuthenticatedLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [loggingOut, setLoggingOut] = useState(false)

  // The drawer remembers the URL it was opened on, so it closes by itself
  // as soon as the user navigates anywhere else.
  const currentUrl = location.pathname + location.search
  const [menuOpenAt, setMenuOpenAt] = useState<string | null>(null)
  const menuOpen = menuOpenAt === currentUrl
  const closeMenu = () => setMenuOpenAt(null)

  // On page change: start at the top and move focus to the new page's content,
  // so keyboard and screen-reader users don't stay stuck on the old link.
  // (Comparing paths keeps the initial load untouched, even under StrictMode.)
  const previousPath = useRef(location.pathname)
  useEffect(() => {
    if (previousPath.current === location.pathname) return
    previousPath.current = location.pathname
    window.scrollTo({ top: 0 })
    document.getElementById('main-content')?.focus({ preventScroll: true })
  }, [location.pathname])

  useEffect(() => {
    if (!menuOpen) return
    const onKey = (event: KeyboardEvent) => event.key === 'Escape' && setMenuOpenAt(null)
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [menuOpen])

  if (!user) return null // ProtectedRoute already redirects; this narrows the type.

  const handleLogout = async () => {
    setLoggingOut(true)
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-svh bg-night">
      <a
        href="#main-content"
        className="sr-only z-50 rounded-lg bg-brand-500 px-4 py-2 font-semibold text-night focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
      >
        Skip to content
      </a>

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 lg:block">
        <Sidebar user={user} onLogout={handleLogout} loggingOut={loggingOut} />
      </aside>

      {/* Mobile drawer */}
      {menuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation menu">
          <div className="absolute inset-0 bg-black/75" onClick={closeMenu} aria-hidden />
          <aside className="relative h-full w-72 max-w-[85%] animate-slide-in shadow-2xl">
            <Sidebar user={user} onLogout={handleLogout} loggingOut={loggingOut} onNavigate={closeMenu} />
            <button
              type="button"
              onClick={closeMenu}
              className="absolute top-3.5 right-3 rounded-lg p-2 text-ink-500 transition hover:bg-ink-100 hover:text-ink-950"
              aria-label="Close navigation menu"
            >
              <X className="size-5" aria-hidden />
            </button>
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <TopNavbar
          user={user}
          onOpenMenu={() => setMenuOpenAt(currentUrl)}
          onLogout={handleLogout}
          loggingOut={loggingOut}
        />
        <main id="main-content" tabIndex={-1} className="bg-line-grid min-h-[calc(100svh-4rem)] focus:outline-none">
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
            <Suspense fallback={<PageSkeleton />}>
              <Outlet />
            </Suspense>
          </div>
        </main>
      </div>
    </div>
  )
}
