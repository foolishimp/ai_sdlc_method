// @vitest-environment node
// Validates: REQ-F-PROJ-004

import { describe, it, expect, vi, beforeEach } from 'vitest'
import path from 'node:path'
import os from 'node:os'

vi.mock('node:fs/promises', () => ({
  default: {
    readFile: vi.fn(),
    readdir: vi.fn(),
    stat: vi.fn(),
    mkdir: vi.fn(),
    writeFile: vi.fn(),
    rename: vi.fn(),
    appendFile: vi.fn(),
    access: vi.fn(),
  },
}))

import fs from 'node:fs/promises'
import {
  generateWorkspaceId,
  findById,
  loadRegistry,
  saveRegistry,
} from '../../../server/lib/workspaceRegistry'
import type { WorkspaceRegistration } from '../../../server/types'

const mockReadFile = vi.mocked(fs.readFile)
const mockWriteFile = vi.mocked(fs.writeFile)
const mockRename = vi.mocked(fs.rename)
const mockMkdir = vi.mocked(fs.mkdir)

const REGISTRY_FILE = path.join(os.homedir(), '.genesis_manager', 'workspaces.json')
const TMP_FILE = `${REGISTRY_FILE}.tmp`

// ---------------------------------------------------------------------------
// generateWorkspaceId
// ---------------------------------------------------------------------------

describe('generateWorkspaceId', () => {
  it('returns exactly 12 characters', () => {
    const id = generateWorkspaceId('/some/path')
    expect(id).toHaveLength(12)
  })

  it('returns only lowercase hex characters', () => {
    const id = generateWorkspaceId('/some/path')
    expect(id).toMatch(/^[0-9a-f]{12}$/)
  })

  it('is deterministic — same path produces same id', () => {
    const id1 = generateWorkspaceId('/workspace/project-a')
    const id2 = generateWorkspaceId('/workspace/project-a')
    expect(id1).toBe(id2)
  })

  it('produces different ids for different paths', () => {
    const id1 = generateWorkspaceId('/workspace/project-a')
    const id2 = generateWorkspaceId('/workspace/project-b')
    expect(id1).not.toBe(id2)
  })

  it('handles paths with spaces and special chars', () => {
    const id = generateWorkspaceId('/my projects/hello world')
    expect(id).toMatch(/^[0-9a-f]{12}$/)
  })
})

// ---------------------------------------------------------------------------
// findById
// ---------------------------------------------------------------------------

describe('findById', () => {
  const regs: WorkspaceRegistration[] = [
    { id: 'aabbccddeeff', path: '/path/a', name: 'Alpha' },
    { id: '112233445566', path: '/path/b', name: 'Beta' },
  ]

  it('returns undefined for an empty array', () => {
    expect(findById('aabbccddeeff', [])).toBeUndefined()
  })

  it('returns the registration when id exists', () => {
    const found = findById('aabbccddeeff', regs)
    expect(found).toBeDefined()
    expect(found!.name).toBe('Alpha')
    expect(found!.path).toBe('/path/a')
  })

  it('returns undefined for a non-existent id', () => {
    expect(findById('000000000000', regs)).toBeUndefined()
  })

  it('does not return a partial match', () => {
    expect(findById('aabbccddee', regs)).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// loadRegistry
// ---------------------------------------------------------------------------

describe('loadRegistry', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mockMkdir.mockResolvedValue(undefined)
  })

  it('returns [] when file does not exist (ENOENT) and saves empty registry', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReadFile.mockRejectedValueOnce(err)
    // saveRegistry calls mkdir + writeFile + rename
    mockWriteFile.mockResolvedValue(undefined)
    mockRename.mockResolvedValue(undefined)

    const result = await loadRegistry()
    expect(result).toEqual([])
    // saveRegistry is called with []
    expect(mockWriteFile).toHaveBeenCalledWith(TMP_FILE, JSON.stringify([], null, 2), 'utf-8')
    expect(mockRename).toHaveBeenCalledWith(TMP_FILE, REGISTRY_FILE)
  })

  it('returns parsed array when file contains valid JSON array', async () => {
    const data: WorkspaceRegistration[] = [
      { id: 'abc123def456', path: '/workspace', name: 'My Project' },
    ]
    mockReadFile.mockResolvedValueOnce(JSON.stringify(data))

    const result = await loadRegistry()
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('abc123def456')
    expect(result[0].name).toBe('My Project')
  })

  it('returns [] when file content is not a JSON array (object)', async () => {
    mockReadFile.mockResolvedValueOnce(JSON.stringify({ not: 'an array' }))

    const result = await loadRegistry()
    expect(result).toEqual([])
  })

  it('returns [] when file content is not a JSON array (string)', async () => {
    mockReadFile.mockResolvedValueOnce(JSON.stringify('hello'))

    const result = await loadRegistry()
    expect(result).toEqual([])
  })

  it('rethrows non-ENOENT errors', async () => {
    const err = Object.assign(new Error('Permission denied'), { code: 'EACCES' })
    mockReadFile.mockRejectedValueOnce(err)

    await expect(loadRegistry()).rejects.toThrow('Permission denied')
  })

  it('calls mkdir with recursive:true to ensure directory exists', async () => {
    mockReadFile.mockResolvedValueOnce('[]')

    await loadRegistry()
    expect(mockMkdir).toHaveBeenCalledWith(
      path.join(os.homedir(), '.genesis_manager'),
      { recursive: true },
    )
  })
})

// ---------------------------------------------------------------------------
// saveRegistry
// ---------------------------------------------------------------------------

describe('saveRegistry', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mockMkdir.mockResolvedValue(undefined)
    mockWriteFile.mockResolvedValue(undefined)
    mockRename.mockResolvedValue(undefined)
  })

  it('writes JSON to a .tmp file before renaming', async () => {
    const regs: WorkspaceRegistration[] = [
      { id: 'abc123def456', path: '/workspace', name: 'Test' },
    ]

    await saveRegistry(regs)

    expect(mockWriteFile).toHaveBeenCalledWith(TMP_FILE, JSON.stringify(regs, null, 2), 'utf-8')
  })

  it('renames .tmp file to registry file for atomic swap', async () => {
    await saveRegistry([])

    expect(mockRename).toHaveBeenCalledWith(TMP_FILE, REGISTRY_FILE)
  })

  it('calls mkdir to ensure directory exists before writing', async () => {
    await saveRegistry([])

    expect(mockMkdir).toHaveBeenCalledWith(
      path.join(os.homedir(), '.genesis_manager'),
      { recursive: true },
    )
  })

  it('serialises empty array correctly', async () => {
    await saveRegistry([])

    expect(mockWriteFile).toHaveBeenCalledWith(TMP_FILE, JSON.stringify([], null, 2), 'utf-8')
  })
})
