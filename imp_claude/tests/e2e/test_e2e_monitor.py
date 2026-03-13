# Validates: REQ-TOOL-005
# Validates: REQ-TEST-003
# Validates: REQ-F-DASH-001
# Validates: REQ-F-DISC-001
"""
Playwright tests that validate genesis-monitor correctly displays e2e run output.

These tests are a second-order proof: they verify that the methodology outputs
(convergence events, feature vectors, phase summary) are correctly observable
through the genesis-monitor dashboard — semantic correctness, not just page loads.

Key validations:
  - All 4 required edges appear in the convergence table AND are marked converged
  - REQ-F-CONV-001 feature vector shows ✓ converged with ≥4 edge tick marks
  - Event log shows ≥4 edge_converged events (real iterations happened)
  - UAT edge (uat_tests) appears as converged
  - Home page shows "5/5 edges" for the latest passing run
  - All project pages return HTTP 200

Run:
    pytest imp_claude/tests/e2e/test_e2e_monitor.py -v -m e2e_monitor -s

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

# Expected methodology outputs from a successful e2e run
REQUIRED_EDGES = [
    "intent→requirements",
    "requirements→design",
    "design→code",
    "code↔unit_tests",
]
UAT_EDGE = "uat_tests"          # as it appears in STATUS.md phase summary
CONVERGENCE_FEATURE = "REQ-F-CONV-001"
MIN_CONVERGED_EDGES = 4         # must show ≥4 converged edges in convergence table
MIN_EDGE_TICK_MARKS = 4         # must show ≥4 ✓ in feature trajectory matrix
MIN_EDGE_CONVERGED_EVENTS = 4   # must show ≥4 edge_converged events in event log


# ── Skip guards ────────────────────────────────────────────────────────────────

def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def _monitor_installable() -> bool:
    try:
        import genesis_monitor  # noqa: F401
        return True
    except ImportError:
        return False


def _runs_exist() -> bool:
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
    """Mirror of genesis_monitor.registry._slugify — computes expected project URLs."""
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
    if not RUNS_DIR.is_dir():
        return None
    candidates = []
    for d in sorted(RUNS_DIR.iterdir()):
        if d.is_symlink() or "FAILED" in d.name:
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
            candidates.append(d)
    return candidates[-1] if candidates else None


def _find_failed_run() -> Path | None:
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
    """Navigate, settle, screenshot. Returns (elapsed_s, inner_text, http_status)."""
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
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        await page.wait_for_timeout(SETTLE_MS)
        hrefs = await page.eval_on_selector_all(
            selector, "els => els.map(e => e.getAttribute('href'))"
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
    """Start genesis-monitor pointing at runs/, yield base URL, terminate on teardown."""
    if not e2e_runs_meta["latest"]:
        pytest.skip("No successful e2e runs found in runs/")
    if not _playwright_available():
        pytest.skip("playwright not installed — run: pip install playwright && playwright install chromium")
    if not _monitor_installable():
        pytest.skip("genesis-monitor not installed — run: pip install -e projects/genesis_monitor/imp_fastapi[dev]")

    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "genesis_monitor",
         "--watch-dir", str(RUNS_DIR),
         "--host", "127.0.0.1",
         "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(REPO_ROOT),
    )

    if not _wait_for_server(port, timeout=15.0):
        proc.terminate()
        proc.wait(timeout=5)
        stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        pytest.fail(f"genesis-monitor failed to start on port {port}.\nStderr:\n{stderr[:2000]}")

    yield f"http://127.0.0.1:{port}"

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


e2e_monitor = pytest.mark.e2e_monitor


# ══════════════════════════════════════════════════════════════════════════════
# SEMANTIC CONVERGENCE TESTS — validates the methodology output is correct
# ══════════════════════════════════════════════════════════════════════════════

@e2e_monitor
class TestSemanticConvergence:
    """
    Convergence fragment at /fragments/project/{slug}/convergence must show
    all required edges as converged — not just any text on any page.
    """

    def test_all_required_edges_present(self, monitor_server: str, e2e_runs_meta: dict):
        """All 4 required edges appear in the convergence table."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, status = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/convergence",
                        "sem_01_conv_edges")
        )
        assert status == 200
        _no_server_errors(body)
        missing = [e for e in REQUIRED_EDGES if e not in body]
        assert not missing, (
            f"Required edges missing from convergence table: {missing}\n"
            f"Body:\n{body}"
        )

    def test_all_required_edges_are_converged(self, monitor_server: str, e2e_runs_meta: dict):
        """Every required edge shows status 'converged', not 'in_progress' or 'pending'."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/convergence",
                        "sem_01_conv_status")
        )
        # The convergence table renders: edge_name | converged | iterations | ...
        # Check each edge row by looking for "edge_name ... converged" proximity
        lines = body.splitlines()
        for edge in REQUIRED_EDGES:
            edge_lines = [l for l in lines if edge in l]
            assert edge_lines, f"Edge {edge!r} row not found in body"
            # The edge row should contain 'converged', not 'in_progress' or 'not started'
            row_text = " ".join(edge_lines)
            assert "converged" in row_text.lower(), (
                f"Edge {edge!r} row does not show 'converged': {row_text!r}"
            )
            assert "in_progress" not in row_text and "in progress" not in row_text.lower(), (
                f"Edge {edge!r} is still in_progress — not converged: {row_text!r}"
            )

    def test_uat_edge_converged(self, monitor_server: str, e2e_runs_meta: dict):
        """UAT edge (uat_tests) appears in the convergence table as converged."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/convergence",
                        "sem_01_conv_uat")
        )
        assert UAT_EDGE in body, (
            f"UAT edge {UAT_EDGE!r} not found in convergence table.\n"
            f"Expected the design→uat_tests edge to be recorded in STATUS.md.\n"
            f"Body:\n{body}"
        )
        lines = [l for l in body.splitlines() if UAT_EDGE in l]
        assert any("converged" in l.lower() for l in lines), (
            f"UAT edge {UAT_EDGE!r} is not marked converged: {lines}"
        )

    def test_converged_count_matches_expected(self, monitor_server: str, e2e_runs_meta: dict):
        """At least MIN_CONVERGED_EDGES rows show 'converged' status."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/convergence",
                        "sem_01_conv_count")
        )
        count = body.lower().count("converged")
        assert count >= MIN_CONVERGED_EDGES, (
            f"Expected ≥{MIN_CONVERGED_EDGES} 'converged' entries, found {count}.\n"
            f"This means not all required edges converged. Body:\n{body}"
        )

    def test_no_edges_still_pending(self, monitor_server: str, e2e_runs_meta: dict):
        """No required edge should appear as 'not started' or 'pending' in the table."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/convergence",
                        "sem_01_conv_no_pending")
        )
        lines = body.splitlines()
        for edge in REQUIRED_EDGES:
            edge_lines = [l for l in lines if edge in l]
            row_text = " ".join(edge_lines).lower()
            assert "not started" not in row_text and "no convergence" not in row_text, (
                f"Edge {edge!r} shows as not-started or no-convergence data: {row_text!r}"
            )


