import { useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { useTheme } from 'next-themes'
import {
  Bell,
  ChevronRight,
  Factory,
  Moon,
  Plus,
  Search,
  Sun,
  TriangleAlert,
  UploadCloud,
  UserRound,
  Wrench,
} from 'lucide-react'

import { useAnomalies, useDashboard } from '@/api/queries'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { resolveRouteMeta } from '@/lib/route-meta'
import { SEVERITY_LABEL, timeAgo } from '@/lib/format'
import { cn } from '@/lib/utils'

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const isDark = resolvedTheme !== 'light'
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      {isDark ? <Sun className="size-4" aria-hidden /> : <Moon className="size-4" aria-hidden />}
    </Button>
  )
}

function QuickActions() {
  const navigate = useNavigate()
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5 max-sm:size-icon">
          <Plus className="size-4" aria-hidden />
          <span className="max-sm:sr-only">Quick actions</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>Create</DropdownMenuLabel>
        <DropdownMenuItem onSelect={() => navigate('/machines?create=1')}>
          <Factory className="size-4" aria-hidden />
          Register machine
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => navigate('/import')}>
          <UploadCloud className="size-4" aria-hidden />
          Import sensor CSV
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => navigate('/maintenance')}>
          <Wrench className="size-4" aria-hidden />
          Log work order
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function AlertBell() {
  const navigate = useNavigate()
  const { data: dashboard } = useDashboard('24h')
  const { data: openAlerts } = useAnomalies({ status: 'open', page_size: 5, order: 'desc' })
  const count = dashboard?.summary.active_alerts ?? 0

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Open alerts (${count})`}
          className="relative"
        >
          <Bell className="size-4" aria-hidden />
          {count > 0 ? (
            <span className="absolute right-1 top-1 flex size-4 items-center justify-center rounded-full bg-destructive-fill text-[10px] font-semibold leading-none text-destructive-foreground">
              {count > 9 ? '9+' : count}
            </span>
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Open alerts</span>
          <span className="text-xs font-normal text-muted-foreground">{count} unacknowledged</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {openAlerts && openAlerts.items.length > 0 ? (
          openAlerts.items.map((alert) => (
            <DropdownMenuItem
              key={alert.id}
              onSelect={() => navigate('/anomalies')}
              className="grid gap-1 py-2"
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    'size-2 shrink-0 rounded-full',
                    alert.severity === 'critical' ? 'bg-destructive' : 'bg-warning',
                  )}
                />
                <span className="font-medium">
                  {alert.machine.identifier} · {alert.metric.replace(/_/g, ' ')}
                </span>
                <span className="ml-auto text-xs text-muted-foreground">
                  {SEVERITY_LABEL[alert.severity]}
                </span>
              </div>
              <span className="pl-4 text-xs text-muted-foreground">
                {alert.observed_value.toFixed(2)} detected {timeAgo(alert.detected_at)}
              </span>
            </DropdownMenuItem>
          ))
        ) : (
          <div className="grid gap-1 px-2 py-3 text-sm">
            <span className="font-medium">No open alerts</span>
            <span className="text-xs text-muted-foreground">
              Every machine is inside its configured thresholds.
            </span>
          </div>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => navigate('/anomalies')}>
          <TriangleAlert className="size-4" aria-hidden />
          View all anomaly events
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function ProfileMenu() {
  const navigate = useNavigate()
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Demo profile menu" className="ml-0.5">
          <span className="flex size-7 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
            DE
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          <span className="grid">
            <span className="text-sm font-medium">Demo engineer</span>
            <span className="text-xs font-normal text-muted-foreground">
              Reliability engineering · demo mode
            </span>
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => navigate('/settings')}>
          <UserRound className="size-4" aria-hidden />
          Profile &amp; settings
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export function AppHeader({ onOpenPalette }: { onOpenPalette: () => void }) {
  const { pathname } = useLocation()
  const meta = resolveRouteMeta(pathname)

  useEffect(() => {
    document.title = `${meta.documentTitle ?? meta.title} · MechSense`
  }, [meta.documentTitle, meta.title])

  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-2 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:px-6">
      <SidebarTrigger className="-ml-1" />
      <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1.5">
        {meta.breadcrumb ? (
          <>
            <Link
              to={`/${meta.breadcrumb.toLowerCase().replace(/\s+/g, '-')}`}
              className="truncate text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {meta.breadcrumb}
            </Link>
            <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" aria-hidden />
          </>
        ) : null}
        <h1 className="truncate text-xl font-semibold tracking-tight">{meta.title}</h1>
      </nav>

      <div className="ml-auto flex items-center gap-1.5">
        <button
          type="button"
          onClick={onOpenPalette}
          className="hidden h-8 w-56 items-center gap-2 rounded-md border bg-muted/40 px-2.5 text-xs text-muted-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:flex"
        >
          <Search className="size-3.5" aria-hidden />
          Search machines, pages…
          <kbd className="ml-auto rounded border bg-background px-1.5 py-0.5 font-mono text-[10px]">
            ⌘K
          </kbd>
        </button>
        <Button
          variant="ghost"
          size="icon"
          className="sm:hidden"
          aria-label="Open search"
          onClick={onOpenPalette}
        >
          <Search className="size-4" aria-hidden />
        </Button>
        <QuickActions />
        <AlertBell />
        <ThemeToggle />
        <ProfileMenu />
      </div>
    </header>
  )
}
