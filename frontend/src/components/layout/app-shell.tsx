import { useEffect, useState } from 'react'
import { Outlet } from 'react-router'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { AppHeader } from './app-header'
import { CommandPalette } from './command-palette'
import { SiteSidebar } from './site-sidebar'

export function AppShell() {
  const [paletteOpen, setPaletteOpen] = useState(false)

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setPaletteOpen((current) => !current)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  return (
    <SidebarProvider>
      <SiteSidebar />
      <SidebarInset className="flex min-w-0 flex-1 flex-col">
        <AppHeader onOpenPalette={() => setPaletteOpen(true)} />
        <div className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-6 md:px-6">
          <Outlet />
        </div>
        <CommandPalette open={paletteOpen} setOpen={setPaletteOpen} />
      </SidebarInset>
    </SidebarProvider>
  )
}
