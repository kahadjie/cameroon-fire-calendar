"""Inspects the real FIRMS files in data/ (read only). Run: python inspect_archives.py"""

import pandas as pd

import harmonize as h

for folder in ["modis", "snpp", "noaa20", "noaa21"]:
    for path in sorted((h.DATA / folder).glob("*.csv")):
        df = h.normalize_confidence(h.load_firms(path, "nrt" if "_nrt_" in path.name else "archive"))
        print(f"\n== {folder}/{path.name}: {len(df)} rows")
        print(f"   dates: {df['acq_date'].min().date()} -> {df['acq_date'].max().date()}")
        print(f"   satellites: {df['satellite'].value_counts().to_dict()}")
        print(f"   confidence (0 low, 1 nominal, 2 high): {df['conf_level'].value_counts().sort_index().to_dict()}")
        types = pd.to_numeric(df["type"], errors="coerce").value_counts(dropna=False).to_dict()
        print(f"   type: {types}")
        print(f"   acq_time examples: {df['acq_time'].head(3).tolist()}")
        days = pd.Series(sorted(df["acq_date"].dt.date.unique()))
        gaps = [(str(a), str(b)) for a, b in zip(days[:-1], days[1:]) if (b - a).days > 3]
        print(f"   gaps longer than 3 days: {len(gaps)}, first ones: {gaps[:5]}")
