// Implements: REQ-F-EVI-001

import React, { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import type { TraceabilityEntry } from '../../api/types'
import { buildReqPath } from '../../routing/routes'

type SortKey = 'reqKey' | 'code' | 'tests'
type SortDir = 'asc' | 'desc'

interface TraceabilityTableProps {
  workspaceId: string
  entries: TraceabilityEntry[]
  loading?: boolean
}

// TraceabilityTable — sortable REQ key coverage table.
// Untagged keys link to their detail page.
// Implements: REQ-F-EVI-001
export function TraceabilityTable({ workspaceId, entries, loading }: TraceabilityTableProps): React.JSX.Element {
  const navigate = useNavigate()
  const [sortKey, setSortKey] = useState<SortKey>('reqKey')
  const [sortDir, setSortDir] = useState<SortDir>('asc')

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const sorted = useMemo(() => {
    return [...entries].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'reqKey') {
        cmp = a.reqKey.localeCompare(b.reqKey)
      } else if (sortKey === 'code') {
        cmp = Number(a.taggedInCode) - Number(b.taggedInCode)
      } else if (sortKey === 'tests') {
        cmp = Number(a.taggedInTests) - Number(b.taggedInTests)
      }
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [entries, sortKey, sortDir])

  const taggedCode = entries.filter((e) => e.taggedInCode).length
  const taggedTests = entries.filter((e) => e.taggedInTests).length
  const total = entries.length

  const pct = (n: number) => total > 0 ? `${Math.round((n / total) * 100)}%` : '—'

  if (loading) {
    return <div className="p-4 text-gray-400 text-sm">Loading traceability data…</div>
  }

  const SortHeader = ({ label, key }: { label: string; key: SortKey }) => (
    <th
      className="text-left pb-1 pr-3 text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-800 select-none"
      onClick={() => handleSort(key)}
    >
      {label} {sortKey === key ? (sortDir === 'asc' ? '↑' : '↓') : ''}
    </th>
  )

  return (
    <div className="flex flex-col gap-3">
      {/* Coverage summary */}
      <div className="flex gap-4 text-xs">
        <div>
          <span className="font-medium">{total}</span> REQ keys
        </div>
        <div>
          Code: <span className={`font-medium ${taggedCode < total ? 'text-red-600' : 'text-green-600'}`}>
            {taggedCode}/{total} ({pct(taggedCode)})
          </span>
        </div>
        <div>
          Tests: <span className={`font-medium ${taggedTests < total ? 'text-red-600' : 'text-green-600'}`}>
            {taggedTests}/{total} ({pct(taggedTests)})
          </span>
        </div>
      </div>

      {/* Progress bars */}
      <div className="space-y-1">
        <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all"
            style={{ width: total > 0 ? `${(taggedCode / total) * 100}%` : '0%' }}
          />
        </div>
        <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all"
            style={{ width: total > 0 ? `${(taggedTests / total) * 100}%` : '0%' }}
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <SortHeader label="REQ Key" key="reqKey" />
              <SortHeader label="Code" key="code" />
              <SortHeader label="Tests" key="tests" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sorted.map((entry) => (
              <tr key={entry.reqKey} className="hover:bg-gray-50">
                <td className="py-1.5 pr-3">
                  <button
                    onClick={() => navigate(buildReqPath(workspaceId, entry.reqKey))}
                    className="font-mono text-xs text-blue-700 hover:underline"
                  >
                    {entry.reqKey}
                  </button>
                </td>
                <td className="py-1.5 pr-3">
                  {entry.taggedInCode ? (
                    <span className="text-xs text-green-700">✓</span>
                  ) : (
                    <span className="text-xs text-red-500">✗</span>
                  )}
                </td>
                <td className="py-1.5">
                  {entry.taggedInTests ? (
                    <span className="text-xs text-green-700">✓</span>
                  ) : (
                    <span className="text-xs text-red-500">✗</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
