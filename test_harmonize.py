"""Tests on synthetic data (no real data). Run: python test_harmonize.py"""

import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

import harmonize as h

HEADER = "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight,type\n"


def frame(rows):
    df = pd.DataFrame(rows, columns=["acq_date", "confidence", "type"])
    df["acq_date"] = pd.to_datetime(df["acq_date"])
    df["latitude"], df["longitude"], df["source"] = 5.0, 12.0, "archive"
    return h.normalize_confidence(df)


class HarmonizeTest(unittest.TestCase):
    def test_acq_time_stays_text_with_leading_zeros(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            path.write_text(HEADER + "5.1,12.2,300,1,1,2020-01-05,0042,SNPP,SNPP,n,2,290,1.0,N,0\n", encoding="utf-8")
            df = h.load_firms(path, "archive")
        self.assertEqual(df["acq_time"].iloc[0], "0042")
        self.assertEqual(df["satellite"].iloc[0], "SNPP")

    def test_nrt_file_without_type_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fire_nrt_x.csv"
            path.write_text(HEADER.replace(",type", "") + "5.1,12.2,300,1,1,2026-08-01,1155,N21,VIIRS,h,2.0NRT,290,1.0,D\n", encoding="utf-8")
            df = h.normalize_confidence(h.load_firms(path, "nrt"))
        self.assertEqual(len(h.filter_detections(df)), 1)

    def test_modis_and_viirs_confidence_on_the_same_scale(self):
        df = frame([("2020-01-01", c, 0) for c in ["12", "30", "79", "80", "l", "n", "h"]])
        self.assertEqual(list(df["conf_level"]), [0, 1, 1, 2, 0, 1, 2])

    def test_confidence_and_archive_type_filter(self):
        df = frame([("2020-01-01", "l", 0), ("2020-01-01", "n", 0), ("2020-01-01", "h", 2), ("2020-01-01", "h", 3)])
        self.assertEqual(len(h.filter_detections(df)), 1)  # only "n, type 0" remains

    def test_monthly_counts(self):
        df = frame([("2020-01-03", "n", 0), ("2020-01-30", "h", 0), ("2020-02-01", "n", 0)])
        c = h.monthly_counts(df)
        self.assertEqual(c[(2020, 1)], 2)
        self.assertEqual(c[(2020, 2)], 1)

    def test_ratio_per_year_never_constant(self):
        # Two fully calibrated years (>= MIN_CALIBRATION_MONTHS months each).
        viirs_pairs = [((2012, m), 400) for m in range(1, 13)] + [((2013, m), 450) for m in range(1, 13)]
        modis_pairs = [((2012, m), 100) for m in range(1, 13)] + [((2013, m), 100) for m in range(1, 13)]
        viirs, modis = pd.Series(dict(viirs_pairs)), pd.Series(dict(modis_pairs))
        usable = set(viirs.index)
        r = h.yearly_ratio(viirs, modis, usable)
        self.assertEqual(r[2012]["ratio"], 4.0)
        self.assertEqual(r[2013]["ratio"], 4.5)
        self.assertEqual(h.ratio_for(2014, r), (4.5, 2013))  # year without overlap: nearest fully calibrated year

    def test_partial_year_falls_back_to_nearest_fully_calibrated_year(self):
        # 2012 and 2013 fully calibrated; 2026 has only 6 months and must NOT set its own factor.
        viirs_pairs = [((2012, m), 400) for m in range(1, 13)] + [((2013, m), 450) for m in range(1, 13)] \
            + [((2026, m), 600) for m in range(1, 7)]
        modis_pairs = [((2012, m), 100) for m in range(1, 13)] + [((2013, m), 100) for m in range(1, 13)] \
            + [((2026, m), 100) for m in range(1, 7)]
        viirs, modis = pd.Series(dict(viirs_pairs)), pd.Series(dict(modis_pairs))
        usable = set(viirs.index)
        r = h.yearly_ratio(viirs, modis, usable)
        self.assertEqual(r[2026]["months_used"], 6)
        # 2026 has its own entry in `r` (with 6 months) but ratio_for must skip it.
        ratio, source = h.ratio_for(2026, r)
        self.assertEqual(source, 2013)
        self.assertEqual(ratio, 4.5)

    def test_ratio_ignores_incomplete_months(self):
        viirs = pd.Series({(2012, 1): 400, (2012, 2): 999})
        modis = pd.Series({(2012, 1): 100, (2012, 2): 1})
        self.assertEqual(h.yearly_ratio(viirs, modis, {(2012, 1)})[2012]["ratio"], 4.0)

    def test_median_and_anomaly(self):
        counts = {(2012, 3): 10, (2013, 3): 20, (2014, 3): 30, (2015, 3): 400}
        med = h.month_medians(counts, {(2012, 3), (2013, 3), (2014, 3)})
        self.assertEqual(med[3], 20.0)
        self.assertEqual(h.anomaly_pct(30, med[3]), 50.0)
        self.assertIsNone(h.anomaly_pct(5, 0))

    def test_modis_gap_makes_august_and_september_2026_incomplete(self):
        cover = {"modis": (date(2012, 1, 20), date(2026, 11, 13)), "snpp": (date(2012, 1, 20), date(2026, 11, 2))}
        self.assertFalse(h.coverage_flags((2026, 8), cover)["modis"])
        self.assertFalse(h.coverage_flags((2026, 9), cover)["modis"])
        self.assertTrue(h.coverage_flags((2026, 10), cover)["modis"])
        self.assertFalse(h.coverage_flags((2012, 1), cover)["snpp"])  # starts on 20 January
        self.assertFalse(h.coverage_flags((2026, 11), cover)["snpp"])  # ends on 2 November

    def test_month_range(self):
        self.assertEqual(h.month_range(date(2025, 11, 5), date(2026, 2, 1)), [(2025, 11), (2025, 12), (2026, 1), (2026, 2)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
