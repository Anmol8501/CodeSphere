import { ArrowRight, BookOpen, Code2, GraduationCap, Presentation, School, Trophy } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { CodeWindow } from '../components/brand/CodeWindow'
import { PublicHeader } from '../components/layout/PublicHeader'
import { useAuth } from '../hooks/useAuth'
import { ROLE_HOME } from '../utils/routes'

const FEATURES: { icon: ReactNode; title: string; text: string }[] = [
  { icon: <Code2 />, title: 'Practice problems', text: 'Solve coding challenges in an online editor with instant test feedback.' },
  { icon: <BookOpen />, title: 'Learning paths', text: 'Follow structured DSA topics from basics to interview-ready.' },
  { icon: <Trophy />, title: 'Contests', text: 'Compete with classmates and climb the leaderboard.' },
  { icon: <School />, title: 'Classrooms', text: 'Staff run classes, publish assignments and track progress.' },
]

const CURRENT_YEAR = new Date().getFullYear()

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div className="min-h-svh bg-night">
      <PublicHeader />

      {/* Hero */}
      <section className="relative overflow-hidden border-b border-ink-200 bg-night text-ink-950">
        <div className="bg-dot-grid absolute inset-0" aria-hidden />
        <div className="absolute -top-32 right-0 size-[480px] rounded-full bg-brand-500/10 blur-3xl" aria-hidden />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 sm:py-24 lg:grid-cols-2">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-brand-500/25 bg-brand-500/5 px-3 py-1 font-mono text-xs text-brand-400">
              <span className="size-1.5 animate-pulse rounded-full bg-brand-500" /> Learn • Code • Compete
            </p>
            <h1 className="mt-6 text-4xl leading-[1.1] font-extrabold tracking-tight sm:text-5xl">
              The coding arena for{' '}
              <span className="bg-gradient-to-r from-brand-500 to-accent bg-clip-text text-transparent">
                college students.
              </span>
            </h1>
            <p className="mt-5 max-w-lg text-[17px] leading-relaxed text-ink-600">
              Build real problem-solving skills, follow your class assignments and prepare for
              placements, all in one place.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              {user ? (
                <Link
                  to={ROLE_HOME[user.role]}
                  className="inline-flex h-12 items-center gap-2 rounded-xl bg-brand-500 px-6 font-bold text-night shadow-glow transition hover:bg-brand-400"
                >
                  Go to dashboard <ArrowRight className="size-4" />
                </Link>
              ) : (
                <>
                  <Link
                    to="/register"
                    className="inline-flex h-12 items-center gap-2 rounded-xl bg-brand-500 px-6 font-bold text-night shadow-glow transition hover:bg-brand-400"
                  >
                    Get started <ArrowRight className="size-4" />
                  </Link>
                  <Link
                    to="/login"
                    className="inline-flex h-12 items-center gap-2 rounded-xl bg-surface px-6 font-semibold text-ink-900 ring-1 ring-ink-200 transition hover:ring-brand-500/40"
                  >
                    Login
                  </Link>
                </>
              )}
            </div>
          </div>
          <CodeWindow className="hidden sm:block" />
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6">
        <p className="font-mono text-sm font-medium text-brand-500">{'// features'}</p>
        <h2 className="mt-2 text-3xl font-extrabold tracking-tight text-ink-950">Everything you need to level up</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="rounded-2xl border border-ink-200 bg-surface p-6 shadow-card transition hover:border-brand-500/30">
              <span className="flex size-10 items-center justify-center rounded-xl bg-brand-500/10 text-brand-500 ring-1 ring-brand-500/25 [&>svg]:size-5">
                {feature.icon}
              </span>
              <h3 className="mt-4 font-bold text-ink-950">{feature.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-500">{feature.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* About + portals */}
      <section id="about" className="scroll-mt-20 border-t border-ink-200 bg-surface">
        <div className="mx-auto grid max-w-6xl gap-8 px-4 py-16 sm:px-6 lg:grid-cols-2">
          <div>
            <p className="font-mono text-sm font-medium text-brand-500">{'// about'}</p>
            <h2 className="mt-2 text-3xl font-extrabold tracking-tight text-ink-950">Built for classrooms</h2>
            <p className="mt-4 leading-relaxed text-ink-600">
              CodeArena connects students and staff. Students register themselves and practice at
              their own pace. Staff accounts are created by the college administrator so classes
              stay organized and secure.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Link
              to="/login"
              className="group rounded-2xl border border-ink-200 p-6 transition bg-night hover:border-brand-500/40 hover:shadow-card"
            >
              <GraduationCap className="size-6 text-brand-500" />
              <h3 className="mt-3 font-bold text-ink-950">Student Login</h3>
              <p className="mt-1 text-sm text-ink-500">Practice, learn and compete.</p>
              <span className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-brand-500">
                Continue <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />
              </span>
            </Link>
            <Link
              to="/login?role=staff"
              className="group rounded-2xl border border-ink-200 p-6 transition bg-night hover:border-brand-500/40 hover:shadow-card"
            >
              <Presentation className="size-6 text-accent" />
              <h3 className="mt-3 font-bold text-ink-950">Staff Login</h3>
              <p className="mt-1 text-sm text-ink-500">Manage classes and track progress.</p>
              <span className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-brand-500">
                Continue <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />
              </span>
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-ink-200 py-6 text-center text-xs text-ink-400">
        © {CURRENT_YEAR} CodeArena. Built for college coders.
      </footer>
    </div>
  )
}
