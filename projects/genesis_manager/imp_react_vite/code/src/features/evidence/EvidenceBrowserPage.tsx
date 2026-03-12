// Implements: REQ-F-EVI-001, REQ-F-EVI-002, REQ-F-EVI-003, REQ-F-EVI-004, REQ-F-VIS-001

import React, { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProjectStore } from '../../stores/projectStore'
import { useWorkspaceStore } from '../../stores/workspaceStore'
import { apiClient } from '../../api/WorkspaceApiClient'
import { FreshnessIndicator } from '../../components/shared/FreshnessIndicator'
import { GapAnalysisPanel } from './GapAnalysisPanel'
import { WorkspaceSidebar } from '../../components/shared/WorkspaceSidebar'
import { buildFeaturePath } from '../../routing/routes'
import type { GapAnalysisData, WorkspaceEvent } from '../../api/types'

// ─── Event type colour coding ─────────────────────────────────────────────────

const EVENT_COLOURS: Record<string, string> = {
  edge_converged:      'text-emerald-400',
  iteration_completed: 'text-blue-400',
  edge_started:        'text-sky-400',
  review_approved:     'text-violet-400',
  spawn_created:       'text-amber-400',
  spawn_folded_back:   'text-amber-300',
  gaps_validated:      'text-teal-400',
  intent_raised:       'text-orange-400',
  auto_mode_set:       'text-slate-400',
  project_initialized: 'text-purple-400',
}

function eventColour(eventType: string): string {
  return EVENT_COLOURS[eventType] ?? 'text-muted-foreground'
}

// ─── Event detail panel ───────────────────────────────────────────────────────

