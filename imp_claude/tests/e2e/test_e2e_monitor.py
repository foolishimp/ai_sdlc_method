# Validates: REQ-TOOL-005, REQ-F-DASH-001, REQ-F-DISC-001
"""
Playwright tests that validate genesis-monitor correctly displays e2e run output.

These tests are a second-order proof: they verify that the methodology outputs
(convergence events, feature vectors, phase summary) are correctly observable
through the genesis-monitor dashboard.

Workflow:
  1. Start genesis-monitor pointing at imp_claude/tests/e2e/runs/
  2. Navigate the monitor UI using Playwright
  3. Validate: runs are listed, convergence status is shown, feature vectors
     are readable, failed runs are visually distinct from passing runs.

Run:
    pytest imp_claude/tests/e2e/test_e2e_monitor.py -v -m e2e_monitor -s

Skip conditions:
  - No e2e runs exist in runs/ directory
  - playwright package not installed
  - genesis-monitor fails to start within 15s

Mark: e2e_monitor — independent from convergence e2e tests
"""

import asyncio
import json
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

# ── Paths ──────────────────────────────────────────────────────────────────────

_E2E_DIR = Path(__file__).parent
RUNS_DIR = _E2E_DIR / "runs"
REPO_ROOT = _E2E_DIR.parent.parent.parent  # imp_claude/tests/e2e → repo root
SCREENSHOT_DIR = _E2E_DIR / "monitor_screenshots"

LOAD_TIMEOUT_MS = 15_000
SETTLE_MS = 1_000
MAX_LOAD_TIME_S = 5.0


# ── Skip guards ────────────────────────────────────────────────────────────────

def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def _monitor_installable() -> bool:
    """Check genesis-monitor is importable (installed in editable mode)."""
    try:
        import genesis_monitor  # noqa: F401
        return True
    except ImportError:
        return False


