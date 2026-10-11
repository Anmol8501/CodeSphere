import { LogoMark } from '../brand/Logo'
import { Spinner } from './Spinner'

/** Full-screen loader shown while the session is restored on page load. */
export function FullPageLoader({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-5 bg-ink-50" role="status">
      <LogoMark className="size-12" />
      <div className="flex items-center gap-2.5 text-sm font-medium text-ink-600">
        <Spinner className="size-4" />
        {message}
      </div>
    </div>
  )
}
