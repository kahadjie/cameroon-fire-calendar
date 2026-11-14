"""MODIS / VIIRS harmonization of NASA FIRMS fire hotspots for Cameroon (NASA Space Apps 2026).

Main series: S-NPP (VIIRS, 2012 to 2026). MODIS is converted to an "S-NPP equivalent" with an overlap
ratio computed FOR EACH YEAR (never a single constant). NOAA-20 and NOAA-21 are used only as a
cross-check (sensors are never added together: they often detect the same fire).

Usage: python harmonize.py  (reads data/, writes aggregats.json, grille.json and donnees.js)
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# Common confidence levels: MODIS 0-100 -> l / n / h (FIRMS thresholds: < 30, 30-79, >= 80).
MODIS_LOW_MAX = 30
MODIS_HIGH_MIN = 80
LEVELS = {"l": 0, "n": 1, "h": 2}
MIN_LEVEL = "n"  # "nominal and high", as for the calibration ratios

# Facts checked on the files (see inspect_archives.py).
MODIS_GAP = (date(2026, 8, 30), date(2026, 9, 8))
PROVISIONAL_LAST_MONTHS = 5
GRID_DEG = 0.5

COLUMNS = ["latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence", "type"]


def load_firms(path: Path, source: str) -> pd.DataFrame:
    """Reads a FIRMS CSV. acq_time stays text (HHMM with leading zeros)."""
    head = pd.read_csv(path, nrows=0).columns
    use = [c for c in COLUMNS if c in head]
    df = pd.read_csv(path, usecols=use, dtype={"acq_time": str, "satellite": str, "confidence": str})
    df["acq_time"] = df["acq_time"].str.zfill(4)
    df["acq_date"] = pd.to_datetime(df["acq_date"], format="%Y-%m-%d")
    df["source"] = source  # "archive" or "nrt"
    if "type" not in df.columns:
        df["type"] = pd.NA  # missing from NRT files
    return df


def normalize_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """Adds conf_level (0 low, 1 nominal, 2 high), same scale for MODIS (number) and VIIRS (l/n/h)."""
    out = df.copy()
    text = out["confidence"].astype(str).str.strip().str.lower()
    numeric = pd.to_numeric(text, errors="coerce")
    level = text.map(LEVELS)
    modis = numeric.notna()
    level[modis] = 0
    level[modis & (numeric >= MODIS_LOW_MAX)] = 1
    level[modis & (numeric >= MODIS_HIGH_MIN)] = 2
    out["conf_level"] = level.astype("Int64")
    return out


def filter_detections(df: pd.DataFrame, min_level: str = MIN_LEVEL) -> pd.DataFrame:
    """Keeps confidence >= min_level; in the archive, only type 0 (presumed vegetation fire)."""
    keep = df["conf_level"] >= LEVELS[min_level]
    has_type = df["type"].notna()
    keep &= ~has_type | (pd.to_numeric(df["type"], errors="coerce") == 0)
    return df[keep.fillna(False)]


def monthly_counts(df: pd.DataFrame) -> pd.Series:
    """Number of detections per (year, month)."""
    if df.empty:
        return pd.Series(dtype="int64")
    key = [df["acq_date"].dt.year.rename("year"), df["acq_date"].dt.month.rename("month")]
    return df.groupby(key).size()


def yearly_ratio(viirs: pd.Series, modis: pd.Series, usable: set[tuple[int, int]]) -> dict[int, dict]:
    """VIIRS / MODIS ratio per year, over months complete for both sensors only."""
    out: dict[int, dict] = {}
    both = [k for k in viirs.index if k in modis.index and k in usable]
    for year in sorted({y for y, _ in both}):
        months = [k for k in both if k[0] == year]
        v = int(sum(viirs[k] for k in months))
        m = int(sum(modis[k] for k in months))
        if m > 0:
            out[year] = {"ratio": round(v / m, 3), "months_used": len(months)}
    return out


def ratio_for(year: int, ratios: dict[int, dict]) -> tuple[float | None, int | None]:
    """The year's ratio, otherwise the nearest known year's (reported through its source year)."""
    if not ratios:
        return None, None
    if year in ratios:
        return ratios[year]["ratio"], year
    nearest = min(ratios, key=lambda y: (abs(y - year), -y))
    return ratios[nearest]["ratio"], nearest


def month_medians(counts: dict[tuple[int, int], int], reference: set[tuple[int, int]]) -> dict[int, float]:
    """Historical median of each calendar month, over reference months only."""
    out: dict[int, float] = {}
    for month in range(1, 13):
        values = [counts[k] for k in reference if k[1] == month and k in counts]
        if values:
            out[month] = float(pd.Series(values).median())
    return out


def anomaly_pct(value: float | None, median: float | None) -> float | None:
    """Difference from the median, in percent; None when the median is zero or unknown."""
    if value is None or median is None or median == 0:
        return None
    return round((value - median) / median * 100, 1)


def month_range(first: date, last: date) -> list[tuple[int, int]]:
    out, y, m = [], first.year, first.month
    while (y, m) <= (last.year, last.month):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def coverage_flags(key: tuple[int, int], cover: dict[str, tuple[date, date]]) -> dict[str, bool]:
    """Whether the month is complete for each sensor (start and end of coverage, MODIS gap)."""
    y, m = key
    start = date(y, m, 1)
    end = date(y + (m == 12), m % 12 + 1, 1)
    flags = {}
    for name, (first, last) in cover.items():
        flags[name] = first <= start and end <= last + pd.Timedelta(days=1).to_pytimedelta()
    gap_start, gap_end = MODIS_GAP
    if start <= gap_end and gap_start < end:
        flags["modis"] = False
    return flags


def load_sensor(folder: str) -> tuple[pd.DataFrame, tuple[date, date]]:
    frames = []
    for path in sorted((DATA / folder).glob("*.csv")):
        frames.append(load_firms(path, "nrt" if "_nrt_" in path.name else "archive"))
    df = normalize_confidence(pd.concat(frames, ignore_index=True))
    span = (df["acq_date"].min().date(), df["acq_date"].max().date())
    return df, span


def grid_counts(df: pd.DataFrame) -> dict[str, list]:
    """Counts per 0.5° cell and per month (main series), for the map. No individual detections."""
    cell_lat = (df["latitude"] // GRID_DEG * GRID_DEG).round(2)
    cell_lng = (df["longitude"] // GRID_DEG * GRID_DEG).round(2)
    g = df.groupby([df["acq_date"].dt.year, df["acq_date"].dt.month, cell_lat, cell_lng]).size()
    out: dict[str, list] = {}
    for (y, m, la, lo), n in g.items():
        out.setdefault(f"{y}-{m:02d}", []).append([float(la), float(lo), int(n)])
    return out


def build(data_dir: Path = DATA) -> tuple[dict, dict]:
    sensors = {"snpp": "snpp", "modis": "modis", "n20": "noaa20", "n21": "noaa21"}
    raw, cover, counts, nrt_months = {}, {}, {}, set()
    for name, folder in sensors.items():
        df, span = load_sensor(folder)
        raw[name] = df
        cover[name] = span
        kept = filter_detections(df)
        counts[name] = monthly_counts(kept)
        nrt = kept[kept["source"] == "nrt"]
        nrt_months |= set(zip(nrt["acq_date"].dt.year, nrt["acq_date"].dt.month))
    first = min(s[0] for s in cover.values())
    last = max(s[1] for s in cover.values())
    keys = month_range(first, last)
    provisional = set(keys[-PROVISIONAL_LAST_MONTHS:]) | nrt_months
    flags = {k: coverage_flags(k, cover) for k in keys}

    usable = {k for k in keys if flags[k]["snpp"] and flags[k]["modis"] and k not in provisional}
    ratios = yearly_ratio(counts["snpp"], counts["modis"], usable)
    main = {k: int(counts["snpp"].get(k, 0)) for k in keys if flags[k]["snpp"]}
    reference = {k for k in main if k not in provisional and k[0] <= keys[-1][0] - 1}
    medians = month_medians(main, reference)

    months = []
    for k in keys:
        y, m = k
        snpp = main.get(k)
        modis = int(counts["modis"].get(k, 0)) if flags[k]["modis"] else None
        ratio, ratio_year = ratio_for(y, ratios)
        months.append({
            "year": y, "month": m,
            "snpp": snpp,
            "modis": modis,
            "modis_equiv": round(modis * ratio) if modis is not None and ratio else None,
            "ratio": ratio, "ratio_year": ratio_year,
            "n20": int(counts["n20"].get(k, 0)) if flags[k]["n20"] else None,
            "n21": int(counts["n21"].get(k, 0)) if flags[k]["n21"] else None,
            "median": medians.get(m),
            "anomaly_pct": anomaly_pct(snpp, medians.get(m)),
            "provisional": k in provisional,
            "complete": {s: bool(v) for s, v in flags[k].items()},
        })

    verification = {}
    for other in ("n20", "n21"):
        pairs = [(main[k], int(counts[other][k])) for k in reference if k in counts[other].index and flags[k][other]]
        if len(pairs) >= 3:
            a, b = pd.Series([p[0] for p in pairs]), pd.Series([p[1] for p in pairs])
            verification[other] = {"months": len(pairs), "corr_with_snpp": round(float(a.corr(b)), 3), "ratio_to_snpp": round(float(b.sum() / a.sum()), 3)}

    archive = raw["snpp"][raw["snpp"]["source"] == "archive"]
    static_share = float((pd.to_numeric(archive["type"], errors="coerce") != 0).mean())
    meta = {
        "title": "Cameroon fire hotspots, MODIS and VIIRS harmonized",
        "source": "NASA FIRMS (Fire Information for Resource Management System), https://firms.modaps.eosdis.nasa.gov",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "main_series": "S-NPP (VIIRS 375 m), nominal and high confidence, archive type 0",
        "coverage": {k: [v[0].isoformat(), v[1].isoformat()] for k, v in cover.items()},
        "modis_gap": [MODIS_GAP[0].isoformat(), MODIS_GAP[1].isoformat()],
        "reference_months": len(reference),
        "reference_years": [min(k[0] for k in reference), max(k[0] for k in reference)],
        "provisional_rule": f"months with NRT data, and the last {PROVISIONAL_LAST_MONTHS} months",
        "snpp_archive_static_share": round(static_share, 4),
        "grid_deg": GRID_DEG,
    }
    calibration = [{"year": y, **v} for y, v in sorted(ratios.items())]
    agg = {"meta": meta, "calibration": calibration, "verification": verification, "months": months}
    grid = {"grid_deg": GRID_DEG, "series": "snpp", "cells": grid_counts(filter_detections(raw["snpp"]))}
    return agg, grid


def main() -> int:
    agg, grid = build()
    (ROOT / "aggregats.json").write_text(json.dumps(agg, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "grille.json").write_text(json.dumps(grid, separators=(",", ":")), encoding="utf-8")
    # Same content as a script, so index.html opens with a double-click (fetch() refuses file://).
    js = "window.FIRMS_AGG=" + json.dumps(agg, ensure_ascii=False, separators=(",", ":")) + ";\n"
    js += "window.FIRMS_GRID=" + json.dumps(grid, separators=(",", ":")) + ";\n"
    (ROOT / "donnees.js").write_text(js, encoding="utf-8")
    print(f"aggregats.json: {len(agg['months'])} months; grille.json: {len(grid['cells'])} months")
    for c in agg["calibration"]:
        print(f"  S-NPP/MODIS ratio {c['year']}: {c['ratio']} ({c['months_used']} months)")
    print("  cross-check:", agg["verification"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
