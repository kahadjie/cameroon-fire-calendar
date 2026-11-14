"""Cameroon Fire Season Check: one question, answered with physics and robust statistics, from local FIRMS files.

Question: was the latest complete fire season in Cameroon unusual compared with the previous seasons
since 2012? The main window is November to March; October to April and December to February are
computed too, to show whether the answer depends on that choice.

Reads data/ (raw FIRMS archives, not versioned) with the same filters as harmonize.py, and the month
flags (complete, provisional) of aggregats.json. Writes season.json and season.js (aggregates and the
exact texts the page shows; no raw detection). Usage: python analysis.py
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
WINDOWS = {"Nov-Mar": (11, 12, 1, 2, 3), "Oct-Apr": (10, 11, 12, 1, 2, 3, 4), "Dec-Feb": (12, 1, 2)}
WINDOW_NAMES = {"Nov-Mar": "November to March", "Oct-Apr": "October to April", "Dec-Feb": "December to February"}
MAIN_WINDOW = "Nov-Mar"  # the five months with the highest 2012-2025 medians (chosen from the same data)
COLS = ["latitude", "longitude", "acq_date", "acq_time", "satellite", "confidence", "type", "frp", "scan", "track", "daynight"]
SENSITIVITY = [2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
BOOTSTRAP_N = 2000
LOW_SEASON_MEDIAN = 2000  # a month whose usual level is below 2,000 detections is "low-fire season"
VALIDATION_METHOD = "frp_aqua_day_nadir"  # the one cross-sensor check this product quotes
LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


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


def season_months(end_year: int, window: tuple[int, ...]) -> list[tuple[int, int]]:
    """Months of the season ending in end_year: October to December belong to the previous year."""
    return [(end_year - 1 if m >= 10 else end_year, m) for m in window]


def median_of(values: list[float]) -> float:
    return float(median(values))


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
                    "frp_mw": round(frp.get(k, 0.0)), "median": median_of([counts[(r["year"], r["month"])] for r in base]) if base else None,
                    "z_count": None if zc is None else round(zc, 2), "z_frp": None if zf is None else round(zf, 2),
                    "signal": stats.is_signal(zc, threshold), "provisional": m["provisional"]})
    return out


def seasons(window: tuple[int, ...], months: list[dict], counts: dict, frp: dict, snpp: pd.DataFrame,
            n20_counts: dict | None = None, n20_complete: set | None = None) -> list[dict]:
    flag = {(m["year"], m["month"]): m for m in months}
    out = []
    for y in range(2012, max(m["year"] for m in months) + 1):
        ks = season_months(y, window)
        if not all(k in flag and flag[k]["snpp"] is not None and not flag[k]["provisional"] for k in ks):
            continue
        groups = [daily(snpp, date(yy, mm, 1), date(yy + (mm == 12), mm % 12 + 1, 1) - timedelta(days=1)) for yy, mm in ks]
        n20 = None
        if n20_counts is not None and all(k in n20_complete for k in ks):
            n20 = int(sum(n20_counts.get(k, 0) for k in ks))
        total = int(sum(counts[k] for k in ks))
        out.append({"season": f"{y - 1}-{str(y)[2:]}" if window[0] >= 10 else str(y), "end_year": y, "count": total,
                    "frp_mw": round(sum(frp.get(k, 0.0) for k in ks)), "n20": n20,
                    "poisson_ci95": [round(v) for v in stats.poisson_ci(total)],
                    "bootstrap_ci95": [round(v) for v in stats.bootstrap_stratified_ci(groups, n=BOOTSTRAP_N)],
                    "dispersion": round(median_of([stats.dispersion_index(g) for g in groups]), 1)})
    for s in out:  # robust z of each season against the other seasons of the same window
        others = [o for o in out if o is not s]
        s["median_others"] = median_of([o["count"] for o in others])
        s["median_others_frp"] = median_of([o["frp_mw"] for o in others])
        s["z_count"] = round(stats.robust_z(s["count"], [o["count"] for o in others]), 2)
        s["z_frp"] = round(stats.robust_z(s["frp_mw"], [o["frp_mw"] for o in others]), 2)
        n20o = [o["n20"] for o in others if o["n20"] is not None]
        zn = stats.robust_z(s["n20"], n20o) if s["n20"] is not None and len(n20o) >= 3 else None
        s["z_n20"] = None if zn is None else round(zn, 2)
        s["pct_vs_median_count"] = round(100 * (s["count"] - s["median_others"]) / s["median_others"], 1)
        s["pct_vs_median_frp"] = round(100 * (s["frp_mw"] - s["median_others_frp"]) / s["median_others_frp"], 1)
        s["rank_from_lowest"] = 1 + sum(1 for o in others if o["count"] < s["count"])
    return out


def sensor_comparison(snpp: pd.DataFrame, modis: pd.DataFrame, usable: set) -> dict:
    """Per year, over months complete for both sensors: count and FRP ratios, all passes, same hour
    (daytime Suomi NPP vs daytime Aqua), same hour near nadir. Plus pixel areas and solar times."""
    def keep(df):
        return df[[k in usable for k in zip(df["acq_date"].dt.year, df["acq_date"].dt.month)]]
    s, m = keep(snpp), keep(modis)
    s_area, m_area = s["scan"] * s["track"], m["scan"] * m["track"]
    solar = lambda d: round(float(d.apply(lambda r: stats.solar_hour(r["acq_time"], r["longitude"]), axis=1).median()), 2) if len(d) else None
    years = {}
    for y in sorted(set(s["acq_date"].dt.year) & set(m["acq_date"].dt.year)):
        sy, my = s[s["acq_date"].dt.year == y], m[m["acq_date"].dt.year == y]
        sd, ad = sy[sy["daynight"] == "D"], my[(my["satellite"] == "Aqua") & (my["daynight"] == "D")]
        sdn = sd[sd["scan"] <= stats.NEAR_NADIR_FACTOR * stats.NADIR_VIIRS_KM]
        adn = ad[ad["scan"] <= stats.NEAR_NADIR_FACTOR * stats.NADIR_MODIS_KM]
        terra = my[(my["satellite"] == "Terra") & (my["daynight"] == "D")]
        sums = {"count_all": (len(sy), len(my)), "frp_all": (stats.frp_sum_mw(sy["frp"]), stats.frp_sum_mw(my["frp"])),
                "count_aqua_day": (len(sd), len(ad)), "frp_aqua_day": (stats.frp_sum_mw(sd["frp"]), stats.frp_sum_mw(ad["frp"])),
                "count_aqua_day_nadir": (len(sdn), len(adn)), "frp_aqua_day_nadir": (stats.frp_sum_mw(sdn["frp"]), stats.frp_sum_mw(adn["frp"]))}
        years[int(y)] = {"months_used": len({k for k in usable if k[0] == y}),
                         **{k: round(a / b, 3) for k, (a, b) in sums.items()},
                         "solar_h_snpp": solar(sd), "solar_h_aqua": solar(ad), "solar_h_terra": solar(terra), "_sums": sums}
    full = {y: v for y, v in years.items() if v["months_used"] == 12}
    validation = {}
    for key in ("count_all", "frp_all", "count_aqua_day", "frp_aqua_day", "count_aqua_day_nadir", "frp_aqua_day_nadir"):
        series = {y: v[key] for y, v in full.items()}
        preds = stats.leave_one_out_predictions(series, {y: v["_sums"][key] for y, v in full.items()})
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
        "pct_off_nadir_modis": round(100 * float((m["scan"] > stats.NEAR_NADIR_FACTOR * stats.NADIR_MODIS_KM).mean())),
        "pct_off_nadir_snpp": round(100 * float((s["scan"] > stats.NEAR_NADIR_FACTOR * stats.NADIR_VIIRS_KM).mean())),
    }
    return {"by_year": years, "validation": validation, "geometry": geometry, "full_years": sorted(full)}


# ---- Texts shown by the page: built here, from the numbers above only (tested in test_season_texts.py).

def fmt_n(v: float) -> str:
    return f"{int(round(v)):,}"


def fmt_z(v: float) -> str:
    return f"{v:+.1f}"


def fmt_pct(v: float) -> str:
    return f"{abs(v):.0f}% {'above' if v >= 0 else 'below'}"


def fmt_date(d: str) -> str:
    y, m, dd = (int(x) for x in d.split("-"))
    return f"{dd} {LONG[m - 1]} {y}"


def place(rank: int, n: int) -> str:
    return "the lowest" if rank == 1 else "the highest" if rank == n else f"number {rank} from the lowest"


def texts(out: dict) -> dict:
    t = out["meta"]["z_threshold"]
    w = out["windows"]
    main = w[MAIN_WINDOW]["seasons"][-1]
    n_main = w[MAIN_WINDOW]["n_seasons"]
    ms = out["monthly_summary"]
    flags = {k: abs(v["seasons"][-1]["z_count"]) >= t for k, v in w.items()}
    same = len(set(flags.values())) == 1
    head = ("Yes" if flags[MAIN_WINDOW] else "No") if same else "It depends on the months counted"
    answer = (f"{head}: the {main['season']} season ({WINDOW_NAMES[MAIN_WINDOW]}) had {fmt_n(main['count'])} fire detections, "
              f"{place(main['rank_from_lowest'], n_main)} of {n_main} seasons and {fmt_pct(main['pct_vs_median_count'])} the usual season, "
              f"{'beyond' if flags[MAIN_WINDOW] else 'but within'} the normal year-to-year range (robust z = {fmt_z(main['z_count'])}; "
              f"flagged only beyond ±{t}).")
    if same:
        answer += f" The answer is the same when the season is counted from {WINDOW_NAMES['Oct-Apr']} or from {WINDOW_NAMES['Dec-Feb']}."
    else:
        answer += " " + "; ".join(f"{WINDOW_NAMES[k]}: {'flagged' if f else 'not flagged'}" for k, f in flags.items()) + "."
    v = out["sensors"]["validation"]
    g = out["sensors"]["geometry"]
    a = out["n20_agreement"]
    val = v[VALIDATION_METHOD]
    return {
        "answer": answer,
        "range": f"95% range for this season's total: {fmt_n(main['bootstrap_ci95'][0])} to {fmt_n(main['bootstrap_ci95'][1])} detections; the usual season is {fmt_n(main['median_others'])}.",
        "frp": f"Fire radiative power, an index of fire intensity, tells the same story: {fmt_pct(main['pct_vs_median_frp'])} the usual season (robust z = {fmt_z(main['z_frp'])}).",
        "windows": [[k.replace("-", "–"), fmt_n(s["count"]), fmt_pct(s["pct_vs_median_count"]), fmt_z(s["z_count"]), "yes" if flags[k] else "no"]
                    for k, data in w.items() for s in [data["seasons"][-1]]],
        "seasons": [[s["season"], fmt_n(s["count"]), fmt_n(s["bootstrap_ci95"][0]), fmt_n(s["bootstrap_ci95"][1]), fmt_z(s["z_count"]), s is main]
                    for s in w[MAIN_WINDOW]["seasons"]],
        "months_intro": f"{ms['flagged']} of {ms['tested']} months pass the ±{t} threshold"
                        + (f"; {ms['low_season']} of them fall in the low-fire season, when a few hundred detections are enough to stand out."
                           if ms["low_season"] else "."),
        "months": [[f"{LONG[m['month'] - 1]} {m['year']}", fmt_n(m["count"]), f"{fmt_n(m['count_ci95'][0])}–{fmt_n(m['count_ci95'][1])}", fmt_n(m["median"]), fmt_z(m["z_count"])]
                   for m in out["monthly"] if m.get("signal")],
        "power": (f"Suomi NPP records about {v['count_all']['mean']:.1f} times more detections than MODIS, but only {v['frp_all']['mean']:.1f} times more fire radiative power: "
                  "its smaller pixels catch many small fires that add little to the index of fire intensity. Comparing at the same hour (daytime Suomi NPP vs Aqua) "
                  "near the centre of the swath makes the comparison steadier from year to year."),
        "sensors": [[label, f"{v[c]['mean']:.2f}", f"{v[c]['cv_pct']:.1f}%", f"{v[f]['mean']:.2f}", f"{v[f]['cv_pct']:.1f}%", f"{v[f]['mape_constant']:.2f}%"]
                    for label, c, f in (("All passes", "count_all", "frp_all"), ("Same hour (daytime Aqua)", "count_aqua_day", "frp_aqua_day"),
                                        ("Same hour, near nadir", "count_aqua_day_nadir", "frp_aqua_day_nadir"))],
        "geometry": (f"Pixel size grows away from the centre of the swath: the mean MODIS pixel covers {g['mean_area_modis_km2']:.3f} km² "
                     f"({g['nadir_area_modis_km2']:.0f} km² at nadir, up to {g['max_area_modis_km2']:.1f} km²); {g['pct_off_nadir_modis']}% of MODIS detections are "
                     f"more than {out['meta']['near_nadir_factor']} times their nadir size, against {g['pct_off_nadir_snpp']}% for Suomi NPP."),
        "check": (f"Cross-sensor check used by this product: the same-hour, near-nadir fire radiative power ratio (Suomi NPP / Aqua, daytime). "
                  f"Leaving each full year out in turn, it is predicted within {val['mape_constant']:.2f}% on average, against "
                  f"{v['count_all']['mape_constant']:.2f}% for one constant detection-count ratio. An independent satellite, NOAA-20, places the season "
                  f"on the same side of the usual level in {a['same_sign']} of {a['seasons']} seasons. Daily counts vary about {out['dispersion_median']:.0f} "
                  "times more than a Poisson count would, so the 95% range resamples days instead. Changing the threshold:"),
        "sensitivity": [[f"{s['threshold']}" + (" (chosen in advance)" if s["threshold"] == t else ""), f"{s['months_flagged']} of {s['months_tested']}",
                         f"{s['seasons_flagged']} of {n_main}", "yes" if s["latest_season_flagged"] else "no"] for s in out["sensitivity"]],
        "snpp_end": fmt_date(out["meta"]["snpp_end"]),
        "generated": f"Analysis generated {out['meta']['generated']}.",
    }


def build() -> dict:
    agg = json.loads((ROOT / "aggregats.json").read_text(encoding="utf-8"))
    months = agg["months"]
    snpp, modis, n20 = load("snpp"), load("modis"), load("noaa20")
    counts = by_month(snpp)
    # The monthly Suomi NPP counts must be exactly those published on main (aggregats.json).
    mismatch = [(m["year"], m["month"]) for m in months if m["snpp"] is not None and int(counts.get((m["year"], m["month"]), 0)) != m["snpp"]]
    if mismatch:
        raise SystemExit(f"S-NPP counts differ from aggregats.json for {mismatch[:3]}")
    frp = by_month(snpp, "frp")
    n20_counts = by_month(n20)
    n20_complete = {(m["year"], m["month"]) for m in months if m["complete"].get("n20")}
    usable = {(m["year"], m["month"]) for m in months if m["complete"]["snpp"] and m["complete"]["modis"] and not m["provisional"]}
    windows = {k: {"months": list(win), "seasons": seasons(win, months, counts, frp, snpp,
                                                           n20_counts if k == MAIN_WINDOW else None, n20_complete if k == MAIN_WINDOW else None)}
               for k, win in WINDOWS.items()}
    for w in windows.values():
        w["n_seasons"] = len(w["seasons"])
    main = windows[MAIN_WINDOW]["seasons"]
    sens = []
    for t in SENSITIVITY:
        flagged = monthly_signals(months, counts, frp, t)
        sens.append({"threshold": t, "months_flagged": sum(1 for r in flagged if r.get("signal")),
                     "months_tested": sum(1 for r in flagged if r.get("z_count") is not None),
                     "seasons_flagged": sum(1 for s in main if stats.is_signal(s["z_count"], t)),
                     "latest_season_flagged": stats.is_signal(main[-1]["z_count"], t)})
    agree = [s for s in main if s["z_n20"] is not None]
    out = {
        "meta": {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "country": "Cameroon",
                 "source": "NASA FIRMS, https://firms.modaps.eosdis.nasa.gov", "main_series": "Suomi NPP (VIIRS 375 m)",
                 "snpp_end": agg["meta"]["coverage"]["snpp"][1], "main_window": MAIN_WINDOW, "z_threshold": stats.Z_THRESHOLD,
                 "near_nadir_factor": stats.NEAR_NADIR_FACTOR, "bootstrap_n": BOOTSTRAP_N, "validation_method": VALIDATION_METHOD,
                 "mad_to_sigma": stats.MAD_TO_SIGMA, "ci_level_pct": 95},
        "windows": windows,
        "monthly": (monthly := monthly_signals(months, counts, frp, stats.Z_THRESHOLD)),
        "monthly_summary": {"flagged": sum(1 for m in monthly if m.get("signal")),
                            "tested": sum(1 for m in monthly if m.get("z_count") is not None),
                            "low_season": sum(1 for m in monthly if m.get("signal") and m["median"] < LOW_SEASON_MEDIAN),
                            "low_season_median_below": LOW_SEASON_MEDIAN},
        "sensors": sensor_comparison(snpp, modis, usable),
        "sensitivity": sens,
        "n20_agreement": {"seasons": len(agree), "same_sign": sum(1 for s in agree if (s["z_count"] >= 0) == (s["z_n20"] >= 0)),
                          "pairs": [[s["season"], s["z_count"], s["z_n20"]] for s in agree]},
        "dispersion_median": median_of([s["dispersion"] for s in main]),
    }
    out["text"] = texts(out)
    return out


def main() -> int:
    out = build()
    (ROOT / "season.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "season.js").write_text("window.SEASON_CHECK=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(out["text"]["answer"])
    for row in out["text"]["windows"]:
        print("  ", " | ".join(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
