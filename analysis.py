"""Jury v2 analysis: one question, answered with physics and robust statistics, from local FIRMS files.

Question: was the latest complete fire season (November to March) in Cameroon unusually active
compared with the previous seasons since 2012?

Reads data/ (raw FIRMS archives, not versioned) with the same filters as harmonize.py, and the month
flags (complete, provisional) of aggregats.json. Writes jury.json and jury.js (aggregates only).
Usage: python analysis.py
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import median

import pandas as pd

import harmonize as h
import stats

ROOT = Path(__file__).resolve().parent
SEASON = (11, 12, 1, 2, 3)  # the five months with the highest medians (Nov to Mar), see README
FOLDERS = {"snpp": "snpp", "modis": "modis", "n20": "noaa20"}
COLS = ["latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence", "type", "frp", "scan", "track", "daynight"]
SENSITIVITY = [2.0, 2.5, 3.0, 3.5, 4.0, 5.0]


def load(folder: str) -> pd.DataFrame:
    frames = []
    for p in sorted((h.DATA / folder).glob("*.csv")):
        head = pd.read_csv(p, nrows=0).columns
        df = pd.read_csv(p, usecols=[c for c in COLS if c in head], dtype={"acq_time": str, "satellite": str, "confidence": str})
        df["acq_time"] = df["acq_time"].str.zfill(4)
        df["acq_date"] = pd.to_datetime(df["acq_date"], format="%Y-%m-%d")
        df["source"] = "nrt" if "_nrt_" in p.name else "archive"
        if "type" not in df.columns:
            df["type"] = pd.NA
        frames.append(df)
    return h.filter_detections(h.normalize_confidence(pd.concat(frames, ignore_index=True)))


def by_month(df: pd.DataFrame, value: str | None = None) -> dict[tuple[int, int], float]:
    g = df.groupby([df["acq_date"].dt.year, df["acq_date"].dt.month])
    s = g.size() if value is None else g[value].sum()
    return {(int(y), int(m)): float(v) for (y, m), v in s.items()}


def daily(df: pd.DataFrame, start: date, end: date) -> list[float]:
    """Detections per day from start to end inclusive, zero for days without detection."""
    counts = df.groupby(df["acq_date"].dt.date).size()
    days, d = [], start
    while d <= end:
        days.append(float(counts.get(d, 0)))
        d += timedelta(days=1)
    return days


def season_months(end_year: int) -> list[tuple[int, int]]:
    return [(end_year - 1, 11), (end_year - 1, 12), (end_year, 1), (end_year, 2), (end_year, 3)]


def monthly_signals(months: list[dict], counts: dict, frp: dict, threshold: float) -> list[dict]:
    """Robust z of each final month against the same calendar month of the OTHER reference years."""
    ref = [m for m in months if m["snpp"] is not None and not m["provisional"] and m["year"] <= 2025]
    out = []
    for m in months:
        k = (m["year"], m["month"])
        if m["snpp"] is None:
            out.append({"year": k[0], "month": k[1], "count": None})
            continue
        base = [r for r in ref if r["month"] == k[1] and r["year"] != k[0]]
        zc = stats.robust_z(counts[k], [counts[(r["year"], r["month"])] for r in base])
        zf = stats.robust_z(frp.get(k, 0.0), [frp.get((r["year"], r["month"]), 0.0) for r in base])
        lo, hi = stats.poisson_ci(int(counts[k]))
        out.append({"year": k[0], "month": k[1], "count": int(counts[k]), "count_ci95": [round(lo), round(hi)],
                    "frp_mw": round(frp.get(k, 0.0)), "median": median([counts[(r["year"], r["month"])] for r in base]) if base else None,
                    "z_count": None if zc is None else round(zc, 2), "z_frp": None if zf is None else round(zf, 2),
                    "signal": stats.is_signal(zc, threshold), "provisional": m["provisional"]})
    return out


def seasons(months: list[dict], counts: dict, frp: dict, snpp: pd.DataFrame, n20_counts: dict, n20_complete: set) -> list[dict]:
    flag = {(m["year"], m["month"]): m for m in months}
    out = []
    for y in range(2013, max(m["year"] for m in months) + 1):
        ks = season_months(y)
        if not all(k in flag and flag[k]["snpp"] is not None and not flag[k]["provisional"] for k in ks):
            continue
        n20 = sum(n20_counts.get(k, 0) for k in ks) if all(k in n20_complete for k in ks) else None
        groups = [daily(snpp, date(yy, mm, 1), date(yy + (mm == 12), mm % 12 + 1, 1) - timedelta(days=1)) for yy, mm in ks]
        out.append({"season": f"{y - 1}-{str(y)[2:]}", "end_year": y, "count": int(sum(counts[k] for k in ks)),
                    "frp_mw": round(sum(frp.get(k, 0.0) for k in ks)), "n20": n20,
                    "poisson_ci95": [round(v) for v in stats.poisson_ci(int(sum(counts[k] for k in ks)))],
                    "bootstrap_ci95": [round(v) for v in stats.bootstrap_stratified_ci(groups)],
                    "dispersion": round(median(stats.dispersion_index(g) for g in groups), 1)})
    for s in out:  # robust z of each season against the other seasons
        others = [o for o in out if o is not s]
        s["z_count"] = round(stats.robust_z(s["count"], [o["count"] for o in others]), 2)
        s["z_frp"] = round(stats.robust_z(s["frp_mw"], [o["frp_mw"] for o in others]), 2)
        n20o = [o["n20"] for o in others if o["n20"] is not None]
        zn = stats.robust_z(s["n20"], n20o) if s["n20"] is not None and len(n20o) >= 3 else None
        s["z_n20"] = None if zn is None else round(zn, 2)
        s["pct_vs_median_count"] = round(100 * (s["count"] - median(o["count"] for o in others)) / median(o["count"] for o in others), 1)
        s["pct_vs_median_frp"] = round(100 * (s["frp_mw"] - median(o["frp_mw"] for o in others)) / median(o["frp_mw"] for o in others), 1)
    return out


def sensor_comparison(snpp: pd.DataFrame, modis: pd.DataFrame, usable: set) -> dict:
    """Per year, over months complete for both sensors: count and FRP ratios, all pixels, time-matched
    (daytime S-NPP vs daytime Aqua), and time-matched near nadir. Plus pixel areas and solar times."""
    def keep(df):
        return df[[k in usable for k in zip(df["acq_date"].dt.year, df["acq_date"].dt.month)]]
    s, m = keep(snpp), keep(modis)
    s_area = s["scan"] * s["track"]
    m_area = m["scan"] * m["track"]
    years = {}
    for y in sorted(set(s["acq_date"].dt.year) & set(m["acq_date"].dt.year)):
        sy, my = s[s["acq_date"].dt.year == y], m[m["acq_date"].dt.year == y]
        sd, ad = sy[sy["daynight"] == "D"], my[(my["satellite"] == "Aqua") & (my["daynight"] == "D")]
        sdn = sd[sd["scan"] <= stats.NEAR_NADIR_FACTOR * stats.NADIR_VIIRS_KM]
        adn = ad[ad["scan"] <= stats.NEAR_NADIR_FACTOR * stats.NADIR_MODIS_KM]
        terra = my[(my["satellite"] == "Terra") & (my["daynight"] == "D")]
        months_used = len({(yy, mm) for yy, mm in usable if yy == y})
        years[int(y)] = {
            "months_used": months_used,
            "count_all": round(len(sy) / len(my), 3), "frp_all": round(stats.frp_sum_mw(sy["frp"]) / stats.frp_sum_mw(my["frp"]), 3),
            "count_aqua_day": round(len(sd) / len(ad), 3), "frp_aqua_day": round(stats.frp_sum_mw(sd["frp"]) / stats.frp_sum_mw(ad["frp"]), 3),
            "count_aqua_day_nadir": round(len(sdn) / len(adn), 3), "frp_aqua_day_nadir": round(stats.frp_sum_mw(sdn["frp"]) / stats.frp_sum_mw(adn["frp"]), 3),
            "solar_h_snpp": round(float(sd.apply(lambda r: stats.solar_hour(r["acq_time"], r["longitude"]), axis=1).median()), 2),
            "solar_h_aqua": round(float(ad.apply(lambda r: stats.solar_hour(r["acq_time"], r["longitude"]), axis=1).median()), 2),
            "solar_h_terra": round(float(terra.apply(lambda r: stats.solar_hour(r["acq_time"], r["longitude"]), axis=1).median()), 2) if len(terra) else None,
            "_sums": {"count_all": (len(sy), len(my)), "frp_all": (stats.frp_sum_mw(sy["frp"]), stats.frp_sum_mw(my["frp"])),
                      "count_aqua_day": (len(sd), len(ad)), "frp_aqua_day": (stats.frp_sum_mw(sd["frp"]), stats.frp_sum_mw(ad["frp"])),
                      "count_aqua_day_nadir": (len(sdn), len(adn)), "frp_aqua_day_nadir": (stats.frp_sum_mw(sdn["frp"]), stats.frp_sum_mw(adn["frp"]))},
        }
    full = {y: v for y, v in years.items() if v["months_used"] == 12}
    validation = {}
    for key in ("count_all", "frp_all", "count_aqua_day", "frp_aqua_day", "count_aqua_day_nadir", "frp_aqua_day_nadir"):
        series = {y: v[key] for y, v in full.items()}
        pooled = {y: v["_sums"][key] for y, v in full.items()}
        preds = stats.leave_one_out_predictions(series, pooled)
        vals = list(series.values())
        validation[key] = {"mape_constant": round(stats.mape(series, preds["constant"]), 2),
                           "mape_neighbours": round(stats.mape(series, preds["neighbours"]), 2),
                           "mape_trend": round(stats.mape(series, preds["trend"]), 2),
                           "mean": round(sum(vals) / len(vals), 3),
                           "cv_pct": round(100 * pd.Series(vals).std() / (sum(vals) / len(vals)), 1)}
    for v in years.values():
        del v["_sums"]
    geometry = {
        "mean_area_snpp_km2": round(float(s_area.mean()), 3), "mean_area_modis_km2": round(float(m_area.mean()), 3),
        "nadir_area_snpp_km2": round(stats.NADIR_VIIRS_KM ** 2, 3), "nadir_area_modis_km2": stats.NADIR_MODIS_KM ** 2,
        "max_area_modis_km2": round(float(m_area.max()), 2), "max_area_snpp_km2": round(float(s_area.max()), 3),
        "share_off_nadir_modis": round(float((m["scan"] > stats.NEAR_NADIR_FACTOR * stats.NADIR_MODIS_KM).mean()), 3),
        "share_off_nadir_snpp": round(float((s["scan"] > stats.NEAR_NADIR_FACTOR * stats.NADIR_VIIRS_KM).mean()), 3),
    }
    return {"by_year": years, "validation": validation, "geometry": geometry, "full_years": sorted(full)}


def build() -> dict:
    agg = json.loads((ROOT / "aggregats.json").read_text(encoding="utf-8"))
    months = agg["months"]
    snpp, modis, n20 = load("snpp"), load("modis"), load("noaa20")
    counts = by_month(snpp)
    check = {(m["year"], m["month"]): m["snpp"] for m in months if m["snpp"] is not None}
    mismatch = [k for k, v in check.items() if int(counts.get(k, 0)) != v]
    if mismatch:
        raise SystemExit(f"S-NPP counts differ from aggregats.json for {mismatch[:3]}")
    frp = by_month(snpp, "frp")
    n20_counts = by_month(n20)
    n20_complete = {(m["year"], m["month"]) for m in months if m["complete"].get("n20")}
    usable = {(m["year"], m["month"]) for m in months if m["complete"]["snpp"] and m["complete"]["modis"] and not m["provisional"]}
    monthly = monthly_signals(months, counts, frp, stats.Z_THRESHOLD)
    seas = seasons(months, counts, frp, snpp, n20_counts, n20_complete)
    comp = sensor_comparison(snpp, modis, usable)
    sens = []
    for t in SENSITIVITY:
        flagged = monthly_signals(months, counts, frp, t)
        sens.append({"threshold": t, "months_flagged": sum(1 for r in flagged if r.get("signal")),
                     "months_tested": sum(1 for r in flagged if r.get("z_count") is not None),
                     "seasons_flagged": sum(1 for s in seas if stats.is_signal(s["z_count"], t)),
                     "latest_season_flagged": stats.is_signal(seas[-1]["z_count"], t)})
    agree = [s for s in seas if s["z_n20"] is not None]
    return {
        "meta": {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "country": "Cameroon",
                 "source": "NASA FIRMS, https://firms.modaps.eosdis.nasa.gov", "main_series": "Suomi NPP (VIIRS 375 m)",
                 "snpp_end": agg["meta"]["coverage"]["snpp"][1], "season_months": list(SEASON),
                 "z_threshold": stats.Z_THRESHOLD, "near_nadir_factor": stats.NEAR_NADIR_FACTOR},
        "seasons": seas, "monthly": monthly, "sensors": comp, "sensitivity": sens,
        "n20_agreement": {"seasons": len(agree), "same_sign": sum(1 for s in agree if (s["z_count"] >= 0) == (s["z_n20"] >= 0)),
                          "pairs": [[s["season"], s["z_count"], s["z_n20"]] for s in agree]},
        "dispersion_median": median(s["dispersion"] for s in seas),
    }


def main() -> int:
    out = build()
    (ROOT / "jury.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "jury.js").write_text("window.JURY=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    last = out["seasons"][-1]
    print(f"latest season {last['season']}: {last['count']} detections ({last['pct_vs_median_count']:+}% vs median), z={last['z_count']}, FRP z={last['z_frp']}, bootstrap {last['bootstrap_ci95']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
