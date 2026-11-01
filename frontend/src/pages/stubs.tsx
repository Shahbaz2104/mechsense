import { LineChart, Settings, UploadCloud, Wrench } from 'lucide-react'

import { PageStub } from './page-stub'

export function MaintenanceStub() {
  return (
    <PageStub
      icon={<Wrench className="size-5" aria-hidden />}
      title="Maintenance"
      description="Work orders and the asset service history."
      notes={[
        'Work-order table with status, priority, due dates, and overdue flags',
        'Create work orders linked to machines and specific anomaly events',
        'Maintenance timeline per machine feeding the overview metrics',
      ]}
    />
  )
}

export function DataImportStub() {
  return (
    <PageStub
      icon={<UploadCloud className="size-5" aria-hidden />}
      title="Data import"
      description="Upload and validate CSV sensor datasets for analysis."
      notes={[
        'Column mapping with strict validation against the reading schema',
        'Preview, row-level error reporting, then commit as imported history',
        'Import jobs listed with source attribution on every stored reading',
      ]}
    />
  )
}

export function AnalyticsStub() {
  return (
    <PageStub
      icon={<LineChart className="size-5" aria-hidden />}
      title="Analytics"
      description="Condition trends, availability, and detection statistics."
      notes={[
        'Fleet-wide health distribution and trend over selectable periods',
        'Per-machine metric statistics versus configured engineering limits',
        'Detection method breakdown once statistical detection ships',
      ]}
    />
  )
}

export function SettingsStub() {
  return (
    <PageStub
      icon={<Settings className="size-5" aria-hidden />}
      title="Settings"
      description="Display, data-source, and demo-environment preferences."
      notes={[
        'Theme and density preferences for the monitoring console',
        'Simulation controls: fault scenarios, generation rate, data reset',
        'About and stack information for the demo environment',
      ]}
    />
  )
}
