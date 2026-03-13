#!/usr/bin/env tsx
// Implements: REQ-TEST-003
/**
 * e2e/capture.ts — Headless Playwright page capture for spec evaluation
 *
 * Usage:
 *   npx tsx e2e/capture.ts --page overview --workspace 0097a6f8a46c
 *   npx tsx e2e/capture.ts --page supervision
 *   npx tsx e2e/capture.ts --page feature-detail --feature REQ-F-FSNAV-001
 *   npx tsx e2e/capture.ts --page evidence
 *   npx tsx e2e/capture.ts --all
 *
 * Output: e2e/screenshots/{page}.png  (overwrites; use --suffix for timestamped)
 *
 * The saved paths are printed to stdout so Claude can Read them for spec evaluation.
 */

import { chromium, type Page } from '@playwright/test'
import * as path from 'node:path'
import * as fs from 'node:fs/promises'
import * as os from 'node:os'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// ─── Config ──────────────────────────────────────────────────────────────────

const BASE_URL = process.env.VITE_APP_URL ?? 'http://localhost:5174'
const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots')
const VIEWPORT = { width: 1440, height: 900 }
const WAIT_TIMEOUT = 8000     // ms to wait for page content after navigation
const REGISTRY_FILE = path.join(os.homedir(), '.genesis_manager', 'workspaces.json')

// ─── Arg parsing ─────────────────────────────────────────────────────────────

interface Args {
  page: string | null
  all: boolean
  workspaceId: string | null
  featureId: string | null
  suffix: string
}

function parseArgs(): Args {
  const args = process.argv.slice(2)
  const get = (flag: string) => {
    const i = args.indexOf(flag)
    return i !== -1 && i + 1 < args.length ? args[i + 1] : null
  }
  return {
    page: get('--page'),
    all: args.includes('--all'),
    workspaceId: get('--workspace'),
    featureId: get('--feature'),
    suffix: get('--suffix') ?? '',
  }
}

// ─── Registry ─────────────────────────────────────────────────────────────────

async function getFirstWorkspaceId(): Promise<string> {
  try {
    const raw = await fs.readFile(REGISTRY_FILE, 'utf-8')
    const entries = JSON.parse(raw) as Array<{ id: string; name: string }>
    if (entries.length === 0) throw new Error('No workspaces registered')
    return entries[0].id
  } catch {
    throw new Error(`Could not read workspace registry at ${REGISTRY_FILE}`)
  }
}

// ─── Page definitions ────────────────────────────────────────────────────────

interface PageDef {
  name: string
  url: (wsId: string, featureId?: string) => string
  waitFor: string          // CSS selector to wait for (signals page is loaded)
  specFile: string         // relative to specification/pages/
}

const PAGES: Record<string, PageDef> = {
  'project-list': {
    name: 'project-list',
    url: () => '/',
    waitFor: '[data-testid="project-list"], .project-card, main',
    specFile: 'PROJECT_LIST_PAGE.md',
  },
  'overview': {
    name: 'overview',
    url: (wsId) => `/project/${wsId}/overview`,
    waitFor: '[data-testid="overview"], .feature-status-counts, header',
    specFile: 'OVERVIEW_PAGE.md',
  },
  'supervision': {
    name: 'supervision',
    url: (wsId) => `/project/${wsId}/supervision`,
    waitFor: '[data-testid="supervision"], .feature-list, header',
    specFile: 'SUPERVISION_PAGE.md',
  },
  'evidence': {
    name: 'evidence',
    url: (wsId) => `/project/${wsId}/evidence`,
    waitFor: '[data-testid="evidence"], table, header',
    specFile: 'EVIDENCE_PAGE.md',
  },
  'feature-detail': {
    name: 'feature-detail',
    url: (wsId, fid = 'REQ-F-FSNAV-001') => `/project/${wsId}/feature/${fid}`,
    waitFor: '[data-testid="feature-detail"], .edge-card, header',
    specFile: 'FEATURE_DETAIL_PAGE.md',
  },
}

// ─── Capture ──────────────────────────────────────────────────────────────────

async function capturePage(
  page: Page,
  def: PageDef,
  wsId: string,
  featureId: string | null,
  suffix: string,
): Promise<string> {
  const url = def.url(wsId, featureId ?? undefined)
  const filename = suffix ? `${def.name}-${suffix}.png` : `${def.name}.png`
  const outputPath = path.join(SCREENSHOTS_DIR, filename)

  console.log(`  → ${BASE_URL}${url}`)
  await page.goto(`${BASE_URL}${url}`, { waitUntil: 'networkidle', timeout: WAIT_TIMEOUT })

  // Wait for meaningful content (try selector, fall back to timeout)
  try {
    await page.waitForSelector(def.waitFor, { timeout: 3000 })
  } catch {
    // Selector not found — page may use different structure; wait a beat anyway
    await page.waitForTimeout(1500)
  }

  // Additional wait for any async data fetch to settle
  await page.waitForTimeout(800)

  await page.screenshot({ path: outputPath, fullPage: false })
  return outputPath
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs()

  await fs.mkdir(SCREENSHOTS_DIR, { recursive: true })

  const wsId = args.workspaceId ?? await getFirstWorkspaceId()
  console.log(`Workspace: ${wsId}`)
  console.log(`Base URL:  ${BASE_URL}`)
  console.log(`Viewport:  ${VIEWPORT.width}×${VIEWPORT.height}`)
  console.log()

  const pagesToCapture: PageDef[] = args.all
    ? Object.values(PAGES)
    : args.page
      ? [PAGES[args.page] ?? (() => { throw new Error(`Unknown page: ${args.page}. Valid: ${Object.keys(PAGES).join(', ')}`) })()]
      : (() => { throw new Error('Specify --page <name> or --all') })()

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({ viewport: VIEWPORT })
  const page = await context.newPage()

  // Suppress console noise from the app
  page.on('console', () => {})
  page.on('pageerror', () => {})

  const captured: string[] = []

  for (const def of pagesToCapture) {
    console.log(`Capturing: ${def.name}`)
    try {
      const outputPath = await capturePage(page, def, wsId, args.featureId, args.suffix)
      console.log(`  ✓ saved: ${outputPath}`)
      captured.push(outputPath)
    } catch (err) {
      console.error(`  ✗ failed: ${err instanceof Error ? err.message : err}`)
    }
  }

  await browser.close()

  console.log()
  console.log('─── Screenshot paths (for spec evaluation) ───')
  for (const p of captured) {
    console.log(p)
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
