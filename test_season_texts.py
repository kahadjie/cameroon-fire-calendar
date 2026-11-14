"""Consistency of what the page shows with season.json, and sensitivity of the answer to the season window.
Run: python -m pytest"""

import copy
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import analysis

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "season.json").read_text(encoding="utf-8"))
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numeric_leaves(obj, skip=("text",)):
    """Every number stored in season.json, outside the texts themselves."""
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield float(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k not in skip:
                yield from numeric_leaves(v, skip)
    elif isinstance(obj, list):
        for v in obj:
            yield from numeric_leaves(v, skip)


def allowed_forms(values):
    forms = set()
    for v in values:
        for d in range(4):
            forms.add(f"{abs(v):.{d}f}")
        forms.add(str(int(abs(v))) if float(v).is_integer() else f"{abs(v)}")
    return forms


def all_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for v in obj:
            yield from all_strings(v)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from all_strings(v)


def test_every_number_shown_comes_from_season_json():
    forms = allowed_forms(numeric_leaves(DATA))
    text = {k: v for k, v in DATA["text"].items() if k not in ("generated", "snpp_end")}
    missing = []
    for s in all_strings(text):
        s = re.sub(r"\b\d{4}-\d{2}\b", "", s)  # season labels such as 2025-26
        for token in NUMBER.findall(s):
            if token.replace(",", "") not in forms:
                missing.append((token, s[:60]))
    assert not missing, missing


def test_texts_are_rebuilt_exactly_from_the_numbers():
    rebuilt = analysis.texts({k: v for k, v in DATA.items() if k != "text"})
    assert rebuilt == DATA["text"]


def test_answer_names_every_window_and_says_when_it_depends_on_it():
    answer = DATA["text"]["answer"]
    flags = {k: abs(w["seasons"][-1]["z_count"]) >= DATA["meta"]["z_threshold"] for k, w in DATA["windows"].items()}
    assert set(DATA["windows"]) == {"Oct-Apr", "Nov-Mar", "Dec-Feb"}
    if len(set(flags.values())) == 1:
        assert answer.startswith("Yes" if flags["Nov-Mar"] else "No")
        assert "October to April" in answer and "December to February" in answer
    # Make the windows disagree: the answer must stop being a plain Yes/No.
    changed = copy.deepcopy({k: v for k, v in DATA.items() if k != "text"})
    changed["windows"]["Dec-Feb"]["seasons"][-1]["z_count"] = -9.0
    a = analysis.texts(changed)["answer"]
    assert a.startswith("It depends on the months counted") and "December to February: flagged" in a


def test_frp_is_called_an_index_of_fire_intensity_never_energy():
    files = [ROOT / "index.html", ROOT / "docs" / "SEASON_CHECK.md", ROOT / "docs" / "DEMO_SEASON_CHECK.md", ROOT / "README.md", ROOT / "submission" / "DESCRIPTION.md"]
    for f in files + [ROOT / "season.json"]:
        assert "energy" not in f.read_text(encoding="utf-8").lower(), f.name
    assert "index of fire intensity" in DATA["text"]["frp"]


BROWSER = next((c for c in [os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
                            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
                            shutil.which("chromium") or "", shutil.which("google-chrome") or ""] if c and Path(c).exists()), None)


@pytest.mark.skipif(BROWSER is None, reason="no headless browser available")
def test_page_shows_exactly_the_texts_of_season_json():
    dom = subprocess.run([BROWSER, "--headless=new", "--disable-gpu", "--virtual-time-budget=5000", "--dump-dom", (ROOT / "index.html").as_uri()],
                         capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
    unescape = lambda s: s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
    for key in ("answer", "range", "frp"):
        shown = re.search(rf'id="{key}"[^>]*>(.*?)<', dom, re.S).group(1)
        assert unescape(shown) == DATA["text"][key], key
    cells = [unescape(c) for c in re.findall(r"<(?:td|th)[^>]*>([^<]*)</(?:td|th)>", re.search(r'id="windows".*?</table>', dom, re.S).group(0))]
    for row in DATA["text"]["windows"]:
        assert all(cell in cells for cell in row), row
