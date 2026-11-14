# Space Apps form: one answer per field, ready to paste

Field names follow the Space Apps project form; if a label differs on the day, paste the closest
block. Every figure below is the one shown by the page and the README on 14 November 2026. Check the
summary sentence on the live page before pasting, it is generated from the data.

## Project name

Cameroon Fire Calendar: MODIS and VIIRS harmonized

## Team

WESH — Kenmoe Kahadjie Felix (Cameroon).

## Challenge

Harmonizing MODIS and VIIRS fire hotspots.

## High-level project summary

NASA has watched fires from space with MODIS since 2000 and with the sharper VIIRS sensors since
2012; VIIRS sees about four times more hotspots, so their counts cannot be compared directly. We
built a month × year calendar of fires across Cameroon, 2012 to 2 November 2026, on one scale: Suomi
NPP is the main series and MODIS is rescaled with one factor per year. The page opens on one
generated sentence that says whether the latest final month is above or below its usual level; one
click gives the map, and every value shown exports to CSV. Forest services, researchers and
journalists can see in seconds whether this season is unusual, on a phone and in grayscale.

## Link to project demo (30 seconds)

[paste the video link]

## Link to final project

https://kahadjie.github.io/cameroon-fire-calendar/
Code: https://github.com/kahadjie/cameroon-fire-calendar

## Detailed project description

**What it does.** A static web page shows, for all of Cameroon, a calendar of every month from 2012
to 2 November 2026 (the last day Suomi NPP delivers near-real-time data). Each cell is colored by how
far the month is from its usual level, the 2012-2025 median for that calendar month, and shows the
value as a number. A map shows detections per 0.5° cell for the chosen months, a "Compare two
years" view puts two seasons side by side, and the values can be downloaded as CSV with documented
columns. Technical words are explained on the page.

**How it works.** NASA FIRMS hotspots, MODIS Collection 6.1 and VIIRS 375 m (Suomi NPP, NOAA-20,
NOAA-21); nominal and high confidence only, on a common scale; presumed vegetation fires only in the
archive. Suomi NPP is the main series, so no fire is counted twice; NOAA-20 and NOAA-21 only
cross-check it (correlation 0.999 and 0.998 with the main series). MODIS is rescaled to a Suomi NPP
equivalent with one factor per year, from 4.008 in 2012 to 4.693 in 2025, never a single constant,
because the factor rises after 2020. Incomplete months are left empty, not extrapolated; months with
near-real-time data are hatched as provisional.

**How we checked it.** Each full year 2013-2025 was left out in turn and its factor predicted from
the other years: 4.49% average error with one constant factor, 2.48% when MODIS is matched with Aqua
only (same time of day as VIIRS). The test is reproducible with `python validate.py` in the
repository. Unit tests cover the confidence scale, the filters, the per-year factor and the medians.

**Limitations.** Detections are not burned area. Low-season percentages are unstable (a few dozen
detections give ±70% in September). July to November 2026 are provisional. The downloaded files
contain no MODIS detection from 30 August to 8 September 2026; the cause is not verified, and the
main series is not affected. The 2026 factor rests on six months.

**Why it matters.** Anyone can answer "is this fire season unusual?" from one consistent series
instead of two incompatible ones, on a phone, in grayscale, and offline once the files are
downloaded.

## NASA data

NASA FIRMS (Fire Information for Resource Management System), country downloads for Cameroon:
MODIS Collection 6.1 (Aqua, Terra), VIIRS 375 m Collection 2 (Suomi NPP, NOAA-20, NOAA-21), archive
and near-real-time files, 2012 to November 2026. We used the detection date, position, satellite,
confidence and type columns. "We acknowledge the use of data and imagery from LANCE FIRMS operated
by NASA's Earth Science Data and Information System (ESDIS) with funding provided by NASA
Headquarters."

## Space agency partner and other data

None. Base map: © OpenStreetMap contributors (ODbL), used only for the map background.

## Use of artificial intelligence

This project was built with an AI assistant (Claude, by Anthropic). It helped write the code and the
documentation. The team chose the method, checked the results against the NASA FIRMS data, and
decided what is published. No AI-generated data, image or figure is presented as observed data.

## References

- NASA FIRMS: https://firms.modaps.eosdis.nasa.gov
- FIRMS country downloads: https://firms.modaps.eosdis.nasa.gov/download/
- Leaflet (map library) and OpenStreetMap (base map).
