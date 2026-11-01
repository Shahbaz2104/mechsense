import { useNavigate } from 'react-router'
import { Factory, Plus, Settings, UploadCloud, Wrench } from 'lucide-react'

import { useMachines } from '@/api/queries'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import { NAV_GROUPS } from './nav'

export function CommandPalette({
  open,
  setOpen,
}: {
  open: boolean
  setOpen: (open: boolean) => void
}) {
  const navigate = useNavigate()
  const { data: machines } = useMachines({ page_size: 100, sort: 'identifier' }, open)

  const go = (to: string) => {
    setOpen(false)
    navigate(to)
  }

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search machines or jump to a page…" />
      <CommandList>
        <CommandEmpty>No machines or pages match.</CommandEmpty>
        <CommandGroup heading="Navigate">
          {NAV_GROUPS.flatMap((group) => group.items).map((item) => (
            <CommandItem key={item.to} value={`page ${item.title}`} onSelect={() => go(item.to)}>
              <item.icon className="size-4" aria-hidden />
              <span>{item.title}</span>
              <span className="ml-auto text-xs text-muted-foreground">{item.to}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Machines">
          {(machines?.items ?? []).map((machine) => (
            <CommandItem
              key={machine.id}
              value={`${machine.identifier} ${machine.name}`}
              onSelect={() => go(`/machines/${machine.id}`)}
            >
              <Factory className="size-4" aria-hidden />
              <span className="font-mono text-xs">{machine.identifier}</span>
              <span className="truncate text-muted-foreground">{machine.name}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Actions">
          <CommandItem value="action register machine" onSelect={() => go('/machines?create=1')}>
            <Plus className="size-4" aria-hidden />
            Register machine
          </CommandItem>
          <CommandItem value="action import csv" onSelect={() => go('/import')}>
            <UploadCloud className="size-4" aria-hidden />
            Import sensor CSV
          </CommandItem>
          <CommandItem value="action work order" onSelect={() => go('/maintenance')}>
            <Wrench className="size-4" aria-hidden />
            Log work order
          </CommandItem>
          <CommandItem value="action settings" onSelect={() => go('/settings')}>
            <Settings className="size-4" aria-hidden />
            Open settings
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
