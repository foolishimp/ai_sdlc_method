// Implements: REQ-F-SHELL-002, REQ-F-NAV-002
import { Routes, Route } from 'react-router'
import { ProjectListPage } from './pages/ProjectListPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'

export function App() {
  return (
    <Routes>
      <Route path="/" element={<ProjectListPage />} />
      <Route path="/projects/:id" element={<ProjectDetailPage />} />
    </Routes>
  )
}