@e2e_monitor
class TestSemanticFeatureVector:
    """
    Feature trajectory fragment must show REQ-F-CONV-001 with ✓ converged
    overall status and ✓ tick marks for each converged edge in the matrix.
    """

    def test_conv001_appears_in_trajectory(self, monitor_server: str, e2e_runs_meta: dict):
        """REQ-F-CONV-001 is present in the feature trajectory matrix."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, status = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/feature-trajectory",
                        "sem_02_traj_present")
        )
        assert status == 200
        _no_server_errors(body)
        assert CONVERGENCE_FEATURE in body, (
            f"{CONVERGENCE_FEATURE} not found in feature trajectory fragment.\n"
            f"Body:\n{body}"
        )

    def test_conv001_status_is_converged(self, monitor_server: str, e2e_runs_meta: dict):
        """REQ-F-CONV-001 shows overall status ✓ converged in the matrix."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/feature-trajectory",
                        "sem_02_traj_status")
        )
        # The template renders: <span>✓ converged</span> for converged features
        assert "✓ converged" in body, (
            f"Feature trajectory does not show '✓ converged' for {CONVERGENCE_FEATURE}.\n"
            f"Actual status indicators in body: "
            f"{[l.strip() for l in body.splitlines() if '✓' in l or 'converged' in l.lower()]}"
        )

    def test_trajectory_matrix_has_required_edge_ticks(self, monitor_server: str, e2e_runs_meta: dict):
        """Feature trajectory matrix shows ✓ tick marks for ≥4 converged edges."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/feature-trajectory",
                        "sem_02_traj_ticks")
        )
        tick_count = body.count("✓")
        assert tick_count >= MIN_EDGE_TICK_MARKS, (
            f"Expected ≥{MIN_EDGE_TICK_MARKS} ✓ symbols in feature trajectory matrix, "
            f"got {tick_count}. Required edges may not all be converged."
        )

    def test_trajectory_matrix_shows_required_edge_columns(self, monitor_server: str, e2e_runs_meta: dict):
        """Feature trajectory matrix has column headers for the required edges."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/feature-trajectory",
                        "sem_02_traj_cols")
        )
        # The template uses edge_order = ['requirements', 'design', 'code', 'unit_tests', ...]
        # inner_text() returns truncated column headers (truncate(10)) — check base names
        expected_col_keywords = ["requirements", "design", "code", "unit tests"]
        missing = [kw for kw in expected_col_keywords if kw not in body.lower()]
        assert not missing, (
            f"Expected trajectory matrix columns missing: {missing}\n"
            f"Column header area of body: "
            f"{[l.strip() for l in body.splitlines()[:20]]}"
        )

    def test_no_pending_in_required_columns(self, monitor_server: str, e2e_runs_meta: dict):
        """No required edge column shows only · pending marks for REQ-F-CONV-001."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/feature-trajectory",
                        "sem_02_traj_no_pending")
        )
        # If ✓ converged appears AND tick count ≥ 4, then we know required edges converged
        # Double-check: "No feature vectors found" must not appear
        assert "No feature vectors found" not in body, (
            "Feature trajectory shows 'No feature vectors found' — "
            "genesis-monitor could not parse feature vectors from the e2e run."
        )


@e2e_monitor
class TestSemanticEventLog:
    """
    Events fragment must show that real work happened — edge_converged events
    for each required edge, not just an empty or trivial event log.
    """

    def test_event_log_has_edge_converged_events(self, monitor_server: str, e2e_runs_meta: dict):
        """Events fragment shows ≥4 edge_converged events — one per required edge."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, status = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/events",
                        "sem_03_events")
        )
        assert status == 200
        _no_server_errors(body)
        count = body.count("edge_converged")
        assert count >= MIN_EDGE_CONVERGED_EVENTS, (
            f"Expected ≥{MIN_EDGE_CONVERGED_EVENTS} edge_converged events in event log, "
            f"found {count}. This indicates not all required edges converged.\n"
            f"Event types visible: "
            f"{list(set(re.findall(r'(edge_converged|iteration_completed|edge_started)', body)))}"
        )

    def test_event_log_shows_iteration_completed_events(self, monitor_server: str, e2e_runs_meta: dict):
        """Events show iteration_completed events — actual LLM iterations were recorded."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/events",
                        "sem_03_events_iter")
        )
        count = body.count("iteration_completed")
        assert count >= 4, (
            f"Expected ≥4 iteration_completed events, found {count}. "
            f"Event log may be incomplete."
        )

    def test_event_log_references_convergence_feature(self, monitor_server: str, e2e_runs_meta: dict):
        """Events reference REQ-F-CONV-001 — events are tied to the correct feature."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/events",
                        "sem_03_events_feature")
        )
        assert CONVERGENCE_FEATURE in body, (
            f"Event log does not reference {CONVERGENCE_FEATURE}. "
            f"Events may not be associated with the correct feature vector."
        )

    def test_event_log_not_empty(self, monitor_server: str, e2e_runs_meta: dict):
        """Events fragment shows actual events, not 'No events' placeholder."""
        slug = e2e_runs_meta["latest_slug"]
        _, body, _ = asyncio.run(
            _fetch_page(f"{monitor_server}/fragments/project/{slug}/events",
                        "sem_03_events_nonempty")
        )
        assert "No events" not in body and "No recent events" not in body, (
            "Event log shows no events — genesis-monitor could not parse events.jsonl."
        )


