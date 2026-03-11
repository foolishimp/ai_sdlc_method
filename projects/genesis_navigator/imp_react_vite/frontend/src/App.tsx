// Implements: REQ-F-SHELL-002, REQ-F-NAV-002, REQ-F-FEATDETAIL-001
import { Routes, Route } from 'react-router'
import { ProjectListPage } from './pages/ProjectListPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { FeatureDetailPage } from './pages/FeatureDetailPage'

export function App() {
  return (
    <Routes>
      <Route path="/" element={<ProjectListPage />} />
      <Route path="/projects/:id" element={<ProjectDetailPage />} />
      <Route path="/projects/:id/features/:featureId" element={<FeatureDetailPage />} />
    </Routes>
  )
}
