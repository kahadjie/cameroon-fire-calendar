# Submission description (about 200 words)

**Cameroon Fire Calendar: MODIS and VIIRS harmonized**

Our app shows fire activity across Cameroon as a month × year calendar from 2012 to 2026, so anyone
can see at a glance whether a month burned more or less than usual. Each cell is the month's anomaly
against its 2012-2025 median; a map shows where detections occurred, and every value shown exports to
CSV.

**Method.** We use NASA FIRMS hotspots: MODIS C6.1 and VIIRS 375 m (S-NPP, NOAA-20, NOAA-21). We keep
nominal and high confidence on a common scale and only presumed vegetation fires. S-NPP is the main
series, because adding sensors would count the same fire twice; NOAA-20 and NOAA-21 cross-check it
(correlation 0.999 and 0.998). MODIS is converted to S-NPP equivalent with one factor per year (4.008
in 2012 to 4.693 in 2025), never a single constant.

**Limitations.** A MODIS gap (30 August to 8 September 2026) and provisional months (July to November
2026) are flagged in the app; rainy-season percentages are unstable; detections are not burned area.

**Impact.** Forest services, researchers and journalists get a trustworthy, accessible view of fire
trends, readable on a phone and in grayscale; the calendar even works offline.

**Use of AI.** Claude (Anthropic) wrote the code, ran the checks and drafted the documentation under
our direction and review. All data are unchanged NASA FIRMS data.
