"""One test per formula of stats.py (synthetic values, no real data). Run: python -m pytest"""

import math
import random

import pytest

import stats


def test_mad_and_robust_z():
    ref = [10, 12, 11, 13, 9, 100]  # one outlier must not move the baseline much
    assert stats.mad(ref) == pytest.approx(1.5)
    z = stats.robust_z(14, ref)
    assert z == pytest.approx((14 - 11.5) / (1.4826 * 1.5), rel=1e-6)
    assert stats.robust_z(5, [3, 3, 3]) is None  # MAD = 0: no z-score, never a division by zero
    assert stats.robust_z(5, [1, 2]) is None  # too few reference values


def test_mad_scaling_matches_sigma_for_normal_data():
    rng = random.Random(1)
    sample = [rng.gauss(0, 2.0) for _ in range(20000)]
    assert stats.MAD_TO_SIGMA * stats.mad(sample) == pytest.approx(2.0, rel=0.03)


def test_signal_threshold_is_fixed_and_symmetric():
    assert stats.Z_THRESHOLD == 3.5
    assert stats.is_signal(3.5) and stats.is_signal(-4.0)
    assert not stats.is_signal(3.49) and not stats.is_signal(None)


@pytest.mark.parametrize("k", [0, 1, 3, 10, 30])
def test_poisson_interval_close_to_exact(k):
    approx, exact = stats.poisson_ci(k), stats.poisson_ci_exact(k)
    assert approx[0] == pytest.approx(exact[0], abs=0.15 + 0.01 * k)
    assert approx[1] == pytest.approx(exact[1], abs=0.15 + 0.01 * k)


def test_poisson_interval_known_values():
    lo, hi = stats.poisson_ci_exact(10)
    assert lo == pytest.approx(4.795, abs=0.01) and hi == pytest.approx(18.390, abs=0.01)  # Garwood table
    lo, hi = stats.poisson_ci(10000)
    assert (hi - lo) / 2 == pytest.approx(1.96 * math.sqrt(10000), rel=0.01)  # large k: about ± 1.96 √k


def test_bootstrap_is_reproducible_and_contains_the_total():
    days = [5, 0, 12, 3, 40, 7, 0, 9] * 4
    a = stats.bootstrap_total_ci(days, n=500, seed=3)
    assert a == stats.bootstrap_total_ci(days, n=500, seed=3)
    assert a[0] <= sum(days) <= a[1]


def test_stratified_bootstrap_keeps_the_seasonal_cycle():
    quiet, busy = [1.0] * 30, [100.0, 300.0] * 15
    lo, hi = stats.bootstrap_stratified_ci([quiet, busy], n=500)
    plain = stats.bootstrap_total_ci(quiet + busy, n=500)
    assert lo >= 30 + 100 * 30 * 0.6 and (hi - lo) < (plain[1] - plain[0])  # narrower: no mixing of months


def test_dispersion_index():
    assert stats.dispersion_index([4, 4, 4, 4]) == 0
    assert stats.dispersion_index([0, 0, 0, 40]) == pytest.approx(40.0)  # clustered: far above 1
    assert stats.dispersion_index([0, 0]) is None


def test_pixel_geometry():
    assert stats.pixel_area_km2(1.0, 1.0) == 1.0
    assert stats.pixel_area_km2(2.0, 1.4) == pytest.approx(2.8)  # MODIS toward the swath edge
    assert stats.near_nadir(1.4, stats.NADIR_MODIS_KM) and not stats.near_nadir(1.6, stats.NADIR_MODIS_KM)
    assert stats.near_nadir(0.5, stats.NADIR_VIIRS_KM) and not stats.near_nadir(0.6, stats.NADIR_VIIRS_KM)
    assert (stats.NADIR_MODIS_KM / stats.NADIR_VIIRS_KM) ** 2 == pytest.approx(7.11, abs=0.01)


def test_solar_time():
    assert stats.solar_hour("1230", 15.0) == pytest.approx(13.5)
    assert stats.solar_hour("2330", 30.0) == pytest.approx(1.5)  # past midnight
    assert stats.solar_hour("0042", 0.0) == pytest.approx(0.7)


def test_frp_sum_ignores_missing_values():
    assert stats.frp_sum_mw([1.5, 2.5, float("nan"), 6.0]) == 10.0


def test_leave_one_out_never_uses_the_held_out_year():
    series = {2013: 4.0, 2014: 4.2, 2015: 4.4, 2016: 100.0}
    pooled = {y: (v * 10, 10) for y, v in series.items()}
    p = stats.leave_one_out_predictions(series, pooled)
    assert p["trend"][2016] == pytest.approx(4.6) and p["neighbours"][2016] == pytest.approx(4.4)
    assert p["constant"][2016] == pytest.approx(4.2)
    assert stats.mape({1: 4.0, 2: 5.0}, {1: 4.4, 2: 4.5}) == pytest.approx(10.0)
