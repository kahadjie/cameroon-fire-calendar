"""Held-out test of the MODIS → S-NPP rescaling: each full year (12 usable months) is left out in turn,
its S-NPP/MODIS factor is predicted from the other years, and the prediction is compared with the
factor actually measured on that year. Reported figure: mean absolute error in percent.

Three predictors are compared:
  constant    one factor for the whole period (what the challenge warns against);
  neighbours  mean of the two adjacent years;
  trend       linear trend over the other years.

Run: python validate.py
Needs aggregats.json only. If data/modis is present, the Aqua-only variant is also computed (Aqua
passes at the same time of day as Suomi NPP); otherwise it is skipped and said so.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def usable_months(months: list[dict]) -> dict[int, list[dict]]:
    """Months complete for both sensors and not provisional, grouped by year."""
    out: dict[int, list[dict]] = {}
    for m in months:
        if m["snpp"] is not None and m["modis"] is not None and not m["provisional"]:
            out.setdefault(m["year"], []).append(m)
    return out


def trend(points: list[tuple[int, float]], year: int) -> float:
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    return my + slope * (year - mx)


def neighbours(points: dict[int, float], year: int) -> float:
    near = [points[y] for y in (year - 1, year + 1) if y in points]
    if near:
        return sum(near) / len(near)
    closest = min(points, key=lambda y: abs(y - year))
    return points[closest]


def predictors(ratios: dict[int, float], sums: dict[int, tuple[float, float]], year: int) -> dict[str, float]:
    """Factor of `year` predicted WITHOUT that year. sums[y] = (S-NPP total, MODIS total)."""
    others = {y: r for y, r in ratios.items() if y != year}
    num = sum(sums[y][0] for y in others)
    den = sum(sums[y][1] for y in others)
    return {
        "constant": num / den,
        "neighbours": neighbours(others, year),
        "trend": trend(sorted(others.items()), year),
    }


def held_out_errors(ratios: dict[int, float], sums: dict[int, tuple[float, float]]) -> dict[str, dict]:
    """Mean and maximum absolute error (percent) of each predictor, over all held-out years."""
    errors: dict[str, list[float]] = {}
    for year in ratios:
        for method, predicted in predictors(ratios, sums, year).items():
            errors.setdefault(method, []).append(abs(predicted - ratios[year]) / ratios[year])
    return {m: {"mean_pct": round(100 * sum(e) / len(e), 2), "max_pct": round(100 * max(e), 2)} for m, e in errors.items()}


def all_modis_variant(agg: dict) -> tuple[dict[int, float], dict[int, tuple[float, float]]]:
    """Published factors (all MODIS) and the sums they come from, full years only."""
    by_year = usable_months(agg["months"])
    ratios = {c["year"]: c["ratio"] for c in agg["calibration"] if c["months_used"] == 12}
    sums = {y: (sum(m["snpp"] for m in by_year[y]), sum(m["modis"] for m in by_year[y])) for y in ratios}
    return ratios, sums


def aqua_variant(agg: dict, data_dir: Path) -> tuple[dict[int, float], dict[int, tuple[float, float]]] | None:
    """Same test with Aqua detections only; needs the raw MODIS files and pandas."""
    if not (data_dir / "modis").is_dir():
        return None
    import harmonize as h

    df, _ = h.load_sensor("modis") if data_dir == h.DATA else _load(h, data_dir / "modis")
    aqua = h.monthly_counts(h.filter_detections(df[df["satellite"] == "Aqua"]))
    by_year = usable_months(agg["months"])
    full = [c["year"] for c in agg["calibration"] if c["months_used"] == 12]
    sums, ratios = {}, {}
    for y in full:
        s = sum(m["snpp"] for m in by_year[y])
        a = sum(int(aqua.get((m["year"], m["month"]), 0)) for m in by_year[y])
        sums[y], ratios[y] = (s, a), round(s / a, 3)
    return ratios, sums


def _load(h, folder: Path):
    frames = [h.load_firms(p, "nrt" if "_nrt_" in p.name else "archive") for p in sorted(folder.glob("*.csv"))]
    df = h.normalize_confidence(h.pd.concat(frames, ignore_index=True))
    return df, None


def main(agg_path: Path = ROOT / "aggregats.json", data_dir: Path = ROOT / "data") -> dict:
    agg = json.loads(agg_path.read_text(encoding="utf-8"))
    ratios, sums = all_modis_variant(agg)
    years = sorted(ratios)
    report = {"held_out_years": years, "all_modis": held_out_errors(ratios, sums)}
    print(f"Held-out years: {years[0]}-{years[-1]} ({len(years)} years, each left out in turn)")
    print("Factor predicted from all MODIS (Aqua + Terra), error on the held-out year:")
    for method, e in report["all_modis"].items():
        print(f"  {method:<11} mean {e['mean_pct']:5.2f} %   max {e['max_pct']:5.2f} %")
    aqua = aqua_variant(agg, data_dir)
    if aqua is None:
        print("Aqua-only variant skipped: data/modis not found (raw FIRMS files are not versioned).")
    else:
        report["aqua_only"] = held_out_errors(*aqua)
        print("Factor predicted from Aqua only (same overpass time as Suomi NPP):")
        for method, e in report["aqua_only"].items():
            print(f"  {method:<11} mean {e['mean_pct']:5.2f} %   max {e['max_pct']:5.2f} %")
    print("The published series uses each year's own all-MODIS factor; this test only measures the"
          " alternatives.")
    return report


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
