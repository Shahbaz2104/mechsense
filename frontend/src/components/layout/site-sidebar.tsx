import { NavLink } from 'react-router'

import { useDashboard } from '@/api/queries'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar'
import { cn } from '@/lib/utils'
import { NAV_GROUPS } from './nav'

export function MechSenseMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      role="img"
      aria-label="MechSense"
      className={cn('size-8 rounded-lg', className)}
    >
      <rect width="32" height="32" rx="7" fill="var(--primary)" />
      <path
        d="M4 18h5l2.5-7 3.5 12 3-9 2 4h8"
        fill="none"
        stroke="var(--primary-foreground)"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function SiteSidebar() {
  const { data: dashboard } = useDashboard('24h')
  const activeAlerts = dashboard?.summary.active_alerts ?? 0

  return (
    <Sidebar collapsible="icon" variant="inset">
      <SidebarHeader>
        <div className="flex items-center gap-2.5 px-1 py-1">
          <MechSenseMark className="size-8 shrink-0" />
          <div className="grid min-w-0 overflow-hidden group-data-[collapsible=icon]:hidden">
            <span className="truncate text-sm font-semibold tracking-tight">MechSense</span>
            <span className="truncate text-xs leading-tight text-muted-foreground">
              Machine health intelligence
            </span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {NAV_GROUPS.map((group) => (
          <SidebarGroup key={group.label}>
            <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => (
                  <SidebarMenuItem key={item.to}>
                    <SidebarMenuButton tooltip={item.title} asChild>
                      <NavLink to={item.to} end={item.end}>
                        <item.icon aria-hidden />
                        <span>{item.title}</span>
                      </NavLink>
                    </SidebarMenuButton>
                    {item.to === '/anomalies' && activeAlerts > 0 ? (
                      <SidebarMenuBadge className="group-data-[collapsible=icon]:hidden">
                        <span
                          className={
                            'flex size-4 items-center justify-center rounded-full bg-destructive-fill text-[10px] font-semibold text-destructive-foreground'
                          }
                        >
                          {activeAlerts}
                        </span>
                      </SidebarMenuBadge>
                    ) : null}
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton tooltip="Demo engineer — settings" size="lg" asChild>
              <NavLink to="/settings">
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                  DE
                </span>
                <span className="grid overflow-hidden">
                  <span className="truncate text-xs font-medium">Demo engineer</span>
                  <span className="truncate text-xs text-muted-foreground">
                    Demo mode · no auth
                  </span>
                </span>
              </NavLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
