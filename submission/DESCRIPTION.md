# Submission description (about 200 words)

**Cameroon Fire Calendar: MODIS and VIIRS harmonized**
Team WESH: Kenmoe Kahadjie Felix.
App: https://kahadjie.github.io/cameroon-fire-calendar/ · Code: https://github.com/kahadjie/cameroon-fire-calendar

**The problem.** NASA has watched fires from space with MODIS since 2000 and with the sharper VIIRS
sensors since 2012; VIIRS sees about four times more hotspots. Their counts cannot be compared
directly, and anyone who wants to know whether a month is unusually active has no single, consistent
series to read.

**Our answer.** A month × year calendar of fires across Cameroon, from 2012 to 2 November 2026, the last
day Suomi NPP delivers near-real-time data. Each cell says how far the month is from its usual level
(the 2012-2025 median for that month); a map shows where, and every value shown exports to CSV.

**Method.** NASA FIRMS hotspots, MODIS C6.1 and VIIRS 375 m (Suomi NPP, NOAA-20, NOAA-21); nominal and
high confidence; presumed vegetation fires only. Suomi NPP is the main series, so no fire is counted
twice; NOAA-20 and NOAA-21 cross-check it (correlation 0.999 and 0.998). MODIS is rescaled with one
factor per year (4.008 in 2012 to 4.693 in 2025). Held-out test: 4.49% error with one constant
factor, 2.48% with Aqua only (measured, not applied to the published series).

**Impact.** Forest services, researchers and journalists can see in seconds whether this season is
unusual, on a phone and in grayscale.

**Limitations.** Provisional months (July to November 2026) are flagged; low-season percentages are
unstable; detections are not burned area.

**Use of AI**

This project was built with an AI assistant (Claude, by Anthropic). It helped write the code and the documentation. The team chose the method, checked the results against the NASA FIRMS data, and decided what is published. No AI-generated data, image or figure is presented as observed data.
