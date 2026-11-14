"""Pure statistical and physical formulas used by analysis.py (each one tested in test_stats.py).

Sources:
- Robust z-score: Iglewicz, B. & Hoaglin, D. (1993), How to Detect and Handle Outliers, ASQC. Modified
  z = 0.6745 (x − median) / MAD, i.e. (x − median) / (1.4826 MAD); outlier threshold 3.5.
- Poisson 95% interval: Wilson–Hilferty approximation of the exact (Garwood 1936) interval, as given by
  Breslow, N. & Day, N. (1987), Statistical Methods in Cancer Research vol. II, IARC, p. 69.
- Day-block bootstrap: Efron, B. & Tibshirani, R. (1993), An Introduction to the Bootstrap, Chapman & Hall.
- Pixel size: MODIS 1 km and VIIRS I-band 375 m at nadir; FIRMS `scan` and `track` columns give the
  actual pixel size (km) of each detection, which grows with the scan angle (FIRMS attribute
  documentation).
- Local solar time = UTC + longitude / 15 h (mean solar time).
"""

from __future__ import annotations

import math
import random
from statistics import median

MAD_TO_SIGMA = 1.4826  # 1 / Φ⁻¹(3/4): makes the MAD consistent with σ for normal data
Z_THRESHOLD = 3.5      # fixed before looking at the data (Iglewicz & Hoaglin 1993)
Z95 = 1.959964
NADIR_MODIS_KM = 1.0
NADIR_VIIRS_KM = 0.375
NEAR_NADIR_FACTOR = 1.5  # "near nadir": pixel side at most 1.5 × its nadir size (assumption, see docs)


def mad(values: list[float]) -> float:
    """Median absolute deviation (unscaled)."""
    m = median(values)
    return median(abs(v - m) for v in values)


def robust_z(x: float, reference: list[float]) -> float | None:
    """(x − median) / (1.4826 × MAD) of the reference; None if the MAD is zero or there is no reference."""
    if len(reference) < 3:
        return None
    s = MAD_TO_SIGMA * mad(reference)
    if s == 0:
        return None
    return (x - median(reference)) / s


def is_signal(z: float | None, threshold: float = Z_THRESHOLD) -> bool:
    return z is not None and abs(z) >= threshold


def poisson_ci(k: int, z: float = Z95) -> tuple[float, float]:
    """Approximate exact 95% interval of a Poisson mean given k events (Breslow & Day 1987)."""
    if k < 0:
        raise ValueError("count must be >= 0")
    lower = 0.0 if k == 0 else k * (1 - 1 / (9 * k) - z / (3 * math.sqrt(k))) ** 3
    k1 = k + 1
    upper = k1 * (1 - 1 / (9 * k1) + z / (3 * math.sqrt(k1))) ** 3
    return lower, upper


def poisson_ci_exact(k: int, level: float = 0.95) -> tuple[float, float]:
    """Exact (Garwood) interval by bisection on the Poisson CDF; for checking small counts in tests."""
    a = (1 - level) / 2

    def cdf(n, mu):  # P(X <= n)
        term = total = math.exp(-mu)
        for i in range(1, n + 1):
            term *= mu / i
            total += term
        return total

    def root_increasing(f, lo, hi):  # f increasing in mu, f(lo) < 0 < f(hi)
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid) < 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    top = k + 20 * math.sqrt(k + 1) + 20
    # lower L: P(X >= k | L) = a ; upper U: P(X <= k | U) = a
    lower = 0.0 if k == 0 else root_increasing(lambda mu: (1 - cdf(k - 1, mu)) - a, 0.0, top)
    upper = root_increasing(lambda mu: a - cdf(k, mu), 0.0, top)
    return lower, upper


def bootstrap_total_ci(daily: list[float], n: int = 2000, seed: int = 42, level: float = 0.95) -> tuple[float, float]:
    """95% interval of a period total by resampling its days with replacement (keeps the clustering of
    detections within a day, which a Poisson interval ignores)."""
    rng = random.Random(seed)
    k = len(daily)
    totals = sorted(sum(daily[rng.randrange(k)] for _ in range(k)) for _ in range(n))
    lo = totals[int((1 - level) / 2 * n)]
    hi = totals[min(n - 1, int((1 + level) / 2 * n))]
    return lo, hi


def bootstrap_stratified_ci(groups: list[list[float]], n: int = 2000, seed: int = 42, level: float = 0.95) -> tuple[float, float]:
    """Like bootstrap_total_ci, but days are resampled within each group (calendar month), so a quiet
    November day never replaces a busy February day: the seasonal cycle is kept."""
    rng = random.Random(seed)
    totals = sorted(sum(sum(g[rng.randrange(len(g))] for _ in range(len(g))) for g in groups if g) for _ in range(n))
    return totals[int((1 - level) / 2 * n)], totals[min(n - 1, int((1 + level) / 2 * n))]


def dispersion_index(daily: list[float]) -> float | None:
    """Variance / mean of daily counts: 1 for Poisson, above 1 when detections cluster (overdispersion)."""
    if len(daily) < 2:
        return None
    m = sum(daily) / len(daily)
    if m == 0:
        return None
    var = sum((d - m) ** 2 for d in daily) / (len(daily) - 1)
    return var / m


def pixel_area_km2(scan_km: float, track_km: float) -> float:
    """Ground footprint of a detection pixel (along-scan × along-track, km²)."""
    return scan_km * track_km


def near_nadir(scan_km: float, nadir_km: float, factor: float = NEAR_NADIR_FACTOR) -> bool:
    """True when the pixel is at most `factor` times its nadir size along the scan."""
    return scan_km <= factor * nadir_km


def solar_hour(acq_time: str, longitude: float) -> float:
    """Local mean solar time (h) from FIRMS acq_time (UTC, 'HHMM') and longitude (degrees east)."""
    t = acq_time.zfill(4)
    return (int(t[:2]) + int(t[2:]) / 60 + longitude / 15) % 24


def frp_sum_mw(frps: list[float]) -> float:
    """Sum of fire radiative power over detections (MW): an index of fire intensity at overpass times.
    Nothing is integrated over time, because the data do not say how long each fire burned."""
    return float(sum(f for f in frps if f == f))  # ignores NaN


def leave_one_out_predictions(series: dict[int, float], pooled: dict[int, tuple[float, float]]) -> dict[str, dict[int, float]]:
    """For each year, the ratio predicted from the OTHER years: one constant (pooled), adjacent years, trend."""
    out: dict[str, dict[int, float]] = {"constant": {}, "neighbours": {}, "trend": {}}
    for y in series:
        others = {k: v for k, v in series.items() if k != y}
        out["constant"][y] = sum(pooled[k][0] for k in others) / sum(pooled[k][1] for k in others)
        near = [others[k] for k in (y - 1, y + 1) if k in others]
        out["neighbours"][y] = sum(near) / len(near) if near else others[min(others, key=lambda k: abs(k - y))]
        xs, ys = list(others), list(others.values())
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        slope = sum((x - mx) * (v - my) for x, v in zip(xs, ys)) / sxx if sxx else 0.0
        out["trend"][y] = my + slope * (y - mx)
    return out


def mape(actual: dict[int, float], predicted: dict[int, float]) -> float:
    """Mean absolute percentage error (%)."""
    errs = [abs(predicted[y] - a) / a for y, a in actual.items()]
    return 100 * sum(errs) / len(errs)
