import {
  Activity,
  BarChart3,
  Factory,
  LayoutDashboard,
  Settings,
  TriangleAlert,
  UploadCloud,
  Wrench,
  type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  title: string
  to: string
  icon: LucideIcon
  /** Match the route exactly (Overview). */
  end?: boolean
}

export interface NavGroup {
  label: string
  items: NavItem[]
}

export const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Monitor',
    items: [
      { title: 'Overview', to: '/overview', icon: LayoutDashboard, end: true },
      { title: 'Sensor Explorer', to: '/explorer', icon: Activity },
      { title: 'Anomaly Events', to: '/anomalies', icon: TriangleAlert },
      { title: 'Analytics', to: '/analytics', icon: BarChart3 },
    ],
  },
  {
    label: 'Assets',
    items: [
      { title: 'Machines', to: '/machines', icon: Factory },
      { title: 'Maintenance', to: '/maintenance', icon: Wrench },
      { title: 'Data Import', to: '/import', icon: UploadCloud },
    ],
  },
  {
    label: 'System',
    items: [{ title: 'Settings', to: '/settings', icon: Settings }],
  },
]
