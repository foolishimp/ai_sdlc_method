import asyncio
import json
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
import pytest

_E2E_DIR = Path(__file__).parent
RUNS_DIR = _E2E_DIR / "runs"
REPO_ROOT = _E2E_DIR.parent.parent.parent
SCREENSHOT_DIR = _E2E_DIR / "monitor_screenshots"

LOAD_TIMEOUT_MS = 15_000
SETTLE_MS = 1_000

REQUIRED_EDGES = ["intent→requirements", "requirements→design", "design→code", "code↔unit_tests"]

def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def _slugify(name: str) -> str:
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
    if not RUNS_DIR.is_dir(): return None
    candidates = []
    for d in sorted(RUNS_DIR.iterdir()):
        if d.is_symlink() or "FAILED" in d.name: continue
        if (d / ".ai-workspace").is_dir(): candidates.append(d)
    return candidates[-1] if candidates else None

@pytest.fixture(scope="session")
def e2e_runs_meta() -> dict:
    latest = _find_latest_successful_run()
    return {"latest": latest, "latest_slug": _slugify(latest.name) if latest else None}

@pytest.fixture(scope="session")
def monitor_server(e2e_runs_meta) -> str:
    if not e2e_runs_meta["latest"]: pytest.skip("No successful e2e runs found")
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "genesis_monitor", "--watch-dir", str(RUNS_DIR), "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(REPO_ROOT)
    )
    if not _wait_for_server(port):
        proc.terminate()
        pytest.fail(f"Monitor failed to start on port {port}")
    yield f"http://127.0.0.1:{port}"
    proc.terminate()

async def _fetch_page(url: str, name: str) -> tuple[int, str]:
    from playwright.async_api import async_playwright
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=LOAD_TIMEOUT_MS)
        await page.wait_for_timeout(SETTLE_MS)
        body = await page.inner_text("body")
        await page.screenshot(path=str(SCREENSHOT_DIR / f"{name}.png"), full_page=True)
        await browser.close()
    return resp.status if resp else 0, body

@pytest.mark.e2e_monitor
class TestGeminiMonitorParity:
    def test_monitor_home_renders(self, monitor_server: str):
        status, body = asyncio.run(_fetch_page(monitor_server, "gemini_home"))
        assert status == 200
        assert "Monitored Projects" in body

    def test_latest_run_visible(self, monitor_server: str, e2e_runs_meta: dict):
        status, body = asyncio.run(_fetch_page(monitor_server, "gemini_home_list"))
        assert e2e_runs_meta["latest"].name in body

    def test_convergence_fragment_parity(self, monitor_server: str, e2e_runs_meta: dict):
        slug = e2e_runs_meta["latest_slug"]
        url = f"{monitor_server}/fragments/project/{slug}/convergence"
        status, body = asyncio.run(_fetch_page(url, "gemini_convergence"))
        assert status == 200
        for edge in REQUIRED_EDGES:
            assert edge in body
            assert "converged" in body.lower()
