"""Tests of the held-out test, on synthetic figures. Run: python test_validate.py"""

import unittest

import validate as v


def sums_from(ratios: dict[int, float], modis: float = 1000.0) -> dict[int, tuple[float, float]]:
    return {y: (r * modis, modis) for y, r in ratios.items()}


class ValidateTest(unittest.TestCase):
    def test_held_out_year_is_never_used(self):
        ratios = {2013: 4.0, 2014: 4.0, 2015: 40.0, 2016: 4.0}  # 2015 is an outlier
        p = v.predictors(ratios, sums_from(ratios), 2015)
        self.assertAlmostEqual(p["constant"], 4.0)  # the outlier does not pull its own prediction
        self.assertAlmostEqual(p["neighbours"], 4.0)
        self.assertAlmostEqual(p["trend"], 4.0)

    def test_constant_ratio_gives_zero_error(self):
        ratios = {y: 4.2 for y in range(2013, 2020)}
        e = v.held_out_errors(ratios, sums_from(ratios))
        for method in ("constant", "neighbours", "trend"):
            self.assertEqual(e[method]["mean_pct"], 0.0)

    def test_rising_ratio_favours_trend_over_constant(self):
        ratios = {y: 4.0 + 0.1 * (y - 2013) for y in range(2013, 2023)}
        e = v.held_out_errors(ratios, sums_from(ratios))
        self.assertLess(e["trend"]["mean_pct"], e["constant"]["mean_pct"])

    def test_usable_months_excludes_provisional_and_incomplete(self):
        months = [
            {"year": 2020, "month": 1, "snpp": 10, "modis": 2, "provisional": False},
            {"year": 2020, "month": 2, "snpp": 10, "modis": None, "provisional": False},
            {"year": 2020, "month": 3, "snpp": 10, "modis": 2, "provisional": True},
        ]
        self.assertEqual([m["month"] for m in v.usable_months(months)[2020]], [1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
