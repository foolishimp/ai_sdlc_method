// Implements: REQ-F-UX-001, REQ-NFR-PERF-001

import { useEffect } from 'react'
import { useProjectStore } from '../stores/projectStore'

// useWorkspacePoller — mounted once at App root.
// Fires refreshAll() immediately on mount, then every intervalMs milliseconds.
// A single setInterval drives all data freshness across all work areas.
// Implements: REQ-F-UX-001
export function useWorkspacePoller(intervalMs: number = 30_000): void {
  const refreshAll = useProjectStore((s) => s.refreshAll)

  useEffect(() => {
    // Fire immediately on mount — don't wait for first interval
    void refreshAll()
    const id = setInterval(() => void refreshAll(), intervalMs)
    return () => clearInterval(id)
  }, [refreshAll, intervalMs])
}
