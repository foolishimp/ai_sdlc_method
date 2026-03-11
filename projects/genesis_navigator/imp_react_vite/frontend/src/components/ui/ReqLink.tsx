// Implements: REQ-F-NAV-002
// Implements: REQ-F-FEATDETAIL-001
import { Link } from 'react-router'

interface ReqLinkProps {
  reqKey: string
  /** When provided, link navigates within the navigator (/projects/:projectId/features/:reqKey) */
  localProjectId?: string
  /** When provided and localProjectId is absent, link opens genesis_monitor */
  projectSlug?: string
  style?: React.CSSProperties
}

const linkStyle: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '12px',
  fontWeight: 500,
  color: 'var(--accent)',
  textDecoration: 'none',
  borderBottom: '1px dotted var(--accent)',
  paddingBottom: '1px',
}

const hoverHandlers = {
  onMouseEnter: (e: React.MouseEvent<HTMLElement>) => {
    e.currentTarget.style.borderBottomStyle = 'solid'
  },
  onMouseLeave: (e: React.MouseEvent<HTMLElement>) => {
    e.currentTarget.style.borderBottomStyle = 'dotted'
  },
}

export function ReqLink({ reqKey, localProjectId, projectSlug, style }: ReqLinkProps) {
  const merged = { ...linkStyle, ...style }

  if (localProjectId) {
    return (
      <Link
        to={`/projects/${encodeURIComponent(localProjectId)}/features/${encodeURIComponent(reqKey)}`}
        title={`View ${reqKey} feature detail`}
        style={merged}
        {...hoverHandlers}
      >
        {reqKey}
      </Link>
    )
  }

  if (projectSlug) {
    return (
      <a
        href={`http://localhost:8000/project/${projectSlug}/feature/${reqKey}`}
        target="_blank"
        rel="noopener noreferrer"
        title={`Open ${reqKey} in Genesis Monitor`}
        style={merged}
        {...hoverHandlers}
      >
        {reqKey}
      </a>
    )
  }

  // No project context — render styled but not linked
  return (
    <span style={{ ...merged, borderBottom: '1px dotted var(--border)', color: 'var(--text-secondary)' }}>
      {reqKey}
    </span>
  )
}

export function projectSlug(projectId: string): string {
  return projectId.replace(/_/g, '-')
}
