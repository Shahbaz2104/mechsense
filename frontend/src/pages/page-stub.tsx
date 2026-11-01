import type { ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/card'

/**
 * Scaffold pages for routes whose features land in later build phases.
 * Replaced page-by-page as each capability ships.
 */
export function PageStub({
  icon,
  title,
  description,
  notes,
}: {
  icon: ReactNode
  title: string
  description: string
  notes: string[]
}) {
  return (
    <Card>
      <CardContent className="grid gap-4 p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-lg border bg-muted text-muted-foreground">
            {icon}
          </span>
          <div>
            <h2 className="text-base font-semibold tracking-tight">{title}</h2>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        <ul className="grid gap-2 rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
          {notes.map((note) => (
            <li key={note} className="flex gap-2">
              <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary/60" aria-hidden />
              {note}
            </li>
          ))}
        </ul>
        <p className="text-xs text-muted-foreground">
          Under construction — this section ships with its dedicated build phase.
        </p>
      </CardContent>
    </Card>
  )
}
