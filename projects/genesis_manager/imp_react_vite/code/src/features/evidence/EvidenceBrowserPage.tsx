// Implements: REQ-F-EVI-001, REQ-F-EVI-002, REQ-F-EVI-003, REQ-F-EVI-004, REQ-F-VIS-001

import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useProjectStore } from '../../stores/projectStore'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { apiClient } from '../../api/WorkspaceApiClient'
import { FreshnessIndicator } from '../../components/shared/FreshnessIndicator'
import { TraceabilityTable } from './TraceabilityTable'
import { GapAnalysisPanel } from './GapAnalysisPanel'
import { EventDetailPanel } from './EventDetailPanel'
import { WorkspaceSidebar } from '../../components/shared/WorkspaceSidebar'
import type { GapAnalysisData, WorkspaceEvent } from '../../api/types'

// EvidenceBrowserPage — two-column layout: left (traceability + gap), right (event history + detail).
// Implements: REQ-F-EVI-001, REQ-F-EVI-004
export function EvidenceBrowserPage(): React.JSX.Element {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const id = workspaceId ?? ''

  const loadWorkspace = useWorkspaceStore((s) => s.loadWorkspace)
  const traceability = useWorkspaceStore((s) => s.traceability)
  const overview = useWorkspaceStore((s) => s.overview)
  const setActiveProject = useProjectStore((s) => s.setActiveProject)
  const lastRefreshed = useProjectStore((s) => s.lastRefreshed)
  const pollingError = useProjectStore((s) => s.pollingError)
  const isRefreshing = useProjectStore((s) => s.isRefreshing)

  const [gapData, setGapData] = useState<GapAnalysisData | null>(null)
  const [gapLoading, setGapLoading] = useState(false)
  const [selectedEventIndex, setSelectedEventIndex] = useState<number | null>(null)
  const [events, setEvents] = useState<WorkspaceEvent[]>([])
  const [eventsLoading, setEventsLoading] = useState(false)
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      setActiveProject(id)
      void loadWorkspace(id)
      loadGapAnalysis()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const loadGapAnalysis = async () => {
    setGapLoading(true)
    try {
      const data = await apiClient.getGapAnalysis(id)
      setGapData(data)
    } catch {
      setGapData(null)
    } finally {
      setGapLoading(false)
    }
  }

  const loadEvents = async (featureId?: string) => {
    setEventsLoading(true)
    try {
      const evts = await apiClient.getEvents(id, featureId)
      setEvents(evts)
    } catch {
      setEvents([])
    } finally {
      setEventsLoading(false)
    }
  }

  const handleRerun = async () => {
    const data = await apiClient.rerunGapAnalysis(id)
    setGapData(data)
  }

  const projectName = overview?.projectName ?? ''
  const selectedEvent = events.find((e) => e.eventIndex === selectedEventIndex) ?? null

  return (
    <div className="h-screen overflow-hidden flex flex-row bg-background">
      {/* Sidebar nav */}
      <WorkspaceSidebar workspaceId={id} projectName={projectName} />

      {/* Main content column */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Header */}
        <header className="flex-shrink-0 bg-secondary border-b px-4 h-12 flex items-center justify-between">
          <span className="font-semibold text-foreground">Evidence Browser</span>
          <div className="flex items-center gap-3">
            <FreshnessIndicator
              lastRefreshed={lastRefreshed}
              isRefreshing={isRefreshing}
              error={pollingError}
            />
            {/* Feature selector */}
            <select
              value={selectedFeatureId ?? ''}
              onChange={(e) => {
                const fid = e.target.value || null
                setSelectedFeatureId(fid)
                void loadEvents(fid ?? undefined)
              }}
              className="text-sm border border-border rounded px-2 py-1 bg-secondary text-foreground"
            >
              <option value="">All events</option>
              {traceability.map((e) => (
                <option key={e.reqKey} value={e.reqKey}>{e.reqKey}</option>
              ))}
            </select>
          </div>
        </header>

        {/* Body — two columns */}
        <div className="flex-1 overflow-hidden grid grid-cols-2 divide-x divide-border">
          {/* Left: Traceability + Gap Analysis */}
          <div className="overflow-y-auto p-4 flex flex-col gap-6">
            <section>
              <h2 className="text-sm font-semibold text-foreground/80 mb-3">Traceability Coverage</h2>
              <TraceabilityTable
                workspaceId={id}
                entries={traceability}
              />
            </section>
            <section>
              <GapAnalysisPanel
                data={gapData}
                loading={gapLoading}
                onRerun={handleRerun}
              />
            </section>
          </div>

          {/* Right: Event history + detail */}
          <div className="overflow-hidden flex flex-col divide-y divide-border">
            {/* Event list */}
            <div className="flex-1 overflow-y-auto p-4">
              <h2 className="text-sm font-semibold text-foreground/80 mb-3">
                Event History
                {selectedFeatureId && <span className="font-mono text-primary ml-2">{selectedFeatureId}</span>}
              </h2>
              {eventsLoading ? (
                <p className="text-sm text-muted-foreground/60">Loading events…</p>
              ) : events.length === 0 ? (
                <p className="text-sm text-muted-foreground/60 italic">
                  {selectedFeatureId ? 'No events for this feature.' : 'Select a feature to view its event history.'}
                </p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-muted-foreground border-b">
                      <th className="pb-1 pr-2 font-medium">#</th>
                      <th className="pb-1 pr-2 font-medium">Type</th>
                      <th className="pb-1 pr-2 font-medium">Edge</th>
                      <th className="pb-1 font-medium">Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50">
                    {events.map((evt) => (
                      <tr
                        key={evt.eventIndex}
                        onClick={() => setSelectedEventIndex(evt.eventIndex)}
                        className={`cursor-pointer hover:bg-muted/50 ${
                          selectedEventIndex === evt.eventIndex ? 'bg-primary/10' : ''
                        }`}
                      >
                        <td className="py-1.5 pr-2 text-xs text-muted-foreground/60 font-mono">{evt.eventIndex}</td>
                        <td className="py-1.5 pr-2 text-xs font-medium text-foreground/80">{evt.eventType}</td>
                        <td className="py-1.5 pr-2 text-xs text-muted-foreground">{evt.edge ?? '—'}</td>
                        <td className="py-1.5 text-xs text-muted-foreground/60">
                          {new Date(evt.timestamp).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Event detail */}
            <div className="flex-shrink-0 max-h-64 overflow-y-auto border-t">
              <EventDetailPanel
                workspaceId={id}
                event={selectedEvent}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
