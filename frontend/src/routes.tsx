import { BrowserRouter, Navigate, Route, Routes } from 'react-router'

import { AppShell } from '@/components/layout/app-shell'
import OverviewPage from '@/pages/Overview'
import MachinesPage from '@/pages/Machines'
import MachineDetailPage from '@/pages/MachineDetail'
import SensorExplorerPage from '@/pages/SensorExplorer'
import AnomaliesPage from '@/pages/Anomalies'
import AnomalyDetailPage from '@/pages/AnomalyDetail'
import { AnalyticsStub, DataImportStub, MaintenanceStub, SettingsStub } from '@/pages/stubs'

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<OverviewPage />} />
          <Route path="/machines" element={<MachinesPage />} />
          <Route path="/machines/:machineId" element={<MachineDetailPage />} />
          <Route path="/explorer" element={<SensorExplorerPage />} />
          <Route path="/anomalies" element={<AnomaliesPage />} />
          <Route path="/anomalies/:anomalyId" element={<AnomalyDetailPage />} />
          <Route path="/maintenance" element={<MaintenanceStub />} />
          <Route path="/import" element={<DataImportStub />} />
          <Route path="/analytics" element={<AnalyticsStub />} />
          <Route path="/settings" element={<SettingsStub />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
