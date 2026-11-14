"""Tests sur données synthétiques (aucune donnée réelle). Lancer : python test_harmonize.py"""

import io
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
    def test_acq_time_reste_du_texte_avec_zeros(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            path.write_text(HEADER + "5.1,12.2,300,1,1,2020-01-05,0042,SNPP,SNPP,n,2,290,1.0,N,0\n", encoding="utf-8")
            df = h.load_firms(path, "archive")
        self.assertEqual(df["acq_time"].iloc[0], "0042")
        self.assertEqual(df["satellite"].iloc[0], "SNPP")

    def test_fichier_nrt_sans_colonne_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fire_nrt_x.csv"
            path.write_text(HEADER.replace(",type", "") + "5.1,12.2,300,1,1,2026-08-01,1155,N21,VIIRS,h,2.0NRT,290,1.0,D\n", encoding="utf-8")
            df = h.normalize_confidence(h.load_firms(path, "nrt"))
        self.assertEqual(len(h.filter_detections(df)), 1)

    def test_confiance_modis_et_viirs_sur_la_meme_echelle(self):
        df = frame([("2020-01-01", c, 0) for c in ["12", "30", "79", "80", "l", "n", "h"]])
        self.assertEqual(list(df["conf_level"]), [0, 1, 1, 2, 0, 1, 2])

    def test_filtre_confiance_et_type_archive(self):
        df = frame([("2020-01-01", "l", 0), ("2020-01-01", "n", 0), ("2020-01-01", "h", 2), ("2020-01-01", "h", 3)])
        self.assertEqual(len(h.filter_detections(df)), 1)  # seul « n, type 0 » reste

    def test_comptes_mensuels(self):
        df = frame([("2020-01-03", "n", 0), ("2020-01-30", "h", 0), ("2020-02-01", "n", 0)])
        c = h.monthly_counts(df)
        self.assertEqual(c[(2020, 1)], 2)
        self.assertEqual(c[(2020, 2)], 1)

    def test_ratio_par_annee_jamais_constant(self):
        viirs = pd.Series({(2012, 1): 400, (2012, 2): 420, (2013, 1): 450})
        modis = pd.Series({(2012, 1): 100, (2012, 2): 100, (2013, 1): 100})
        r = h.yearly_ratio(viirs, modis, {(2012, 1), (2012, 2), (2013, 1)})
        self.assertEqual(r[2012]["ratio"], 4.1)
        self.assertEqual(r[2013]["ratio"], 4.5)
        self.assertEqual(h.ratio_for(2014, r), (4.5, 2013))  # année sans recouvrement : la plus proche, signalée

    def test_ratio_ignore_les_mois_incomplets(self):
        viirs = pd.Series({(2012, 1): 400, (2012, 2): 999})
        modis = pd.Series({(2012, 1): 100, (2012, 2): 1})
        self.assertEqual(h.yearly_ratio(viirs, modis, {(2012, 1)})[2012]["ratio"], 4.0)

    def test_mediane_et_anomalie(self):
        counts = {(2012, 3): 10, (2013, 3): 20, (2014, 3): 30, (2015, 3): 400}
        med = h.month_medians(counts, {(2012, 3), (2013, 3), (2014, 3)})
        self.assertEqual(med[3], 20.0)
        self.assertEqual(h.anomaly_pct(30, med[3]), 50.0)
        self.assertIsNone(h.anomaly_pct(5, 0))

    def test_trou_modis_rend_aout_et_septembre_2026_incomplets(self):
        cover = {"modis": (date(2012, 1, 20), date(2026, 11, 13)), "snpp": (date(2012, 1, 20), date(2026, 11, 2))}
        self.assertFalse(h.coverage_flags((2026, 8), cover)["modis"])
        self.assertFalse(h.coverage_flags((2026, 9), cover)["modis"])
        self.assertTrue(h.coverage_flags((2026, 10), cover)["modis"])
        self.assertFalse(h.coverage_flags((2012, 1), cover)["snpp"])  # début le 20 janvier
        self.assertFalse(h.coverage_flags((2026, 11), cover)["snpp"])  # fin le 2 novembre

    def test_suite_de_mois(self):
        self.assertEqual(h.month_range(date(2025, 11, 5), date(2026, 2, 1)), [(2025, 11), (2025, 12), (2026, 1), (2026, 2)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
