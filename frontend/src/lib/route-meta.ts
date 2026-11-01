export interface RouteMeta {
  title: string
  /** Parent label for the breadcrumb, if any. */
  breadcrumb?: string
  documentTitle?: string
}

/**
 * Static route metadata for the header. Dynamic segments (machine detail)
 * resolve through `resolveRouteMeta`.
 */
const META: Record<string, RouteMeta> = {
  '/overview': { title: 'Overview', documentTitle: 'Overview' },
  '/machines': { title: 'Machines', documentTitle: 'Machines' },
  '/explorer': { title: 'Sensor Explorer', documentTitle: 'Sensor Explorer' },
  '/anomalies': { title: 'Anomaly Events', documentTitle: 'Anomaly Events' },
  '/maintenance': { title: 'Maintenance', documentTitle: 'Maintenance' },
  '/import': { title: 'Data Import', documentTitle: 'Data Import' },
  '/analytics': { title: 'Analytics', documentTitle: 'Analytics' },
  '/settings': { title: 'Settings', documentTitle: 'Settings' },
}

export function resolveRouteMeta(pathname: string): RouteMeta {
  const exact = META[pathname]
  if (exact) return exact
  if (pathname.startsWith('/machines/')) {
    return { title: 'Machine detail', breadcrumb: 'Machines', documentTitle: 'Machine' }
  }
  if (pathname.startsWith('/anomalies/')) {
    return { title: 'Anomaly event', breadcrumb: 'Anomaly Events', documentTitle: 'Anomaly event' }
  }
  return { title: 'MechSense', documentTitle: 'Machine Health Intelligence' }
}