function EventDetail({
  event,
  workspaceId,
  onClose,
}: {
  event: WorkspaceEvent
  workspaceId: string
  onClose: () => void
}): React.JSX.Element {
  const navigate = useNavigate()
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Event #{event.eventIndex}
        </span>
        <button
          onClick={onClose}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          ✕ close
        </button>
      </div>

      {/* Key fields */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div className="text-muted-foreground">Type</div>
        <div className={`font-mono font-medium ${eventColour(event.eventType)}`}>{event.eventType}</div>

        <div className="text-muted-foreground">Time</div>
        <div className="text-foreground/80">{new Date(event.timestamp).toLocaleString()}</div>

        {event.feature && (
          <>
            <div className="text-muted-foreground">Feature</div>
            <button
              onClick={() => navigate(buildFeaturePath(workspaceId, event.feature!))}
              className="font-mono text-primary hover:underline text-left"
            >
              {event.feature}
            </button>
          </>
        )}
        {event.edge && (
          <>
            <div className="text-muted-foreground">Edge</div>
            <div className="font-mono text-foreground/80">{event.edge}</div>
          </>
        )}
        {event.iteration != null && (
          <>
            <div className="text-muted-foreground">Iteration</div>
            <div className="text-foreground/80">#{event.iteration}</div>
          </>
        )}
        {event.delta != null && (
          <>
            <div className="text-muted-foreground">Delta (δ)</div>
            <div className={`font-mono font-medium ${event.delta === 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
              {event.delta}
            </div>
          </>
        )}
        {event.runId && (
          <>
            <div className="text-muted-foreground">Run ID</div>
            <div className="font-mono text-xs text-foreground/60 truncate" title={event.runId}>{event.runId}</div>
          </>
        )}
      </div>

      {/* Raw JSON */}
      <div>
        <p className="text-xs text-muted-foreground/60 mb-1">Raw JSON</p>
        <pre className="text-xs bg-black/40 text-green-300 rounded p-2 overflow-x-auto max-h-40">
          {JSON.stringify(event.raw, null, 2)}
        </pre>
      </div>
    </div>
  )
}

// ─── Traceability summary (inline, compact) ───────────────────────────────────

function TraceabilitySummary({
  entries,
  activeReqKey,
  onSelectReqKey,
}: {
  entries: { reqKey: string; taggedInCode: boolean; taggedInTests: boolean }[]
  activeReqKey: string | null
  onSelectReqKey: (k: string | null) => void
}): React.JSX.Element {
  const taggedCode = entries.filter((e) => e.taggedInCode).length
  const taggedTests = entries.filter((e) => e.taggedInTests).length
  const total = entries.length
  const pct = (n: number) => (total > 0 ? `${Math.round((n / total) * 100)}%` : '—')

  // Sort: gaps first, then converged
  const sorted = [...entries].sort((a, b) => {
    const aScore = (a.taggedInCode ? 1 : 0) + (a.taggedInTests ? 1 : 0)
    const bScore = (b.taggedInCode ? 1 : 0) + (b.taggedInTests ? 1 : 0)
    return aScore - bScore
  })

  return (
    <div className="flex flex-col gap-2">
      {/* Summary bars */}
      <div className="flex gap-4 text-xs text-muted-foreground">
        <span><span className="text-foreground font-medium">{total}</span> REQ keys</span>
        <span>Code <span className={taggedCode < total ? 'text-amber-400' : 'text-emerald-400'}>{taggedCode}/{total} ({pct(taggedCode)})</span></span>
        <span>Tests <span className={taggedTests < total ? 'text-amber-400' : 'text-emerald-400'}>{taggedTests}/{total} ({pct(taggedTests)})</span></span>
      </div>
      <div className="space-y-0.5">
        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
          <div className="h-full bg-sky-500 transition-all" style={{ width: `${total > 0 ? (taggedCode / total) * 100 : 0}%` }} />
        </div>
        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
          <div className="h-full bg-emerald-500 transition-all" style={{ width: `${total > 0 ? (taggedTests / total) * 100 : 0}%` }} />
        </div>
      </div>

      {/* REQ key pills — click to filter events */}
      <div className="flex flex-wrap gap-1 max-h-48 overflow-y-auto">
        {sorted.map((e) => {
          const covered = e.taggedInCode && e.taggedInTests
          const partial = e.taggedInCode || e.taggedInTests
          const isActive = activeReqKey === e.reqKey
          return (
            <button
              key={e.reqKey}
              onClick={() => onSelectReqKey(isActive ? null : e.reqKey)}
              title={`Code: ${e.taggedInCode ? '✓' : '✗'}  Tests: ${e.taggedInTests ? '✓' : '✗'}\nClick to filter events`}
              className={`font-mono text-[10px] px-1.5 py-0.5 rounded border transition-colors ${
                isActive
                  ? 'bg-primary/20 border-primary text-primary'
                  : covered
                  ? 'bg-emerald-900/20 border-emerald-800/40 text-emerald-400 hover:border-emerald-600'
                  : partial
                  ? 'bg-amber-900/20 border-amber-800/40 text-amber-400 hover:border-amber-600'
                  : 'bg-red-900/20 border-red-800/40 text-red-400 hover:border-red-600'
              }`}
            >
              {e.reqKey}
            </button>
          )
        })}
      </div>
      <p className="text-[10px] text-muted-foreground/50">
        <span className="inline-block w-2 h-2 rounded-sm bg-emerald-900/40 border border-emerald-800/40 mr-1" />code+tests
        <span className="inline-block w-2 h-2 rounded-sm bg-amber-900/40 border border-amber-800/40 mr-1 ml-2" />partial
        <span className="inline-block w-2 h-2 rounded-sm bg-red-900/40 border border-red-800/40 mr-1 ml-2" />missing
        &nbsp;· click to filter events
      </p>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

// EvidenceBrowserPage — event log (primary) + traceability/gap (secondary panel).
// Events load immediately. Feature and REQ key filters narrow the view.
// Clicking a REQ key pill filters events to those referencing it.
// Implements: REQ-F-EVI-001, REQ-F-EVI-002, REQ-F-EVI-003, REQ-F-EVI-004
export function EvidenceBrowserPage(): React.JSX.Element {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const id = workspaceId ?? ''

  const loadWorkspace = useWorkspaceStore((s) => s.loadWorkspace)
  const traceability = useWorkspaceStore((s) => s.traceability)
  const features = useWorkspaceStore((s) => s.features)
  const overview = useWorkspaceStore((s) => s.overview)
  const setActiveProject = useProjectStore((s) => s.setActiveProject)
  const lastRefreshed = useProjectStore((s) => s.lastRefreshed)
  const pollingError = useProjectStore((s) => s.pollingError)
  const isRefreshing = useProjectStore((s) => s.isRefreshing)

  const [gapData, setGapData] = useState<GapAnalysisData | null>(null)
  const [gapLoading, setGapLoading] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<WorkspaceEvent | null>(null)
  const [events, setEvents] = useState<WorkspaceEvent[]>([])
  const [eventsLoading, setEventsLoading] = useState(false)
  const [featureFilter, setFeatureFilter] = useState<string>('')
  const [reqKeyFilter, setReqKeyFilter] = useState<string | null>(null)
  const [showPanel, setShowPanel] = useState<'traceability' | 'gap'>('traceability')

  const loadEvents = useCallback(async (featureId?: string) => {
    setEventsLoading(true)
    try {
      const evts = await apiClient.getEvents(id, featureId)
      setEvents(evts)
    } catch {
      setEvents([])
    } finally {
      setEventsLoading(false)
    }
  }, [id])

  useEffect(() => {
    if (!id) return
    setActiveProject(id)
    void loadWorkspace(id)
    void loadEvents()
    setGapLoading(true)
    apiClient.getGapAnalysis(id)
      .then(setGapData)
      .catch(() => setGapData(null))
      .finally(() => setGapLoading(false))
  }, [id, loadWorkspace, setActiveProject, loadEvents])

  const handleRerun = async () => {
    const data = await apiClient.rerunGapAnalysis(id)
    setGapData(data)
  }

  const handleFeatureFilter = (fid: string) => {
    setFeatureFilter(fid)
    setReqKeyFilter(null)
    setSelectedEvent(null)
    void loadEvents(fid || undefined)
  }

  const handleReqKeyFilter = (key: string | null) => {
    setReqKeyFilter(key)
    setSelectedEvent(null)
  }

  // Apply req key filter client-side (events already filtered by feature server-side)
  const visibleEvents = reqKeyFilter
    ? events.filter((e) => JSON.stringify(e.raw).includes(reqKeyFilter))
    : events

  // Newest first
  const displayEvents = [...visibleEvents].reverse()

  const projectName = overview?.projectName ?? ''

  return (
    <div className="h-screen overflow-hidden flex flex-row bg-background">
      <WorkspaceSidebar workspaceId={id} projectName={projectName} />

      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Header */}
        <header className="flex-shrink-0 bg-secondary border-b px-4 h-12 flex items-center gap-3">
          <span className="font-semibold text-foreground">Evidence</span>
          <div className="w-px h-4 bg-border" />
          {/* Feature filter */}
          <select
            value={featureFilter}
            onChange={(e) => handleFeatureFilter(e.target.value)}
            className="text-xs border border-border rounded px-2 py-1 bg-background text-foreground"
          >
            <option value="">All features</option>
            {features.map((f) => (
              <option key={f.featureId} value={f.featureId}>{f.featureId}</option>
            ))}
          </select>
          {reqKeyFilter && (
            <span className="flex items-center gap-1 text-xs bg-primary/10 border border-primary/30 text-primary rounded px-2 py-0.5">
              {reqKeyFilter}
              <button onClick={() => setReqKeyFilter(null)} className="hover:text-foreground ml-1">✕</button>
            </span>
          )}
          <div className="ml-auto">
            <FreshnessIndicator lastRefreshed={lastRefreshed} isRefreshing={isRefreshing} error={pollingError} />
          </div>
        </header>

        {/* Body — event log (main) + right panel */}
        <div className="flex-1 overflow-hidden flex divide-x divide-border">

          {/* ── Event log ── */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {/* Event count / context */}
            <div className="flex-shrink-0 px-4 py-2 border-b bg-secondary/50 flex items-center gap-3 text-xs text-muted-foreground">
              <span>
                Event log
                {featureFilter && <span className="font-mono text-primary ml-1">{featureFilter}</span>}
                {reqKeyFilter && <span className="font-mono text-primary ml-1">· {reqKeyFilter}</span>}
              </span>
              <span className="ml-auto font-medium text-foreground/70">
                {eventsLoading ? 'Loading…' : `${visibleEvents.length} event${visibleEvents.length !== 1 ? 's' : ''}`}
              </span>
              <span className="text-muted-foreground/50">newest first</span>
            </div>

            {/* Events table */}
            <div className="flex-1 overflow-y-auto">
              {eventsLoading ? (
                <div className="flex items-center justify-center py-12 text-sm text-muted-foreground/60">Loading events…</div>
              ) : displayEvents.length === 0 ? (
                <div className="flex items-center justify-center py-12 text-sm text-muted-foreground/60 italic">
                  {featureFilter || reqKeyFilter ? 'No events match the current filter.' : 'No events recorded yet.'}
                </div>
              ) : (
                <table className="w-full text-xs">
                  <thead className="sticky top-0 bg-background z-10">
                    <tr className="text-left text-muted-foreground border-b">
                      <th className="px-4 py-2 font-medium w-10">#</th>
                      <th className="px-2 py-2 font-medium">Event type</th>
                      <th className="px-2 py-2 font-medium">Feature</th>
                      <th className="px-2 py-2 font-medium">Edge</th>
                      <th className="px-2 py-2 font-medium text-right w-10">iter</th>
                      <th className="px-2 py-2 font-medium text-right w-10">δ</th>
                      <th className="px-4 py-2 font-medium text-right">Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40">
                    {displayEvents.map((evt) => (
                      <tr
                        key={evt.eventIndex}
                        onClick={() => setSelectedEvent(selectedEvent?.eventIndex === evt.eventIndex ? null : evt)}
                        className={`cursor-pointer hover:bg-muted/30 transition-colors ${
                          selectedEvent?.eventIndex === evt.eventIndex ? 'bg-primary/10' : ''
                        }`}
                      >
                        <td className="px-4 py-1.5 font-mono text-muted-foreground/40">{evt.eventIndex}</td>
                        <td className={`px-2 py-1.5 font-mono font-medium ${eventColour(evt.eventType)}`}>
                          {evt.eventType}
                        </td>
                        <td className="px-2 py-1.5 font-mono text-foreground/60">{evt.feature ?? '—'}</td>
                        <td className="px-2 py-1.5 text-muted-foreground/70">{evt.edge ?? '—'}</td>
                        <td className="px-2 py-1.5 text-right text-muted-foreground/60">
                          {evt.iteration != null ? `#${evt.iteration}` : '—'}
                        </td>
                        <td className={`px-2 py-1.5 text-right font-mono ${
                          evt.delta == null ? 'text-muted-foreground/40' : evt.delta === 0 ? 'text-emerald-400' : 'text-amber-400'
                        }`}>
                          {evt.delta != null ? evt.delta : '—'}
                        </td>
                        <td className="px-4 py-1.5 text-right text-muted-foreground/50">
                          {new Date(evt.timestamp).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Event detail — inline below the table */}
            {selectedEvent && (
              <div className="flex-shrink-0 border-t bg-secondary/50 p-4 max-h-72 overflow-y-auto">
                <EventDetail
                  event={selectedEvent}
                  workspaceId={id}
                  onClose={() => setSelectedEvent(null)}
                />
              </div>
            )}
          </div>

          {/* ── Right panel: Traceability + Gap ── */}
          <div className="w-80 flex-shrink-0 overflow-hidden flex flex-col">
            {/* Panel tabs */}
            <div className="flex-shrink-0 flex border-b text-xs">
              <button
                onClick={() => setShowPanel('traceability')}
                className={`flex-1 px-3 py-2 font-medium transition-colors ${
                  showPanel === 'traceability' ? 'text-foreground border-b-2 border-primary' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Traceability
              </button>
              <button
                onClick={() => setShowPanel('gap')}
                className={`flex-1 px-3 py-2 font-medium transition-colors ${
                  showPanel === 'gap' ? 'text-foreground border-b-2 border-primary' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Gap Analysis
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-3">
              {showPanel === 'traceability' ? (
                <TraceabilitySummary
                  entries={traceability}
                  activeReqKey={reqKeyFilter}
                  onSelectReqKey={handleReqKeyFilter}
                />
              ) : (
                <GapAnalysisPanel
                  data={gapData}
                  loading={gapLoading}
                  onRerun={handleRerun}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
