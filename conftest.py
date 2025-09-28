# conftest.py
import os
import re
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

REPORT_DIR = Path("reports")
SCREEN_DIR = REPORT_DIR / "screens"
TRACE_DIR = REPORT_DIR / "traces"
SCREEN_DIR.mkdir(parents=True, exist_ok=True)
TRACE_DIR.mkdir(parents=True, exist_ok=True)

def _safe_name(node_name: str) -> str:
    # make a filesystem-safe filename from the test name
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", node_name)

@pytest.fixture(scope="session")
def browser():
    """
    One Chromium instance for the whole test session (fast + CI friendly).
    Set SHOW_BROWSER=1 to run headed locally if you want to see it.
    """
    headed = os.getenv("SHOW_BROWSER") in ("1", "true", "yes")
    with sync_playwright() as p:
        b = p.chromium.launch(headless=not headed)
        yield b
        b.close()

@pytest.fixture
def page(browser, request):
    """
    New context/page per test (isolated storage, cookies, etc.).
    Starts Playwright tracing; on failure, saves a .zip trace.
    """
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    # capture screenshots + snapshots for useful traces
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    pg = context.new_page()
    yield pg

    # Teardown: stop tracing; if test failed, save trace
    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    if failed:
        trace_path = TRACE_DIR / f"{_safe_name(request.node.name)}_trace.zip"
        context.tracing.stop(path=str(trace_path))
    else:
        context.tracing.stop()  # discard
    context.close()

# ---- pytest-html integration: mark test outcome + embed screenshot on failure ----

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Make the test result (setup/call/teardown) available on the node as:
    item.rep_setup, item.rep_call, item.rep_teardown
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    """
    If a test fails during its 'call' phase, take a full-page screenshot.
    Also embed it into the pytest-html report (self-contained).
    """
    yield
    # Only take screenshot for assertion/runtime failures in the test body
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        filename = f"{_safe_name(request.node.name)}.png"
        path = SCREEN_DIR / filename
        page.screenshot(path=str(path), full_page=True)

        # If pytest-html is active, embed the image inline in the HTML report
        if request.config.pluginmanager.hasplugin("html"):
            try:
                from pytest_html import extras
                # Read and base64-embed the screenshot
                with open(path, "rb") as f:
                    image_bytes = f.read()
                extra = getattr(request.node.rep_call, "extra", [])
                extra.append(extras.image(image_bytes, mime_type="image/png", extension="png"))
                request.node.rep_call.extra = extra
            except Exception:
                # Don't fail the test run if embedding has any issue
                pass