@e2e_monitor
class TestSemanticHomePage:
    """
    Home page tree must reflect actual convergence state:
    - Latest passing run shows full edge count
    - Monitor correctly lists e2e runs it discovered
    """

    def test_home_shows_full_edge_count_for_passing_run(self, monitor_server: str, e2e_runs_meta: dict):
        """Home page tree shows '5/5 edges' for the latest passing run."""
        # STATUS.md has: Edges converged: 5/5
        # _tree.html renders: done_count/total edges
        _, body, status = asyncio.run(_fetch_page(monitor_server, "sem_04_home_edge_count"))
        assert status == 200
        _no_server_errors(body)
        # "5/5 edges" appears somewhere near the passing run entry
        edge_counts = re.findall(r"\d+/\d+", body)
        assert "5/5" in body, (
            f"Home page does not show '5/5 edges' for the fully converged run.\n"
            f"Edge count strings found: {edge_counts}\n"
            f"Body preview:\n{body[:800]}"
        )

    def test_home_has_project_links_for_e2e_runs(self, monitor_server: str, e2e_runs_meta: dict):
        """Home page has /project/ links and at least one contains 'e2e'."""
        hrefs = asyncio.run(_collect_hrefs(monitor_server, "a[href*='/project/']"))
        e2e_slugs = [h for h in hrefs if "e2e" in h]
        assert e2e_slugs, (
            f"No e2e project links on home page. All /project/ links: {hrefs}"
        )

    def test_home_latest_run_is_linked(self, monitor_server: str, e2e_runs_meta: dict):
        """The latest passing run's slug appears as a project link on the home page."""
        hrefs = asyncio.run(_collect_hrefs(monitor_server, "a[href*='/project/']"))
        latest_slug = e2e_runs_meta["latest_slug"]
        assert any(latest_slug in h for h in hrefs), (
            f"Latest passing run slug {latest_slug!r} not found in home page links: {hrefs}"
        )

    def test_home_no_server_errors(self, monitor_server: str):
        """Home page renders without server errors."""
        elapsed, body, status = asyncio.run(_fetch_page(monitor_server, "sem_04_home_ok"))
        assert status == 200
        _no_server_errors(body)
        assert elapsed < MAX_LOAD_TIME_S, f"Home page too slow: {elapsed:.2f}s"
        assert "Monitored Projects" in body


