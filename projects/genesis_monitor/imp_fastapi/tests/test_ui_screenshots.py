# Validates: REQ-F-DASH-001, REQ-F-DASH-002, REQ-NFR-001
"""
Playwright screenshot tests for Genesis Monitor UI.

Requires a running genesis-monitor server and Chromium:
    genesis-monitor --watch-dir . --watch-dir projects/ --port 8000 &

Run:
    pytest tests/test_ui_screenshots.py -v -m ui

Screenshots saved to: tests/screenshots/

Mark: ui — skipped automatically if server is unreachable or Playwright unavailable.
"""

import asyncio
import socket
import time
from pathlib import Path

import pytest

# ── Constants ──────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
LOAD_TIMEOUT_MS = 10_000   # page.goto timeout
SETTLE_MS = 800            # wait after DOMContentLoaded for HTMX/Mermaid rendering
MAX_LOAD_TIME_S = 3.0      # pages must load within this threshold

# ── Server availability guard ──────────────────────────────────────────────────

def _server_up() -> bool:
    try:
        s = socket.create_connection(("localhost", 8000), timeout=1.0)
        s.close()
        return True
    except OSError:
        return False


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


# ── Core async helpers ─────────────────────────────────────────────────────────

async def _screenshot(url: str, name: str, *, full_page: bool = True) -> float:
    """Navigate, settle, screenshot. Returns elapsed seconds."""
    from playwright.async_api import async_playwright

    SCREENSHOT_DIR.mkdir(exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        t0 = time.perf_counter()
        response = await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        await page.wait_for_timeout(SETTLE_MS)
        elapsed = time.perf_counter() - t0

        assert response is not None and response.status == 200, (
            f"Expected 200 for {url}, got {response.status if response else 'no response'}"
        )

        path = SCREENSHOT_DIR / f"{name}.png"
        await page.screenshot(path=str(path), full_page=full_page)

        body = await page.inner_text("body")
        await ctx.close()
        await browser.close()

    return elapsed, body


async def _click_and_screenshot(url: str, selector: str, name: str) -> tuple[float, str]:
    """Load page, click selector, wait for HTMX, screenshot. Returns (elapsed, body)."""
    from playwright.async_api import async_playwright

    SCREENSHOT_DIR.mkdir(exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        await page.wait_for_timeout(SETTLE_MS)

        el = await page.query_selector(selector)
        t0 = time.perf_counter()
        if el:
            await el.click()
            await page.wait_for_timeout(1500)  # HTMX swap settle
        elapsed = time.perf_counter() - t0

        path = SCREENSHOT_DIR / f"{name}.png"
        await page.screenshot(path=str(path), full_page=True)
        body = await page.inner_text("body")

        await ctx.close()
        await browser.close()

    return elapsed, body


def _no_errors(body: str):
    for marker in ("Internal Server Error", "500 Internal", "Traceback", "404 Not Found"):
        assert marker not in body, f"Error text on page: {marker!r}"


# ── Skip condition ─────────────────────────────────────────────────────────────

ui = pytest.mark.skipif(
    not (_server_up() and _playwright_available()),
    reason="UI tests require genesis-monitor server on :8000 and Playwright",
)

# ── Tests ──────────────────────────────────────────────────────────────────────

@ui
def test_home_page():
    """Home page lists projects and loads within threshold."""
    elapsed, body = asyncio.run(_screenshot(BASE_URL, "01_home_page"))
    print(f"\n  01_home_page: {elapsed:.2f}s")
    assert elapsed < MAX_LOAD_TIME_S, f"Too slow: {elapsed:.2f}s"
    _no_errors(body)
    # inner_text() returns visible text, not HTML — check for known project name
    assert "ai_sdlc_method" in body or "Monitored Projects" in body, (
        "Expected project names on home page"
    )


@ui
def test_project_page():
    """Project page renders with asset graph and feature list."""
    url = f"{BASE_URL}/project/ai-sdlc-method"
    elapsed, body = asyncio.run(_screenshot(url, "02_project_ai_sdlc"))
    print(f"\n  02_project_ai_sdlc: {elapsed:.2f}s")
    assert elapsed < MAX_LOAD_TIME_S, f"Too slow: {elapsed:.2f}s"
    _no_errors(body)
    # inner_text() returns rendered text — Mermaid renders as SVG nodes with labels
    assert any(label in body for label in ("Intent", "Requirements", "Design", "Asset Graph")), (
        "Expected asset graph node labels on project page"
    )


@ui
def test_feature_page_engine():
    """Feature page REQ-F-ENGINE-001 loads correctly."""
    url = f"{BASE_URL}/project/ai-sdlc-method/feature/REQ-F-ENGINE-001"
    elapsed, body = asyncio.run(_screenshot(url, "03_feature_engine"))
    print(f"\n  03_feature_engine: {elapsed:.2f}s")
    assert elapsed < MAX_LOAD_TIME_S, f"Too slow: {elapsed:.2f}s"
    _no_errors(body)
    assert "REQ-F-ENGINE-001" in body, "Feature ID should appear on page"


@ui
def test_feature_page_evol():
    """Feature page REQ-F-EVOL-001 loads correctly."""
    url = f"{BASE_URL}/project/ai-sdlc-method/feature/REQ-F-EVOL-001"
    elapsed, body = asyncio.run(_screenshot(url, "04_feature_evol"))
    print(f"\n  04_feature_evol: {elapsed:.2f}s")
    assert elapsed < MAX_LOAD_TIME_S, f"Too slow: {elapsed:.2f}s"
    _no_errors(body)
    assert "REQ-F-EVOL-001" in body


@ui
def test_feature_page_consensus():
    """Feature page REQ-F-CONSENSUS-001 loads correctly."""
    url = f"{BASE_URL}/project/ai-sdlc-method/feature/REQ-F-CONSENSUS-001"
    elapsed, body = asyncio.run(_screenshot(url, "05_feature_consensus"))
    print(f"\n  05_feature_consensus: {elapsed:.2f}s")
    assert elapsed < MAX_LOAD_TIME_S, f"Too slow: {elapsed:.2f}s"
    _no_errors(body)
    assert "REQ-F-CONSENSUS-001" in body


@ui
def test_feature_trajectory_fragment():
    """Feature trajectory HTMX fragment contains REQ keys."""
    url = f"{BASE_URL}/fragments/project/ai-sdlc-method/feature-trajectory"
    elapsed, body = asyncio.run(_screenshot(url, "06_fragment_feature_trajectory"))
    print(f"\n  06_feature_trajectory: {elapsed:.2f}s")
    assert elapsed < MAX_LOAD_TIME_S, f"Too slow: {elapsed:.2f}s"
    _no_errors(body)
    assert "REQ-F-" in body, "Expected feature IDs in trajectory fragment"


@ui
def test_adrs_fragment():
    """ADR register HTMX fragment renders the ADR table."""
    url = f"{BASE_URL}/fragments/project/ai-sdlc-method/adrs"
    elapsed, body = asyncio.run(_screenshot(url, "07_fragment_adrs"))
    print(f"\n  07_adrs: {elapsed:.2f}s")
    assert elapsed < MAX_LOAD_TIME_S, f"Too slow: {elapsed:.2f}s"
    _no_errors(body)


@ui
def test_backing_docs_lazy_load():
    """Backing docs lazy-load on click — content replaces placeholder."""
    url = f"{BASE_URL}/project/ai-sdlc-method/feature/REQ-F-ENGINE-001"
    elapsed, body = asyncio.run(
        _click_and_screenshot(url, "#backing-docs-section summary", "08_backing_docs_loaded")
    )
    print(f"\n  08_backing_docs: {elapsed:.2f}s after click")
    _no_errors(body)
    assert "Click to load" not in body or "No backing documents" in body, (
        "Backing docs should have loaded or shown 'No backing documents found'"
    )
    assert elapsed < MAX_LOAD_TIME_S + 1.0, f"Lazy load too slow: {elapsed:.2f}s"


@ui
def test_all_feature_pages_load():
    """Walk every feature link on the project page; all must return 200."""
    async def _collect_and_check():
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
            page = await ctx.new_page()

            resp = await page.goto(
                f"{BASE_URL}/project/ai-sdlc-method",
                wait_until="domcontentloaded",
                timeout=LOAD_TIMEOUT_MS,
            )
            assert resp and resp.status == 200

            hrefs = await page.eval_on_selector_all(
                "a[href*='/feature/']",
                "els => els.map(e => e.getAttribute('href'))",
            )
            feature_urls = list(dict.fromkeys(
                f"{BASE_URL}{h}" for h in hrefs if h and "/feature/" in h
            ))

            results = []
            for i, url in enumerate(feature_urls):
                fid = url.split("/feature/")[-1]
                t0 = time.perf_counter()
                r = await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
                await page.wait_for_timeout(SETTLE_MS)
                elapsed = time.perf_counter() - t0
                status = r.status if r else 0
                name = f"09_all_{i:02d}_{fid}"
                SCREENSHOT_DIR.mkdir(exist_ok=True)
                await page.screenshot(path=str(SCREENSHOT_DIR / f"{name}.png"), full_page=True)
                results.append((fid, status, elapsed))
                print(f"\n    {fid}: {status} {elapsed:.2f}s")

            await ctx.close()
            await browser.close()
        return results

    results = asyncio.run(_collect_and_check())
    assert len(results) > 0, "No feature pages found"

    errors = [(fid, s, t) for fid, s, t in results if s != 200]
    slow = [(fid, t) for fid, s, t in results if t > MAX_LOAD_TIME_S]

    if errors:
        pytest.fail("Feature pages returned non-200:\n" +
                    "\n".join(f"  {fid}: HTTP {s} ({t:.2f}s)" for fid, s, t in errors))
    if slow:
        print(f"\n  WARNING — slow pages (>{MAX_LOAD_TIME_S}s):")
        for fid, t in slow:
            print(f"    {fid}: {t:.2f}s")


# ── Standalone runner ──────────────────────────────────────────────────────────

async def _run_standalone():
    print("Genesis Monitor — Screenshot Capture")
    print(f"  Server : {BASE_URL}")
    print(f"  Output : {SCREENSHOT_DIR}\n")

    pages = [
        (BASE_URL, "01_home_page"),
        (f"{BASE_URL}/project/ai-sdlc-method", "02_project_ai_sdlc"),
        (f"{BASE_URL}/project/ai-sdlc-method/feature/REQ-F-ENGINE-001", "03_feature_engine"),
        (f"{BASE_URL}/project/ai-sdlc-method/feature/REQ-F-EVOL-001", "04_feature_evol"),
        (f"{BASE_URL}/project/ai-sdlc-method/feature/REQ-F-CONSENSUS-001", "05_feature_consensus"),
        (f"{BASE_URL}/fragments/project/ai-sdlc-method/feature-trajectory", "06_fragment_feature_trajectory"),
        (f"{BASE_URL}/fragments/project/ai-sdlc-method/adrs", "07_fragment_adrs"),
    ]

    for url, name in pages:
        elapsed, _ = await _screenshot(url, name)
        tag = "OK  " if elapsed < MAX_LOAD_TIME_S else "SLOW"
        print(f"  [{tag}] {name}: {elapsed:.2f}s")

    print(f"\n  {len(pages)} screenshots → {SCREENSHOT_DIR}")


if __name__ == "__main__":
    asyncio.run(_run_standalone())
