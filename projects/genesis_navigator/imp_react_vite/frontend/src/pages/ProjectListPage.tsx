// Implements: REQ-F-STAT-001, REQ-F-NAV-001
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { api } from '../api/client'
import type { ProjectSummary } from '../api/types'
import { StateBadge } from '../components/ui/Badge'

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function ProjectRow({ project, onClick }: { project: ProjectSummary; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
      data-testid={`project-card-${project.project_id}`}
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr auto auto auto',
        alignItems: 'center',
        gap: '24px',
        padding: '14px 20px',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
        cursor: 'pointer',
        transition: 'border-color 0.15s, box-shadow 0.15s',
        marginBottom: '6px',
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget
        el.style.borderColor = 'var(--accent)'
        el.style.boxShadow = 'var(--shadow)'
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget
        el.style.borderColor = 'var(--border)'
        el.style.boxShadow = 'none'
      }}
    >
      <div>
        <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '2px' }}>{project.name}</div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          {project.path}
        </div>
      </div>
      <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>{project.active_feature_count}</div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>features</div>
      </div>
      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
        {formatDate(project.last_event_at)}
      </div>
      <StateBadge state={project.state} />
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

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid var(--border)', background: 'var(--surface)', padding: '0 32px' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '56px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: 28, height: 28, borderRadius: '6px', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: 800, color: 'white' }}>G</div>
            <span style={{ fontWeight: 700, fontSize: '15px' }}>Genesis Navigator</span>
          </div>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['projects'] })}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '6px 12px', borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border)', background: 'var(--surface)',
              color: 'var(--text-secondary)', fontWeight: 500,
            }}
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '32px' }}>
        {isLoading && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '64px 0' }}>
            Scanning workspace…
          </div>
        )}
        {error && (
          <div style={{ padding: '16px', background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 'var(--radius)', color: '#991b1b' }}>
            {String(error)}
          </div>
        )}
        {projects && (
          <>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '20px' }}>
              <h1 style={{ fontSize: '20px', fontWeight: 700 }}>Projects</h1>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{projects.length} found</span>
            </div>
            {projects.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '64px 0', fontSize: '14px' }}>
                No Genesis projects found in the scanned workspace.
              </div>
            ) : (
              <div>
                {projects.map((p) => (
                  <ProjectRow key={p.project_id} project={p} onClick={() => navigate(`/projects/${p.project_id}`)} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
