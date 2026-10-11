import { Code2, Lock } from 'lucide-react'
import type { Language } from '../../types/problem'
import { ButtonLink } from '../ui/Button'
import { Badge } from '../ui/Badge'
import { Card } from '../ui/Card'
import { LANGUAGE_LABEL } from './labels'

interface SolveCardProps {
  languages: Language[]
  /** Students get a link to the coding workspace; staff see it is student-only. */
  solvePath?: string
}

export function SolveCard({ languages, solvePath }: SolveCardProps) {
  return (
    <Card as="section" aria-labelledby="solve-card-title" className="overflow-hidden" hud>
      <div className="flex items-center justify-between gap-3 border-b border-ink-200 bg-night/60 px-5 py-3">
        <h2 id="solve-card-title" className="font-mono text-xs font-semibold tracking-[0.14em] text-ink-950 uppercase">
          Code Workspace
        </h2>
      </div>
      <div className="flex flex-col items-center px-6 py-8 text-center">
        <span className="flex size-12 items-center justify-center rounded-xl bg-brand-500/10 text-brand-500 ring-1 ring-brand-500/25">
          {solvePath ? <Code2 className="size-6" aria-hidden /> : <Lock className="size-6" aria-hidden />}
        </span>
        {solvePath ? (
          <>
            <p className="mt-4 font-semibold text-ink-950">Ready to write code?</p>
            <p className="mt-1 max-w-xs text-sm text-ink-500">
              Write your solution, run it on the sample tests, then submit it for judging. Your work is saved automatically.
            </p>
            <ButtonLink to={solvePath} className="mt-5" fullWidth icon={<Code2 className="size-4" aria-hidden />}>
              Solve Problem
            </ButtonLink>
          </>
        ) : (
          <>
            <p className="mt-4 font-semibold text-ink-950">The coding workspace is for students.</p>
            <p className="mt-1 max-w-xs text-sm text-ink-500">Staff can review the problem statement here.</p>
          </>
        )}
        <div className="mt-6 w-full rounded-xl border border-ink-200 bg-night/60 p-4 text-left">
          <p className="font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">Languages</p>
          <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Available languages">
            {languages.map((lang) => (
              <li key={lang}>
                <Badge tone="brand" mono>
                  {LANGUAGE_LABEL[lang]}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  )
}
