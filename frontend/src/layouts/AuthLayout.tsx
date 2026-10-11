import type { ReactNode } from 'react'
import { BrandPanel } from '../components/auth/BrandPanel'
import { PublicHeader } from '../components/layout/PublicHeader'

const CURRENT_YEAR = new Date().getFullYear()

/**
 * Layout for /login and /register.
 * Desktop: brand panel + form card side by side. Mobile: single column card.
 */
export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col bg-night">
      <PublicHeader />
      <main className="bg-dot-grid-light flex flex-1 items-center">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 py-8 sm:px-6 sm:py-12 lg:grid-cols-[1.05fr_1fr] lg:gap-12">
          <BrandPanel />
          <div className="flex items-center justify-center">
            <div className="w-full max-w-[440px] animate-fade-in rounded-3xl border border-ink-200 bg-surface p-6 shadow-lift sm:p-9">
              {children}
            </div>
          </div>
        </div>
      </main>
      <footer className="border-t border-ink-200 bg-night py-5 text-center text-xs text-ink-400">
        © {CURRENT_YEAR} CodeArena. Built for college coders.
      </footer>
    </div>
  )
}