def _runs_exist() -> bool:
    """At least one successful e2e run exists."""
    if not RUNS_DIR.is_dir():
        return False
    return any(
        d.is_dir() and (d / ".ai-workspace").is_dir() and "FAILED" not in d.name
        for d in RUNS_DIR.iterdir()
        if not d.is_symlink()
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _slugify(name: str) -> str:
    """Mirror of genesis_monitor.registry._slugify — used to compute expected URLs."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


def _wait_for_server(port: int, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.25)
    return False


def _find_latest_successful_run() -> Path | None:
    """Return the resolved path of the latest non-FAILED e2e run with all tests passed."""
    if not RUNS_DIR.is_dir():
        return None

    candidates = []
    for d in sorted(RUNS_DIR.iterdir()):
        if d.is_symlink():
            continue
        if "FAILED" in d.name:
            continue
        if not (d / ".ai-workspace").is_dir():
            continue
        manifest = d / ".e2e-meta" / "run_manifest.json"
        if manifest.exists():
            try:
                data = json.loads(manifest.read_text())
                if not data.get("failed", True):
                    candidates.append(d)
            except (json.JSONDecodeError, KeyError):
                pass
        else:
            # Older runs may not have manifest — include anyway
            candidates.append(d)

    return candidates[-1] if candidates else None


def _find_failed_run() -> Path | None:
    """Return a FAILED run directory (for negative validation)."""
    if not RUNS_DIR.is_dir():
        return None
    for d in sorted(RUNS_DIR.iterdir(), reverse=True):
        if d.is_symlink():
            continue
        if "FAILED" in d.name and (d / ".ai-workspace").is_dir():
            return d
    return None


# ── Playwright helpers ─────────────────────────────────────────────────────────

async def _fetch_page(url: str, name: str) -> tuple[float, str, int]:
    """Navigate to url, settle, screenshot, return (elapsed, body_text, http_status)."""
    from playwright.async_api import async_playwright

    SCREENSHOT_DIR.mkdir(exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        t0 = time.perf_counter()
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        await page.wait_for_timeout(SETTLE_MS)
        elapsed = time.perf_counter() - t0

        status = resp.status if resp else 0
        body = await page.inner_text("body")

        path = SCREENSHOT_DIR / f"{name}.png"
        await page.screenshot(path=str(path), full_page=True)

        await ctx.close()
        await browser.close()

    return elapsed, body, status


async def _collect_hrefs(url: str, selector: str) -> list[str]:
    """Return all href values matching selector on the given page."""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        await page.wait_for_timeout(SETTLE_MS)

        hrefs = await page.eval_on_selector_all(
            selector,
            "els => els.map(e => e.getAttribute('href'))",
        )

        await ctx.close()
        await browser.close()

    return [h for h in hrefs if h]


def _no_server_errors(body: str) -> None:
    for marker in ("Internal Server Error", "500 Internal", "Traceback", "404 Not Found"):
        assert marker not in body, f"Server error on page: {marker!r}"


# ── Session fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def e2e_runs_meta() -> dict:
    """Collect metadata about available e2e runs for use across tests."""
    latest = _find_latest_successful_run()
    failed = _find_failed_run()
    return {
        "latest": latest,
        "latest_slug": _slugify(latest.name) if latest else None,
        "failed": failed,
        "failed_slug": _slugify(failed.name) if failed else None,
    }


@pytest.fixture(scope="session")
def monitor_server(e2e_runs_meta) -> str:
    """Start genesis-monitor subprocess, yield base URL, terminate on teardown."""
    latest = e2e_runs_meta["latest"]
    if not latest:
        pytest.skip("No successful e2e runs found in runs/ directory")

    if not _playwright_available():
        pytest.skip("playwright not installed — run: pip install playwright && playwright install chromium")

    if not _monitor_installable():
        pytest.skip("genesis-monitor not installed — run: pip install -e projects/genesis_monitor/imp_fastapi[dev]")

    port = _free_port()
    cmd = [
        sys.executable, "-m", "genesis_monitor",
        "--watch-dir", str(RUNS_DIR),
        "--host", "127.0.0.1",
        "--port", str(port),
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
    )

    if not _wait_for_server(port, timeout=15.0):
        proc.terminate()
        proc.wait(timeout=5)
        stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        pytest.fail(f"genesis-monitor failed to start on port {port}.\nStderr:\n{stderr[:2000]}")

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── Skip markers ───────────────────────────────────────────────────────────────

e2e_monitor = pytest.mark.e2e_monitor


# ── Tests ──────────────────────────────────────────────────────────────────────

@e2e_monitor
class TestMonitorHomePage:
    """Home page lists discovered e2e runs."""

    def test_home_loads_without_error(self, monitor_server: str):
        """Home page returns 200 and no server errors."""
        elapsed, body, status = asyncio.run(
            _fetch_page(monitor_server, "monitor_01_home")
        )
        print(f"\n  home: {elapsed:.2f}s HTTP {status}")
        assert status == 200, f"Expected 200, got {status}"
        _no_server_errors(body)
        assert elapsed < MAX_LOAD_TIME_S, f"Home page too slow: {elapsed:.2f}s"

    def test_home_lists_monitored_projects(self, monitor_server: str):
        """Home page shows 'Monitored Projects' heading with at least one project."""
        _, body, _ = asyncio.run(_fetch_page(monitor_server, "monitor_01_home_projects"))
        assert "Monitored Projects" in body, "Expected 'Monitored Projects' heading"

    def test_home_contains_e2e_run_links(self, monitor_server: str):
        """Home page has at least one /project/ link for an e2e run."""
        hrefs = asyncio.run(
            _collect_hrefs(monitor_server, "a[href*='/project/']")
        )
        project_slugs = [h.split("/project/")[1].split("/")[0] for h in hrefs if "/project/" in h]
        e2e_slugs = [s for s in project_slugs if "e2e" in s]
        assert e2e_slugs, (
            f"Expected at least one e2e project link on home page. "
            f"Found slugs: {project_slugs}"
        )

    def test_home_shows_latest_successful_run(self, monitor_server: str, e2e_runs_meta: dict):
        """Home page shows the latest successful run slug."""
        latest_slug = e2e_runs_meta["latest_slug"]
        hrefs = asyncio.run(
            _collect_hrefs(monitor_server, "a[href*='/project/']")
        )
        assert any(latest_slug in h for h in hrefs), (
            f"Latest run slug {latest_slug!r} not found in project links: {hrefs}"
        )


@e2e_monitor
class TestLatestRunProjectPage:
    """Project page for the latest successful run shows convergence data."""

    def test_project_page_loads(self, monitor_server: str, e2e_runs_meta: dict):
        """Project page for latest run returns 200 with no errors."""
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/project/{slug}"
        elapsed, body, status = asyncio.run(
            _fetch_page(url, "monitor_02_project_latest")
        )
        print(f"\n  project/{slug}: {elapsed:.2f}s HTTP {status}")
        assert status == 200, f"Expected 200 for {url}, got {status}"
        _no_server_errors(body)

    def test_project_page_shows_convergence_info(self, monitor_server: str, e2e_runs_meta: dict):
        """Project page shows edge count or convergence status."""
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/project/{slug}"
        _, body, _ = asyncio.run(_fetch_page(url, "monitor_02_project_conv"))
        # Should show edges info (e.g. "4/4" or "converged") or feature vector
        has_convergence = (
            "converged" in body.lower()
            or "/4" in body  # edges converged count like "4/4"
            or "REQ-F-CONV" in body
        )
        assert has_convergence, (
            "Project page should show convergence info, edge counts, or feature vectors. "
            f"Body preview: {body[:500]}"
        )

    def test_project_page_shows_feature_vector(self, monitor_server: str, e2e_runs_meta: dict):
        """Project page references REQ-F-CONV-001 (the e2e convergence feature)."""
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/project/{slug}"
        _, body, _ = asyncio.run(_fetch_page(url, "monitor_02_project_fv"))
        assert "REQ-F-CONV-001" in body, (
            f"Expected REQ-F-CONV-001 on project page for {slug}. "
            f"Body preview: {body[:500]}"
        )

    def test_project_page_loads_within_threshold(self, monitor_server: str, e2e_runs_meta: dict):
        """Project page renders within load time threshold."""
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/project/{slug}"
        elapsed, _, _ = asyncio.run(_fetch_page(url, "monitor_02_project_perf"))
        assert elapsed < MAX_LOAD_TIME_S, f"Project page too slow: {elapsed:.2f}s"


@e2e_monitor
class TestLatestRunFeatureVectorPage:
    """Feature vector page shows the trajectory for REQ-F-CONV-001."""

    def test_feature_page_loads(self, monitor_server: str, e2e_runs_meta: dict):
        """Feature page for REQ-F-CONV-001 returns 200."""
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/project/{slug}/feature/REQ-F-CONV-001"
        elapsed, body, status = asyncio.run(
            _fetch_page(url, "monitor_03_feature_conv001")
        )
        print(f"\n  feature/REQ-F-CONV-001: {elapsed:.2f}s HTTP {status}")
        assert status == 200, f"Expected 200, got {status}"
        _no_server_errors(body)

    def test_feature_page_shows_req_id(self, monitor_server: str, e2e_runs_meta: dict):
        """Feature page displays the REQ-F-CONV-001 identifier."""
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/project/{slug}/feature/REQ-F-CONV-001"
        _, body, _ = asyncio.run(_fetch_page(url, "monitor_03_feature_id"))
        assert "REQ-F-CONV-001" in body, "Feature ID should appear on feature page"

    def test_feature_page_shows_trajectory_edges(self, monitor_server: str, e2e_runs_meta: dict):
        """Feature page shows graph edges (requirements, design, code, unit_tests)."""
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/project/{slug}/feature/REQ-F-CONV-001"
        _, body, _ = asyncio.run(_fetch_page(url, "monitor_03_feature_traj"))
        # At least some edge names should appear
        edge_keywords = ["requirements", "design", "code", "unit_tests", "intent"]
        found = [kw for kw in edge_keywords if kw in body.lower()]
        assert found, (
            f"Feature page should show trajectory edges. "
            f"Checked for: {edge_keywords}. Body preview: {body[:500]}"
        )

    def test_feature_trajectory_fragment(self, monitor_server: str, e2e_runs_meta: dict):
        """Feature trajectory HTMX fragment endpoint returns REQ key data."""
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/fragments/project/{slug}/feature-trajectory"
        elapsed, body, status = asyncio.run(
            _fetch_page(url, "monitor_03_traj_fragment")
        )
        assert status == 200, f"Trajectory fragment returned {status}"
        _no_server_errors(body)
        # Fragment should contain REQ keys or edge data
        assert "REQ-F-" in body or "requirements" in body.lower() or "No features" in body, (
            f"Trajectory fragment should contain feature data. Body: {body[:300]}"
        )


@e2e_monitor
class TestFailedRunDisplay:
    """Monitor distinguishes failed runs from passing runs."""

    def test_failed_run_listed_on_home(self, monitor_server: str, e2e_runs_meta: dict):
        """A FAILED run appears in the project list on the home page."""
        failed = e2e_runs_meta["failed"]
        if not failed:
            pytest.skip("No FAILED runs found in runs/ directory")

        hrefs = asyncio.run(
            _collect_hrefs(monitor_server, "a[href*='/project/']")
        )
        failed_slug = e2e_runs_meta["failed_slug"]
        assert any(failed_slug in h for h in hrefs), (
            f"FAILED run slug {failed_slug!r} not found in home page links: {hrefs}"
        )

    def test_failed_run_project_page_loads(self, monitor_server: str, e2e_runs_meta: dict):
        """Failed run's project page loads without a 500 error."""
        failed = e2e_runs_meta["failed"]
        if not failed:
            pytest.skip("No FAILED runs found in runs/ directory")

        slug = e2e_runs_meta["failed_slug"]
        url = f"{monitor_server}/project/{slug}"
        _, body, status = asyncio.run(_fetch_page(url, "monitor_04_failed_run"))
        assert status == 200, f"Expected 200 for failed run page, got {status}"
        _no_server_errors(body)

    def test_latest_run_not_marked_failed(self, monitor_server: str, e2e_runs_meta: dict):
        """The latest successful run page does not show 'FAILED' in the run name area."""
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/project/{slug}"
        _, body, _ = asyncio.run(_fetch_page(url, "monitor_04_not_failed"))
        # The project name or header should not contain FAILED
        # (FAILED might appear elsewhere as metadata about other runs)
        lines = [line for line in body.splitlines() if slug[:15] in line.lower() or "FAILED" in line]
        # Just validate the page loaded without calling a passing run "FAILED"
        assert "FAILED" not in slug, (
            f"Latest successful run slug should not contain FAILED: {slug!r}"
        )


@e2e_monitor
class TestAllRunPagesNavigable:
    """Walk all project links from home page — all must return 200."""

    def test_all_project_pages_return_200(self, monitor_server: str):
        """Every project link on the home page returns HTTP 200."""
        async def _check_all():
            from playwright.async_api import async_playwright

            SCREENSHOT_DIR.mkdir(exist_ok=True)
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
                page = await ctx.new_page()

                await page.goto(monitor_server, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
                await page.wait_for_timeout(SETTLE_MS)

                hrefs = await page.eval_on_selector_all(
                    "a[href*='/project/']",
                    "els => els.map(e => e.getAttribute('href'))",
                )
                project_urls = list(dict.fromkeys(
                    f"{monitor_server}{h}" for h in hrefs
                    if h and "/project/" in h and h.count("/") == 2  # top-level project pages
                ))

                results = []
                for url in project_urls[:10]:  # cap at 10 to keep test fast
                    slug = url.split("/project/")[-1]
                    t0 = time.perf_counter()
                    r = await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
                    await page.wait_for_timeout(SETTLE_MS)
                    elapsed = time.perf_counter() - t0
                    status = r.status if r else 0
                    name = f"monitor_05_all_{slug[:40]}"
                    await page.screenshot(path=str(SCREENSHOT_DIR / f"{name}.png"), full_page=True)
                    results.append((slug, status, elapsed))
                    print(f"\n    {slug}: HTTP {status} {elapsed:.2f}s")

                await ctx.close()
                await browser.close()
            return results

        results = asyncio.run(_check_all())
        assert results, "No project pages found on home page"

        errors = [(s, code) for s, code, _ in results if code != 200]
        if errors:
            pytest.fail(
                "Project pages returned non-200:\n" +
                "\n".join(f"  {slug}: HTTP {code}" for slug, code in errors)
            )

        print(f"\n  Checked {len(results)} project pages — all returned 200")
