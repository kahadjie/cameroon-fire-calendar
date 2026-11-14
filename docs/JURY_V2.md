# Cameroon fire season check (branch `jury-v2`)

Team WESH: Kenmoe Kahadjie Felix. NASA Space Apps Challenge 2026, "Harmonizing MODIS and VIIRS fire
hotspots". Every figure below is produced by `analysis.py` from local NASA FIRMS files and stored in
`jury.json`; nothing here is a promise about a future season.

## Problem

Is the last fire season in Cameroon unusual? MODIS and VIIRS cannot be compared directly (VIIRS records
about 4.3 times more detections), detections cluster in time, and one extreme year distorts a mean.

## Answer (latest complete season, 2025-26, November to March)

135,062 Suomi NPP detections: the lowest of 14 seasons since 2012-13 and 21.7% below the median of the
other seasons (172,490); 95% day-bootstrap range 119,488 to 152,279. Robust z = −1.38 (counts) and
−1.55 (fire radiative power): **not flagged** at the threshold ±3.5 fixed in advance, nor at ±2.0.
So: a low season, within the normal year-to-year range of the last 14 seasons.

## Method

| Element | Formula / rule | Source |
|---|---|---|
| Main series | Suomi NPP VIIRS 375 m, nominal and high confidence, archive type 0, final months only | as on `main` |
| Season | November to March (the five months with the highest 2012-2025 medians) | data |
| Robust z | (x − median) / (1.4826 × MAD), each value against the *other* seasons or years | Iglewicz & Hoaglin 1993 |
| Signal | abs(z) ≥ 3.5, fixed before computing results | Iglewicz & Hoaglin 1993 |
| Season interval | 2,000 bootstrap resamples of days within each month, seed 42 | Efron & Tibshirani 1993 |
| Monthly interval | Poisson 95%, Wilson–Hilferty form of the exact interval | Breslow & Day 1987 |
| FRP | sum of fire radiative power (MW) over detections | FIRMS attribute `frp` |
| Pixel geometry | area = scan × track (km²); near nadir = scan ≤ 1.5 × nadir size | FIRMS attributes `scan`, `track` |
| Overpass time | local solar time = UTC + longitude / 15; daytime Suomi NPP vs daytime Aqua | — |

**Assumptions, stated plainly**
- Summed FRP is an index of intensity at overpass time, **not** an energy: converting it to energy (MJ)
  would need the fire duration between overpasses, which the data do not give.
- "Near nadir" (1.5 × the nadir pixel size) is a chosen threshold, not a standard.
- The season (November to March) was chosen from the medians of the same data.
- Days without any detection are counted as zero (FIRMS lists fires only; a missing day and a day
  without fire look the same).

## Validation (measured)

- **Counts match `main`**: the analysis stops if any monthly Suomi NPP count differs from `aggregats.json`.
- **Left-out years (2013-2025, 13 full years)**, error of the predicted Suomi NPP / MODIS ratio:

| Ratio | Year-to-year spread (CV) | Error, one constant | Error, adjacent years | Error, trend |
|---|---|---|---|---|
| Counts, all passes | 5.1% | 4.49% | 3.25% | 3.12% |
| FRP, all passes | 7.0% | 5.57% | 4.15% | 3.82% |
| Counts, same hour (daytime Aqua) | 3.2% | 3.03% | 3.80% | 3.25% |
| FRP, same hour | 4.5% | 3.43% | 5.46% | 3.75% |
| Counts, same hour, near nadir | 4.8% | 4.10% | 3.94% | 4.31% |
| FRP, same hour, near nadir | 3.6% | **2.63%** | 3.88% | 3.16% |

  Comparing at the same hour and near nadir on fire power gives the steadiest ratio; counts on all
  passes the least steady. This is measured on Cameroon only.
- **Overpass drift (measured)**: daytime Suomi NPP stays between 13:22 and 13:29; Aqua moves from 13:31 (2012) to
  15:05 (2026); Terra from 10:37 to 09:07.
- **Pixel geometry (measured)**: mean MODIS pixel 1.836 km² (1 km² at nadir, up to 9.6 km²), Suomi NPP
  0.218 km² (0.141 at nadir); 27% of MODIS detections and 10% of Suomi NPP detections are beyond
  1.5 × their nadir size.
- **Overdispersion (measured)**: the variance of daily counts is about 315 times their mean (median over
  season months), so Poisson intervals are far too narrow for seasons; the bootstrap is used instead.
- **Threshold sensitivity**: months flagged out of 177: 20 (2.0), 14 (2.5), 8 (3.0), 5 (3.5), 4 (4.0), 1
  (5.0); seasons flagged: 0 of 14 at every threshold; the 2025-26 season is never flagged.
- **Independent satellite**: NOAA-20 puts the season on the same side of its median as Suomi NPP in 6 of
  8 seasons (2018-19 to 2025-26). Its baseline has only 7 other seasons, so its z-scores are fragile.

## Limits

Detections are not burned area; clouds hide fires; Suomi NPP near-real-time data end on 2 November 2026
and provisional months are never used in the answer; results are for Cameroon only; the FRP and
geometry comparisons have not been tested on other countries.