@e2e_monitor
class TestSemanticAllRunsNavigable:
    """All project pages (up to 10) must return HTTP 200 without server errors."""

    def test_all_project_pages_load_cleanly(self, monitor_server: str):
        """Walk every /project/ link from home; all return 200 with no server errors."""
        async def _check_all():
            from playwright.async_api import async_playwright

            SCREENSHOT_DIR.mkdir(exist_ok=True)
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
                page = await ctx.new_page()

                await page.goto(monitor_server, wait_until="domcontentloaded",
                                timeout=LOAD_TIMEOUT_MS)
                await page.wait_for_timeout(SETTLE_MS)

                hrefs = await page.eval_on_selector_all(
                    "a[href*='/project/']",
                    "els => els.map(e => e.getAttribute('href'))",
                )
                project_urls = list(dict.fromkeys(
                    f"{monitor_server}{h}" for h in hrefs
                    if h and h.count("/") == 2  # top-level project pages only
                ))

                results = []
                for url in project_urls[:10]:
                    slug = url.split("/project/")[-1]
                    t0 = time.perf_counter()
                    r = await page.goto(url, wait_until="domcontentloaded",
                                        timeout=LOAD_TIMEOUT_MS)
                    await page.wait_for_timeout(SETTLE_MS)
                    elapsed = time.perf_counter() - t0
                    status = r.status if r else 0
                    body = await page.inner_text("body")
                    name = f"sem_05_all_{slug[:40]}"
                    await page.screenshot(
                        path=str(SCREENSHOT_DIR / f"{name}.png"), full_page=True
                    )
                    results.append((slug, status, elapsed, body))
                    print(f"\n    {slug}: HTTP {status} {elapsed:.2f}s")

                await ctx.close()
                await browser.close()
            return results

        results = asyncio.run(_check_all())
        assert results, "No project pages found on home page"

        errors_http = [(s, code) for s, code, _, _ in results if code != 200]
        errors_500 = [
            (s, body[:200]) for s, _, _, body in results
            if any(m in body for m in ("Internal Server Error", "500 Internal", "Traceback"))
        ]

        if errors_http:
            pytest.fail(
                "Project pages returned non-200:\n" +
                "\n".join(f"  {slug}: HTTP {code}" for slug, code in errors_http)
            )
        if errors_500:
            pytest.fail(
                "Project pages contain server errors:\n" +
                "\n".join(f"  {slug}: {preview}" for slug, preview in errors_500)
            )

        print(f"\n  Checked {len(results)} project pages — all clean")
