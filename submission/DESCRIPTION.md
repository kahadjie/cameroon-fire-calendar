# Description (about 200 words): Cameroon Fire Season Check

**Cameroon Fire Season Check: MODIS and VIIRS, physics and robust statistics**
Team WESH: Kenmoe Kahadjie Felix.
Code: https://github.com/kahadjie/cameroon-fire-calendar/tree/season-check (open `index.html`; not yet
published on GitHub Pages; the submitted monthly calendar is on `main`).

**The problem.** MODIS and VIIRS cannot be compared directly: VIIRS records about four times more
detections. Anyone asking "was this fire season unusual?" has no consistent series and no measure of
uncertainty.

**Our answer.** One question, answered from the data: was Cameroon's last complete fire season unusual
compared with every season since 2012? The 2025-26 season (November to March) was the lowest of 14,
22% below the usual season, but within the normal range (robust z = −1.4; flagged only beyond ±3.5).
The answer is the same for October to April and December to February.

**Method.** NASA FIRMS, MODIS C6.1 and VIIRS 375 m. Robust z-scores (median and median absolute
deviation), a 95% range from resampled days, fire radiative power as an index of fire intensity, pixel
size from the scan angle, and overpass time. Cross-sensor check: the same-hour, near-nadir fire
radiative power ratio (Suomi NPP / Aqua) is predicted within 2.63% on years left out, against 4.49%
for one constant count ratio.

**Limitations.** Detections are not burned area; clouds hide fires; Suomi NPP data end on 2 November
2026 and provisional months are not used.

**Use of AI.** Claude (Anthropic) wrote the code, ran the checks and drafted the documentation under our
direction and review. All data are unchanged NASA FIRMS data.
