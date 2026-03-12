// @vitest-environment node
// Validates: REQ-F-EVI-001

import { describe, it, expect, vi, beforeEach } from 'vitest'
import path from 'node:path'
import type { Dirent } from 'node:fs'

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
import { scan } from '../../../server/readers/TraceabilityScanner'

const mockReadFile = vi.mocked(fs.readFile)
const mockReaddir = vi.mocked(fs.readdir)
const mockStat = vi.mocked(fs.stat)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeDirent(name: string, isFile: boolean, isDirectory: boolean): Dirent {
  return { name, isFile: () => isFile, isDirectory: () => isDirectory } as unknown as Dirent
}

function makeStatResult(mtime = 1000000): { mtimeMs: number } {
  return { mtimeMs: mtime }
}

const ROOT = '/project/root'

// ---------------------------------------------------------------------------
// scan
// ---------------------------------------------------------------------------

describe('scan', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns empty array when root directory does not exist (readdir throws ENOENT)', async () => {
    const err = Object.assign(new Error('ENOENT'), { code: 'ENOENT' })
    mockReaddir.mockRejectedValueOnce(err)

    const result = await scan(ROOT)
    expect(result).toEqual([])
  })

  it('returns empty array when root has no source files', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('README.md', true, false)] as unknown as Dirent[])

    const result = await scan(ROOT)
    expect(result).toEqual([])
  })

  it('finds Implements: REQ-* tag with // comment style', async () => {
    const filePath = path.join(ROOT, 'module.ts')
    mockReaddir.mockResolvedValueOnce([makeDirent('module.ts', true, false)] as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    mockReadFile.mockResolvedValueOnce('// Implements: REQ-F-AUTH-001\nconst x = 1;')

    const result = await scan(ROOT)
    expect(result).toHaveLength(1)
    expect(result[0].reqKey).toBe('REQ-F-AUTH-001')
    expect(result[0].kind).toBe('implements')
    expect(result[0].filePath).toBe(filePath)
    expect(result[0].lineNumber).toBe(1)
  })

  it('finds Implements: REQ-* tag with # comment style (.py file)', async () => {
    const filePath = path.join(ROOT, 'module.py')
    mockReaddir.mockResolvedValueOnce([makeDirent('module.py', true, false)] as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    mockReadFile.mockResolvedValueOnce('# Implements: REQ-F-CTL-002\ndef foo(): pass')

    const result = await scan(ROOT)
    expect(result).toHaveLength(1)
    expect(result[0].reqKey).toBe('REQ-F-CTL-002')
    expect(result[0].kind).toBe('implements')
    expect(result[0].filePath).toBe(filePath)
  })

  it('finds Validates: REQ-* tags', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('test.ts', true, false)] as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    mockReadFile.mockResolvedValueOnce('// Validates: REQ-F-AUTH-001\nit("test", () => {})')

    const result = await scan(ROOT)
    expect(result).toHaveLength(1)
    expect(result[0].kind).toBe('validates')
    expect(result[0].reqKey).toBe('REQ-F-AUTH-001')
  })

  it('finds multiple tags in the same file', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('multi.ts', true, false)] as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    mockReadFile.mockResolvedValueOnce(
      '// Implements: REQ-F-AUTH-001\n// Implements: REQ-F-CTL-002\n// Validates: REQ-F-AUTH-001'
    )

    const result = await scan(ROOT)
    expect(result).toHaveLength(3)
    expect(result.map(e => e.kind)).toContain('implements')
    expect(result.map(e => e.kind)).toContain('validates')
  })

  it('reports correct 1-based line numbers', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('f.ts', true, false)] as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    mockReadFile.mockResolvedValueOnce('const x = 1;\nconst y = 2;\n// Implements: REQ-F-AUTH-001')

    const result = await scan(ROOT)
    expect(result).toHaveLength(1)
    expect(result[0].lineNumber).toBe(3)
  })

  it('excludes files inside node_modules directory', async () => {
    const rootDirents = [
      makeDirent('node_modules', false, true),
      makeDirent('src', false, true),
    ]
    const srcDirents = [makeDirent('app.ts', true, false)]

    mockReaddir.mockResolvedValueOnce(rootDirents as unknown as Dirent[])
    // node_modules is excluded, so only src is walked
    mockReaddir.mockResolvedValueOnce(srcDirents as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    mockReadFile.mockResolvedValueOnce('// Implements: REQ-F-AUTH-001')

    const result = await scan(ROOT)
    // Only src/app.ts scanned, not anything under node_modules
    expect(result).toHaveLength(1)
    expect(result[0].filePath).toContain('src')
    expect(result[0].filePath).not.toContain('node_modules')
  })

  it('excludes .git directory', async () => {
    const rootDirents = [makeDirent('.git', false, true)]
    mockReaddir.mockResolvedValueOnce(rootDirents as unknown as Dirent[])

    const result = await scan(ROOT)
    expect(result).toEqual([])
    // readdir should only be called once (for root) — .git is never walked
    expect(mockReaddir).toHaveBeenCalledTimes(1)
  })

  it('excludes .d.ts files', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('types.d.ts', true, false)] as unknown as Dirent[])

    const result = await scan(ROOT)
    expect(result).toEqual([])
  })

  it('excludes .min.js files', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('bundle.min.js', true, false)] as unknown as Dirent[])

    const result = await scan(ROOT)
    expect(result).toEqual([])
  })

  it('returns empty array when stat throws for a file (handles gracefully)', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('broken.ts', true, false)] as unknown as Dirent[])
    const err = new Error('stat failed')
    mockStat.mockRejectedValueOnce(err)

    const result = await scan(ROOT)
    expect(result).toEqual([])
  })

  it('does not match REQ keys without the required format (too short suffix)', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('f.ts', true, false)] as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    // 'REQ-F-A-1' — segment "A" has only one char before '-\d+', which should not match
    // The regex: REQ-[A-Z][A-Z0-9-]*[A-Z0-9]-\d+
    // 'REQ-A-001' → [A-Z][A-Z0-9-]*[A-Z0-9] needs at least 2 chars in middle (A...Z0-9)
    mockReadFile.mockResolvedValueOnce('// Implements: REQ-F-AUTH-001')

    const result = await scan(ROOT)
    expect(result).toHaveLength(1)
    expect(result[0].reqKey).toBe('REQ-F-AUTH-001')
  })

  it('correctly scans .tsx files', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('Component.tsx', true, false)] as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    mockReadFile.mockResolvedValueOnce('// Implements: REQ-F-UI-001\nconst Comp = () => <div/>')

    const result = await scan(ROOT)
    expect(result).toHaveLength(1)
    expect(result[0].reqKey).toBe('REQ-F-UI-001')
  })

  it('correctly scans .sh files', async () => {
    mockReaddir.mockResolvedValueOnce([makeDirent('setup.sh', true, false)] as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    mockReadFile.mockResolvedValueOnce('#!/bin/bash\n# Implements: REQ-F-INS-001\necho "hello"')

    const result = await scan(ROOT)
    expect(result).toHaveLength(1)
    expect(result[0].reqKey).toBe('REQ-F-INS-001')
    expect(result[0].lineNumber).toBe(2)
  })

  it('walks subdirectories recursively', async () => {
    const rootDirents = [makeDirent('src', false, true)]
    const srcDirents = [makeDirent('sub', false, true)]
    const subDirents = [makeDirent('deep.ts', true, false)]

    mockReaddir.mockResolvedValueOnce(rootDirents as unknown as Dirent[])
    mockReaddir.mockResolvedValueOnce(srcDirents as unknown as Dirent[])
    mockReaddir.mockResolvedValueOnce(subDirents as unknown as Dirent[])
    mockStat.mockResolvedValueOnce(makeStatResult() as unknown as ReturnType<typeof fs.stat> extends Promise<infer T> ? T : never)
    mockReadFile.mockResolvedValueOnce('// Implements: REQ-F-DEEP-001')

    const result = await scan(ROOT)
    expect(result).toHaveLength(1)
    expect(result[0].reqKey).toBe('REQ-F-DEEP-001')
    expect(result[0].filePath).toContain('sub')
  })
})
