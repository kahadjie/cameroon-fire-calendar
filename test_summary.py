"""Runs tests/summary_test.html (the summary sentences of index.html) in a headless browser.
Skipped when no Edge or Chrome is installed. Run: python -m pytest"""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
CANDIDATES = [
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
    shutil.which("chromium") or "", shutil.which("google-chrome") or "",
]
BROWSER = next((c for c in CANDIDATES if c and Path(c).exists()), None)


@pytest.mark.skipif(BROWSER is None, reason="no headless browser available")
def test_summary_sentences_follow_the_data():
    page = (ROOT / "tests" / "summary_test.html").resolve().as_uri()
    out = subprocess.run([BROWSER, "--headless=new", "--disable-gpu", "--virtual-time-budget=5000", "--dump-dom", page],
                         capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
    result = re.search(r'<pre id="out">(.*?)</pre>', out, re.S)
    assert result, "test page did not run"
    assert result.group(1).strip() == "PASS", result.group(1)
