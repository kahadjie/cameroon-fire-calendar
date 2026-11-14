# Demo plan

App: https://kahadjie.github.io/cameroon-fire-calendar/ · Team WESH:
Kenmoe Kahadjie Felix. The figures below are those the page computes from the published data; check
them on the page on the day of recording (the summary sentence is generated, not written by hand).

## 30-second script (one sentence per screen)

1. **Top of the page**: "NASA's two fire sensors, MODIS and VIIRS, count fires differently, so nobody
   can read one consistent fire history for Cameroon."
2. **Summary sentence**: "Our calendar puts them on one scale: the latest final month of the main
   series, June 2026, was 65% above its usual level — main series data end on 2 November 2026."
3. **Calendar**: "Every month since 2012, colored by how far it is from usual; one click gives the map."
4. **Validation line**: "We tested the rescaling on years left out: 4.49% error with one constant
   factor, 2.48% when MODIS is matched with Aqua only."

## 2-minute script (one sentence per screen)

1. **Title and lead** (0:00): "Is this fire season unusual? That is the question forest services,
   researchers and journalists in Cameroon ask, and NASA has the data to answer it."
2. **The problem** (0:15): "But MODIS and VIIRS see fires differently: VIIRS records about four times
   more detections, so their counts cannot be compared."
3. **Summary sentence** (0:30): "The page answers first: the latest final month of the main series,
   Suomi NPP, is June 2026, 65% above usual; October 2026 reads 90% above but is provisional, so it is
   shown apart; the main series ends on 2 November 2026."
4. **Calendar** (0:45): "Each cell is a month since 2012; dark is below usual, yellow above; hatched
   months are provisional; hover any underlined word for an explanation."
5. **Show the most active month** (1:00): "One button jumps to the most active month on record,
   February 2023, and the map shows where the fires were."
6. **Compare two years** (1:15): "Side by side, 2025 and 2026, month by month."
7. **Rescaling table and cross-check** (1:30): "MODIS is rescaled year by year — the factor rises from
   4.0 to 4.7 — and two other VIIRS satellites confirm the main series, correlation 0.999."
8. **Validation line** (1:45): "On years left out, the error is 4.49% with one constant factor and 2.48%
   when MODIS is matched with Aqua only; we measured it, we have not applied it yet. Download the values
   as CSV, and see the method on GitHub."

## 7 slides

1. **Title**: Cameroon Fire Calendar — MODIS and VIIRS harmonized. Team WESH, Kenmoe Kahadjie Felix,
   NASA Space Apps Challenge 2026, challenge "Harmonizing MODIS and VIIRS fire hotspots". Visual:
   `docs/screenshot.png`.
2. **The problem**: two NASA sensors, about four times more VIIRS detections, the same fire seen by
   several satellites; no consistent series to answer "is this month unusual?".
3. **NASA data used**: NASA FIRMS, Cameroon, archive and near real-time; MODIS C6.1 (Aqua, Terra),
   VIIRS 375 m (Suomi NPP, NOAA-20, NOAA-21), 2012 to 2 November 2026 for the main series (Suomi NPP);
   NOAA-20 and NOAA-21 to 14 November 2026. Citation: LANCE FIRMS, NASA ESDIS.
4. **Method**: Suomi NPP as main series (no double counting); confidence nominal and high; MODIS
   rescaled with one factor per year (4.008 in 2012 to 4.693 in 2025); usual level = 2012-2025 median.
5. **User experience** (live): summary sentence (latest final month; provisional month apart), calendar, most active month, map, compare two years,
   CSV download; works on a phone (390 px) and in grayscale.
6. **Validity**: cross-check with NOAA-20/21 (correlation 0.999 / 0.998); held-out test 4.49% (one
   constant factor) vs 2.48% (Aqua only, measured, not applied); provisional months hatched; low-season
   percentages flagged as unstable; detections are not burned area.
7. **Impact and next steps**: who uses it (forest services, researchers, journalists); next: any
   country (development branch), automatic updates, Aqua-only calibration if validated. Use of AI:
   Claude (Anthropic) wrote code and documentation under the team's review.
