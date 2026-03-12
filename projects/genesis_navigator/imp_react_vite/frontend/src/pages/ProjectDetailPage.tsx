// Implements: REQ-F-STAT-002, REQ-F-STAT-003, REQ-F-STAT-004, REQ-F-HIST-001, REQ-F-HIST-002
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { StatusView } from '../components/StatusView'
import { GapView } from '../components/GapView'
import { QueueView } from '../components/QueueView'
import { HistoryView } from '../components/HistoryView'
import { StateBadge } from '../components/ui/Badge'

type Tab = 'status' | 'gaps' | 'queue' | 'history'
const TABS: { key: Tab; label: string }[] = [
  { key: 'status', label: 'Status' },
  { key: 'gaps', label: 'Gaps' },
  { key: 'queue', label: 'Queue' },
  { key: 'history', label: 'History' },
]

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<Tab>('status')
  const projectId = id ?? ''

  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId),
    enabled: !!projectId,
  })

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <div style={{ borderBottom: '1px solid var(--border)', background: 'var(--surface)', padding: '0 32px', position: 'sticky', top: 0, zIndex: 10 }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          {/* Top bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', height: '56px' }}>
            <button
              onClick={() => navigate('/')}
              style={{
                display: 'flex', alignItems: 'center', gap: '4px',
                padding: '4px 10px', borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)', background: 'transparent',
                color: 'var(--text-secondary)', fontSize: '13px',
              }}
            >
              ← Projects
            </button>
            <div style={{ width: 1, height: 20, background: 'var(--border)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
              <div style={{ width: 22, height: 22, borderRadius: '5px', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800, color: 'white', flexShrink: 0 }}>G</div>
              <span style={{ fontWeight: 600, fontSize: '15px' }}>{project?.name ?? projectId}</span>
              {project && <StateBadge state={project.state} />}
            </div>
            <button
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ['project', projectId] })
                queryClient.invalidateQueries({ queryKey: ['gaps', projectId] })
                queryClient.invalidateQueries({ queryKey: ['queue', projectId] })
                queryClient.invalidateQueries({ queryKey: ['runs', projectId] })
              }}
              style={{
                padding: '5px 12px', borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)', background: 'transparent',
                color: 'var(--text-secondary)', fontSize: '13px',
              }}
            >
              ↻ Refresh
            </button>
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', gap: '0' }}>
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                data-testid={`tab-${tab.key}`}
                style={{
                  padding: '10px 16px',
                  border: 'none',
                  borderBottom: `2px solid ${activeTab === tab.key ? 'var(--accent)' : 'transparent'}`,
                  background: 'none',
                  color: activeTab === tab.key ? 'var(--accent)' : 'var(--text-secondary)',
                  fontWeight: activeTab === tab.key ? 600 : 400,
                  fontSize: '13px',
                  transition: 'color 0.1s',
                  marginBottom: '-1px',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px' }}>
        {isLoading && <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '64px 0' }}>Loading…</div>}
        {error && <div style={{ padding: '16px', background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: 'var(--radius)', color: '#991b1b' }}>{String(error)}</div>}
        {project && activeTab === 'status' && <StatusView project={project} projectId={projectId} />}
        {activeTab === 'gaps' && projectId && <GapView projectId={projectId} />}
        {activeTab === 'queue' && projectId && <QueueView projectId={projectId} />}
        {activeTab === 'history' && projectId && <HistoryView projectId={projectId} />}
      </div>
    </div>
  )
}
