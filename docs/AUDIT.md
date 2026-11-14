# Audit against the judging criteria

> Historical audit of the submitted version (`main`, commit `b249d43`). The "2.48%" below is the figure
> quoted on `main` (Aqua detection counts, day and night, branch `global`); the Fire Season Check on
> branch `season-check` uses one cross-sensor check, 2.63% (see [SEASON_CHECK.md](SEASON_CHECK.md)).

State audited: branch `main`, commit `b249d43` (before the "plain-language summary" changes).
Evidence refers to that commit (`git show b249d43:index.html`). Effort: low (< 1 h), medium (1-3 h),
high (> 3 h). Impact: how much a judge's opinion would change.

## The five most serious issues

1. **No conclusion on the first screen** (Impact, Presentation). The page opens with a method sentence,
   two warning banners and controls (`index.html:58-76`); the answer ("is this season unusual?") has
   to be read from a 177-cell table. Fix: one generated sentence at the top. Effort low, impact high.
2. **An unverified claim is shown as a fact** (Validity). A banner says "no MODIS data from 30 August
   to 8 September 2026" (`index.html:62`) and the README calls it "a confirmed outage"
   (`README.md:72`, `README.md:84`). NASA's own availability service lists MODIS standard data up to
   31 August and near-real-time data from 1 September; the missing days may simply have had no fire.
   Fix: describe what the files contain, say it is not yet checked. Effort low, impact high.
3. **The end date of the main series is not stated** (Validity). The page says "2012 to 2026"
   (`index.html:59`) while Suomi NPP near-real-time data stop on 2 November 2026; a reader may think
   November is covered. Fix: state the date in the summary and the description. Effort low, impact medium.
4. **Jargon without explanation** (Presentation). "Anomaly (% vs median)", "S-NPP detections",
   "MODIS as S-NPP equivalent" (`index.html:67-69`), "median", "hatching" are not explained on screen.
   Fix: plain labels and a short tooltip for each technical term. Effort low, impact high.
5. **The problem is not stated** (Relevance). The subtitle explains the method, not why the work is
   needed (`index.html:59`). Fix: a three-sentence "The problem" section. Effort low, impact medium.

## By criterion

### Impact
- Shows today: a calendar of every month since 2012 for Cameroon, a map per month, CSV export
  (`index.html`, `docs/screenshot.png`).
- A demanding judge would say: who acts on this, and what do they learn in 30 seconds? Nothing on the
  first screen tells a forest officer whether this year is worse than usual.
- Fix: generated conclusion (latest month of the main series vs its usual level, and how many months
  of the year were above it) — low effort, high impact. Name the users in the description — low, medium.

### Creativity
- Shows today: one calendar view; the anomaly-calendar idea and the per-year calibration table.
- A judge would say: a calendar plus a map is a standard dashboard; no way to compare two seasons.
- Fix: a "Compare two years" view (monthly bars side by side) — medium effort, medium impact.
  Multi-country version exists on branch `global` (not merged) — high effort to finish, high impact.

### Validity
- Shows today: per-year calibration table, cross-check with NOAA-20/21 (correlation 0.999 / 0.998),
  provisional months hatched, low-season warning in the month details (`index.html:156`), tests
  (`test_harmonize.py`, 10 tests).
- A judge would contest: the unverified MODIS claim (issue 2); the end date (issue 3); the held-out
  test of the calibration (4.49% with one constant factor, 2.48% with Aqua only, measured on branch
  `global`) is not shown anywhere on `main`; "uncertain months" (dashed outline) exist only on
  `global`, so there is nothing to explain in the `main` legend.
- Fix: one readable validation line under the conclusion — low effort, high impact. Reword the MODIS
  banner — low, high.

### Relevance
- Shows today: NASA FIRMS data only, MODIS and VIIRS both used, the challenge named in the README.
- A judge would contest: the link with the challenge ("harmonizing MODIS and VIIRS") is explained in the
  README but not on the page.
- Fix: "The problem" section on the page — low effort, medium impact.

### Presentation
- Shows today: accessible palette checked in grayscale (`check_palette.py`), 390 px layout without
  horizontal scroll, keyboard Enter on cells, source citation in the footer.
- A judge would contest: jargon (issue 4); several buttons of equal weight and no obvious first action
  (`index.html:65-76`); CSV file name `cameroon_fires_anomaly.csv` does not say what the file holds;
  arrow keys do not move between cells on `main`.
- Offline wording: `README.md:19` is accurate (calendar and CSV export work without a connection once
  the files are on the computer, the map needs one). The submission description said "the calendar
  even works offline", which is true only for the downloaded files, not for the website (no service
  worker on `main`). Fix: say exactly that.
- Fix: plain labels and tooltips — low, high; one primary action "Show the most active month" — low,
  medium; clearer CSV name and documented columns — low, low.

## Not applicable on `main`
- "Choose my country" button and its keyboard behaviour: only on branch `global`.
- Dashed outline for uncertain months: only on branch `global`.
