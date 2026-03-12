// Implements: REQ-F-EVI-001
// Walks the project source tree and extracts Implements/Validates REQ-key tags
// from source files. Uses an mtime-based in-memory cache so repeated API calls
// within a polling interval are cheap.

import fs from 'node:fs/promises';
import { Dirent } from 'node:fs';
import path from 'node:path';
import type { TraceabilityEntry } from '../types.js';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SCAN_EXTENSIONS = new Set(['.py', '.ts', '.tsx', '.js', '.sh']);
const SCAN_EXCLUDE = new Set([
  'node_modules',
  '.git',
  'dist',
  'build',
  '__pycache__',
  '.venv',
  'venv',
  'coverage',
  '.mypy_cache',
]);

// Matches both # and // comment styles
const IMPLEMENTS_RE =
  /(?:#|\/\/)\s*Implements:\s*(REQ-[A-Z][A-Z0-9-]*[A-Z0-9]-\d+)/g;
const VALIDATES_RE =
  /(?:#|\/\/)\s*Validates:\s*(REQ-[A-Z][A-Z0-9-]*[A-Z0-9]-\d+)/g;

// ---------------------------------------------------------------------------
// Mtime-based cache
// ---------------------------------------------------------------------------

interface CacheEntry {
  mtime: number;
  entries: TraceabilityEntry[];
}

const mtimeCache = new Map<string, CacheEntry>();

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

async function walkDir(
  dir: string,
  onFile: (filePath: string) => Promise<void>,
): Promise<void> {
  let entries: Dirent[];
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return; // Directory may have disappeared; skip silently
  }

  for (const entry of entries) {
    if (SCAN_EXCLUDE.has(entry.name)) continue;

    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      await walkDir(fullPath, onFile);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name);
      if (SCAN_EXTENSIONS.has(ext) && !entry.name.endsWith('.d.ts') && !entry.name.endsWith('.min.js')) {
        await onFile(fullPath);
      }
    }
  }
}

async function scanFile(filePath: string): Promise<TraceabilityEntry[]> {
  // Check cache first
  let stat: { mtimeMs: number };
  try {
    stat = await fs.stat(filePath);
  } catch {
    return [];
  }

  const cached = mtimeCache.get(filePath);
  if (cached && cached.mtime === stat.mtimeMs) {
    return cached.entries;
  }

  let content: string;
  try {
    content = await fs.readFile(filePath, 'utf-8');
  } catch {
    return [];
  }

  const entries: TraceabilityEntry[] = [];
  const lines = content.split('\n');

  for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
    const line = lines[lineIdx];

    // Reset lastIndex for global regexes before each line
    IMPLEMENTS_RE.lastIndex = 0;
    VALIDATES_RE.lastIndex = 0;

    let match: RegExpExecArray | null;

    while ((match = IMPLEMENTS_RE.exec(line)) !== null) {
      entries.push({
        reqKey: match[1],
        kind: 'implements',
        filePath,
        lineNumber: lineIdx + 1,
      });
    }

    VALIDATES_RE.lastIndex = 0;
    while ((match = VALIDATES_RE.exec(line)) !== null) {
      entries.push({
        reqKey: match[1],
        kind: 'validates',
        filePath,
        lineNumber: lineIdx + 1,
      });
    }
  }

  mtimeCache.set(filePath, { mtime: stat.mtimeMs, entries });
  return entries;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Walk the project source tree rooted at `projectRoot` and return all
 * traceability entries found in source and test files.
 *
 * Results are mtime-cached per file — subsequent calls for unchanged files
 * return the cached entries immediately.
 */
export async function scan(projectRoot: string): Promise<TraceabilityEntry[]> {
  const allEntries: TraceabilityEntry[] = [];

  await walkDir(projectRoot, async (filePath) => {
    const fileEntries = await scanFile(filePath);
    allEntries.push(...fileEntries);
  });

  return allEntries;
}
