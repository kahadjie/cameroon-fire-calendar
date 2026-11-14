"""Inspection des fichiers FIRMS réels de data/ (lecture seule). Lancer : python inspect_archives.py"""

from pathlib import Path

import pandas as pd

import harmonize as h

for folder in ["modis", "snpp", "noaa20", "noaa21"]:
    for path in sorted((h.DATA / folder).glob("*.csv")):
        df = h.normalize_confidence(h.load_firms(path, "nrt" if "_nrt_" in path.name else "archive"))
        print(f"\n== {folder}/{path.name} : {len(df)} lignes")
        print(f"   dates : {df['acq_date'].min().date()} -> {df['acq_date'].max().date()}")
        print(f"   satellites : {df['satellite'].value_counts().to_dict()}")
        print(f"   confiance (0 bas, 1 nominal, 2 haut) : {df['conf_level'].value_counts().sort_index().to_dict()}")
        types = pd.to_numeric(df["type"], errors="coerce").value_counts(dropna=False).to_dict()
        print(f"   type : {types}")
        print(f"   acq_time exemples : {df['acq_time'].head(3).tolist()}")
        days = pd.Series(sorted(df["acq_date"].dt.date.unique()))
        gaps = [(a, b) for a, b in zip(days[:-1], days[1:]) if (b - a).days > 3]
        print(f"   trous de plus de 3 jours : {gaps[:5]}")
