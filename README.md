# Cameroon fire calendar: MODIS and VIIRS harmonized

NASA Space Apps Challenge 2026, challenge "Harmonizing MODIS and VIIRS fire hotspots".

**Live app: https://kahadjie.github.io/cameroon-fire-calendar/**

**Team WESH MIS** (WorldWide Emergent Smart Hub), Cameroon: Kenmoe Kahadjie Felix (sole member).

![The application: month × year anomaly calendar, map and calibration table](docs/screenshot.png)

A static web application (one page, `index.html`, Leaflet from a CDN, no server) that shows, for all of
Cameroon, a month × year calendar of fire hotspots from 2012 to 2026. The main view is each month's
**anomaly** against its **historical median** (2012 to 2025). A map shows detections per 0.5° cell for
the chosen year and months. The values shown can be exported as CSV.

## Open the application

Double-click `index.html` (the data are in `donnees.js`, no server needed). Leaflet and the base map
come from the internet; without a connection, the calendar and the CSV export still work. Alternative:
`python -m http.server 8000`, then open http://localhost:8000.

## NASA data

All fire data come from **NASA FIRMS** (Fire Information for Resource Management System),
https://firms.modaps.eosdis.nasa.gov, country downloads for Cameroon
(https://firms.modaps.eosdis.nasa.gov/download/):

| Product | FIRMS download | Satellites | Archive | Near real-time (NRT) |
|---|---|---|---|---|
| MODIS Collection 6.1, 1 km | `DL_FIRE_M-C61` | Aqua, Terra | 2012-01-20 → 2026-08-29 | 2026-09-09 → 2026-11-13 |
| VIIRS 375 m, Collection 2 | `DL_FIRE_SV-C2` | Suomi NPP (`SNPP`) | 2012-01-20 → 2026-07-31 | 2026-08-01 → 2026-11-02 |
| VIIRS 375 m, Collection 2 | `DL_FIRE_J1V-C2` | NOAA-20 (`N20`) | 2018-04-01 → 2026-07-31 | 2026-08-01 → 2026-11-13 |
| VIIRS 375 m, Collection 2 | `DL_FIRE_J2V-C2` | NOAA-21 (`N21`) | 2023-03-01 → 2026-07-31 | 2026-08-01 → 2026-11-13 |

Coverage dates are those found in the files by `inspect_archives.py`. Citation (also shown in the
application):

> We acknowledge the use of data and imagery from LANCE FIRMS operated by NASA's Earth Science Data and
> Information System (ESDIS) with funding provided by NASA Headquarters.

Base map: © OpenStreetMap contributors (ODbL). No other data source is used.

## Decisions

1. **Main series: S-NPP alone; sensors are never added together.** S-NPP, NOAA-20 and NOAA-21 often
   pass over the same fire a few minutes apart, so adding their detections would count the same fire
   two or three times. Instead of a space-time de-duplication (fragile and slow), S-NPP is fixed as the
   main series: it is the only VIIRS series covering 2012 to 2026. NOAA-20 and NOAA-21 are used **only
   to cross-check** that series (see Key results).
2. **Nominal and high confidence, on a common scale.** VIIRS gives `l`/`n`/`h`. MODIS gives 0-100,
   converted with the FIRMS thresholds: low < 30, nominal 30-79, high ≥ 80. Low-confidence detections
   are dropped for both sensors.
3. **Archive: `type = 0` only** (presumed vegetation fire), which removes volcanoes, static land sources
   and offshore detections (gas flares). NRT files have no such column, so they keep everything. Effect
   measured on the S-NPP archive: 0.42% of detections.
4. **MODIS → S-NPP-equivalent calibration per year, never a single constant.** For each year:
   factor = S-NPP detections / MODIS detections, over months that are complete for both sensors and
   not provisional. A year without overlap would take the nearest year's factor (and say so).
5. **Incomplete months are left empty, not extrapolated.** A month has a value for a sensor only if it
   is covered from its first to its last day: January 2012 (data start on the 20th), November 2026 for
   S-NPP (NRT ends on 2 November), August and September 2026 for MODIS (gap).
6. **Historical median** of each calendar month over 2012-2025 (167 reference months, excluding
   incomplete and provisional months). Anomaly = (value − median) / median × 100.
7. **Provisional data**: every month containing NRT data, plus the last 5 months (July to November
   2026). They are hatched and announced in a banner; 2026 is marked incomplete.
8. **"Cividis" palette** (8 classes), readable with color vision deficiency and ordered in grayscale.
   Checked by `check_palette.py` (gray levels 30 to 224, at least 22 between two classes) and by a
   grayscale screenshot of the page. Every cell also shows its value as a number.

## Limitations

- **MODIS gap from 30 August to 8 September 2026** (no data in either the archive or NRT): August and
  September 2026 have no MODIS value. Shown in the application. The S-NPP series is not affected.
- **The 2026 factor is 5.942, from 6 months only** (January to June). It is well outside the 2012-2025
  range (3.951 to 4.693), so read it with caution (incomplete year; possibly the end of life of the
  Terra satellite). The 2026 MODIS equivalent depends on it.
- **Rainy season** (June to September): the median drops below 500 detections (104 in September), so a
  few dozen detections give ±70%. The application says so in the month details.
- **Days without detections**: FIRMS files list fires only, so a day without any detection cannot be
  told apart from a day without data. The archives have breaks of more than 3 days: MODIS 134 (121
  starting between June and September), S-NPP 24 (20 between June and September), mostly the quiet
  rainy season. Two S-NPP breaks fall in the fire season and may be data outages: **2 to 7 November
  2024** and **9 to 13 March 2026**. Those months are kept as complete; their counts may be slightly
  low. Only the 2026 MODIS gap above is a confirmed outage.
- A detection is not a fire: a large fire gives several pixels, a small fire under clouds gives none.
  Counts measure detected activity, not burned area.
- NRT files have no `type` column: NRT months may include a few static sources (about 0.4% based on
  the archive).
- Geolocation errors at the country border (FIRMS country window) are not corrected.

## Key results

All figures below come from `aggregats.json`.

- **S-NPP/MODIS factor**: 4.008 (2012) to 4.693 (2025); mean 4.30, standard deviation 0.23 over the
  14 years 2012-2025 (2012 from 11 months, the others from 12); minimum 3.951 (2015). It **rises** after 2020 (4.120 → 4.693), so a single
  constant would bias any comparison between the two periods. Hence one factor per year.
- **Cross-check of the main series** over the reference months: NOAA-20 correlation 0.999 with S-NPP
  (93 months), ratio 0.996; NOAA-21 correlation 0.998 (34 months), ratio 0.961. The S-NPP series is
  stable and consistent with the two other VIIRS sensors, without double counting.
- **Seasonality**: the fire season runs from November to March (medians: January 52,007, February
  55,432, December 42,406.5 detections); July to September each have a median below 250.
- **Annual S-NPP totals** (complete years 2013-2025): from 153,503 (2013) to 208,332 (2020), the
  maximum; 189,714 in 2025.
- **Notable months**: November 2023 at −72.9% (2,847 detections against a median of 10,510.5), a
  strong anomaly in the fire season itself.
- **2026**: January (−24.9%) and February (−32.2%), the most active months, were below their median;
  March (+41.6%) above. July to November 2026 are provisional.

## Reproduce

Requirements: Python 3.13 (pandas has no release for Python 3.15 yet) and pandas.

```
pip install pandas
python test_harmonize.py      # 10 tests on synthetic data
python inspect_archives.py    # checks the real files in data/ (dates, satellites, confidence, gaps)
python harmonize.py           # writes aggregats.json, grille.json and donnees.js
python check_palette.py       # grayscale palette check
```

`data/` (raw FIRMS archives, not versioned): download the "Country: Cameroon" archives for MODIS C6.1
and VIIRS S-NPP, NOAA-20, NOAA-21 from https://firms.modaps.eosdis.nasa.gov/download/ and extract them
into `data/modis`, `data/snpp`, `data/noaa20`, `data/noaa21`. No API key is used.

## Files

| File | Role |
|---|---|
| `index.html` | the application (map, calendar, CSV export) |
| `donnees.js` | aggregates loaded by the page (same content as the two JSON files) |
| `aggregats.json` | month × year: S-NPP, MODIS, S-NPP equivalent, factor, NOAA-20/21, median, anomaly, provisional flag, completeness |
| `grille.json` | S-NPP detections per 0.5° cell and per month (map); no individual detections |
| `harmonize.py` | loading, common confidence scale, filters, calibration, medians, anomalies |
| `test_harmonize.py` | unit tests |
| `inspect_archives.py` | inspection of the real files |
| `check_palette.py` | grayscale palette check |

The repository contains only aggregates: no raw detection, no key, no personal data.

## Use of AI

This project was built with the help of **Claude** (Anthropic), an AI assistant, working under the
direction and review of the team (Kenmoe Kahadjie Felix):

- **Code**: Claude wrote `harmonize.py`, `test_harmonize.py`, `inspect_archives.py`,
  `check_palette.py` and `index.html` (layout, calendar, map, CSV export), from a written plan and the
  team's decisions (S-NPP as main series, per-year calibration, confidence filter, flagged gaps).
- **Data checks**: Claude ran the tests and the inspection of the real FIRMS files, and compared the
  figures in this README with `aggregats.json`.
- **Documentation**: Claude drafted this README, the English translation of the interface, the
  submission description and the demo outline.

The data themselves are NASA FIRMS data, unchanged; no AI-generated data, image or figure is presented
as observed data. The team reviewed and approved the choices and the results.

## Data license

NASA FIRMS data: free to use with the citation above. OpenStreetMap base map: ODbL.
