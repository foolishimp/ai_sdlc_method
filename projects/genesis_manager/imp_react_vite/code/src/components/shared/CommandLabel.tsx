// Implements: REQ-F-UX-002

import React from 'react'

interface CommandLabelProps {
  command: string
  children?: React.ReactNode
  className?: string
}

// CommandLabel — wraps action content with an informational genesis command label.
// The label is read-only informational text beneath the action, not interactive.
// Implements: REQ-F-UX-002
export function CommandLabel({ command, children, className }: CommandLabelProps): React.JSX.Element {
  return (
    <div className={`flex flex-col gap-1 ${className ?? ''}`}>
      {children}
      <span className="text-xs font-mono text-muted-foreground pl-0.5 select-all">
        {command}
      </span>
    </div>
  )
}
