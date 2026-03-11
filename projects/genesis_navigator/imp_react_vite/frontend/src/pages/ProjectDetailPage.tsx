// Implements: REQ-F-STAT-002, REQ-F-STAT-003, REQ-F-STAT-004
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { StatusView } from '../components/StatusView'
import { GapView } from '../components/GapView'
import { QueueView } from '../components/QueueView'

type Tab = 'status' | 'gaps' | 'queue'

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

  if (!projectId) return <div style={{ padding: '32px' }}>Invalid project ID</div>
  if (isLoading) return <div style={{ padding: '32px', textAlign: 'center' }}>Loading…</div>
  if (error) return <div style={{ padding: '32px', color: '#dc2626' }}>Error: {String(error)}</div>
  if (!project) return null

  const tabs: { key: Tab; label: string }[] = [
    { key: 'status', label: 'Status' },
    { key: 'gaps', label: 'Gaps' },
    { key: 'queue', label: 'Queue' },
  ]

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <button onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>← Back</button>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>{project.name}</h1>
        <button
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['project', projectId] })
            queryClient.invalidateQueries({ queryKey: ['gaps', projectId] })
            queryClient.invalidateQueries({ queryKey: ['queue', projectId] })
          }}
          style={{ marginLeft: 'auto', padding: '8px 16px', cursor: 'pointer' }}
        >
          Refresh
        </button>
      </div>

      <div style={{ display: 'flex', gap: '0', borderBottom: '1px solid #e5e7eb', marginBottom: '24px' }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            data-testid={`tab-${tab.key}`}
            style={{
              padding: '8px 20px',
              border: 'none',
              borderBottom: activeTab === tab.key ? '2px solid #2563eb' : '2px solid transparent',
              background: 'none',
              cursor: 'pointer',
              fontWeight: activeTab === tab.key ? 'bold' : 'normal',
              color: activeTab === tab.key ? '#2563eb' : 'inherit',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'status' && <StatusView project={project} />}
      {activeTab === 'gaps' && <GapView projectId={projectId} />}
      {activeTab === 'queue' && <QueueView projectId={projectId} />}
    </div>
  )
}
