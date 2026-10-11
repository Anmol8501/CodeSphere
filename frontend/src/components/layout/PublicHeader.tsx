import { GraduationCap, Menu, Presentation, X } from 'lucide-react'
import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { cn } from '../../utils/format'
import { Logo } from '../brand/Logo'

const NAV_LINKS = [
  { label: 'Home', to: '/' },
  { label: 'Features', to: '/#features' },
  { label: 'About', to: '/#about' },
]

export function PublicHeader() {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-40 border-b border-ink-200 bg-night/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo />

        <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.label}
              to={link.to}
              end
              className="rounded-lg px-3 py-2 text-sm font-medium text-ink-600 transition hover:bg-ink-100 hover:text-ink-900"
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Link
            to="/login"
            className="inline-flex h-9 items-center gap-2 rounded-xl px-3.5 text-sm font-semibold text-ink-800 ring-1 ring-ink-200 transition hover:bg-ink-100 hover:ring-brand-500/40"
          >
            <GraduationCap className="size-4" /> Student Login
          </Link>
          <Link
            to="/login?role=staff"
            className="inline-flex h-9 items-center gap-2 rounded-xl bg-brand-500 px-3.5 text-sm font-bold text-night shadow-glow transition hover:bg-brand-400"
          >
            <Presentation className="size-4" /> Staff Login
          </Link>
        </div>

        <button
          type="button"
          className="rounded-lg p-2 text-ink-700 hover:bg-ink-100 md:hidden"
          onClick={() => setOpen((value) => !value)}
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
        >
          {open ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </div>

      <div className={cn('border-t border-ink-200 bg-surface md:hidden', open ? 'block' : 'hidden')}>
        <nav className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-3" aria-label="Mobile">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.label}
              to={link.to}
              onClick={() => setOpen(false)}
              className="rounded-lg px-3 py-2.5 text-sm font-medium text-ink-700 hover:bg-ink-100"
            >
              {link.label}
            </Link>
          ))}
          <div className="mt-2 grid grid-cols-2 gap-2">
            <Link
              to="/login"
              onClick={() => setOpen(false)}
              className="flex h-10 items-center justify-center rounded-xl text-sm font-semibold text-ink-700 ring-1 ring-ink-200"
            >
              Student Login
            </Link>
            <Link
              to="/login?role=staff"
              onClick={() => setOpen(false)}
              className="flex h-10 items-center justify-center rounded-xl bg-brand-500 text-sm font-bold text-night"
            >
              Staff Login
            </Link>
          </div>
        </nav>
      </div>
    </header>
  )
}
