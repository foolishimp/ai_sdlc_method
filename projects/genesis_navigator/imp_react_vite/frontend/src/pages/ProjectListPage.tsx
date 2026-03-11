// Implements: REQ-F-STAT-001, REQ-F-NAV-001
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { api } from '../api/client'
import type { ProjectSummary } from '../api/types'

function StateBadge({ state }: { state: string }) {
  const colors: Record<string, string> = {
    ITERATING: '#2563eb',
    QUIESCENT: '#d97706',
    CONVERGED: '#16a34a',
    BOUNDED: '#7c3aed',
  }
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: '4px',
      backgroundColor: colors[state] ?? '#6b7280',
      color: 'white',
      fontSize: '0.75rem',
      fontWeight: 'bold',
    }}>
      {state}
    </span>
  )
}

function ProjectCard({ project, onClick }: { project: ProjectSummary; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '16px',
        cursor: 'pointer',
        transition: 'box-shadow 0.1s',
      }}
      data-testid={`project-card-${project.project_id}`}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h3 style={{ margin: 0, fontSize: '1rem' }}>{project.name}</h3>
        <StateBadge state={project.state} />
      </div>
      <div style={{ fontSize: '0.875rem', color: '#6b7280', display: 'flex', gap: '16px' }}>
        <span>{project.feature_count} features</span>
        <span>{project.converged_count} converged</span>
        <span>{project.iterating_count} iterating</span>
        {project.blocked_count > 0 && <span style={{ color: '#dc2626' }}>{project.blocked_count} blocked</span>}
      </div>
      <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '4px' }}>{project.root_path}</div>
    </div>
  )
}

export function ProjectListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: api.listProjects,
  })

  if (isLoading) return <div style={{ padding: '32px', textAlign: 'center' }}>Loading projects…</div>
  if (error) return <div style={{ padding: '32px', color: '#dc2626' }}>Error: {String(error)}</div>

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Genesis Navigator</h1>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['projects'] })}
          style={{ padding: '8px 16px', cursor: 'pointer' }}
        >
          Refresh
        </button>
      </div>
      {projects && projects.length === 0 && (
        <p style={{ color: '#6b7280' }}>No Genesis projects found in the scanned workspace.</p>
      )}
      <div style={{ display: 'grid', gap: '12px' }}>
        {projects?.map((p) => (
          <ProjectCard
            key={p.project_id}
            project={p}
            onClick={() => navigate(`/projects/${p.project_id}`)}
          />
        ))}
      </div>
    </div>
  )
}
