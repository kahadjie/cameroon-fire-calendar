# Demo plan: 7 slides (English)

Screenshots: `docs/screenshot.png`, or take them from the live app in a browser (desktop and phone).

## Slide 1: Title
- **Cameroon Fire Calendar: MODIS and VIIRS harmonized**
- Team: WESH MIS (WorldWide Emergent Smart Hub). Member: Kenmoe Kahadjie Felix.
- Live app: https://kahadjie.github.io/cameroon-fire-calendar/
- NASA Space Apps Challenge 2026, challenge "Harmonizing MODIS and VIIRS fire hotspots".
- Visual: the calendar in anomaly view.

## Slide 2: The problem
- Two NASA fire records: MODIS (since 2000, 1 km) and VIIRS (since 2012, 375 m).
- VIIRS sees about 4 to 5 times more hotspots than MODIS: raw counts cannot be compared.
- Several VIIRS satellites see the same fire: adding them counts it twice.
- Question for users: "Was this month a bad fire month for Cameroon?"

## Slide 3: NASA data used
- NASA FIRMS, Cameroon country downloads, archive + near real-time:
  MODIS C6.1 (Aqua, Terra), VIIRS 375 m S-NPP, NOAA-20, NOAA-21.
- 2012-01-20 to 2026-11-13, about 6 million detections in total.
- Citation: LANCE FIRMS, NASA ESDIS.

## Slide 4: Our method
- Common confidence scale (nominal and high), presumed vegetation fires only.
- S-NPP = main series; NOAA-20 and NOAA-21 only cross-check it (correlation 0.999 and 0.998).
- MODIS → S-NPP equivalent with one factor per year: 4.008 (2012) to 4.693 (2025).
- Anomaly = month vs its 2012-2025 median.
- Visual: small chart or table of the yearly factor.

## Slide 5: The user experience (live demo)
- Open the page: the calendar shows every month since 2012, colored by anomaly.
- Tap a month: details (S-NPP, median, MODIS equivalent) and the map of that month.
- Choose a year and months: the map sums them; switch the view to counts.
- Export CSV: exactly the values shown.
- Works on a phone (390 px), in grayscale (cividis palette, values written in each cell).
- Visual: desktop screenshot + phone screenshot.

## Slide 6: Honest about the data
- MODIS gap 30 August to 8 September 2026: flagged.
- July to November 2026: provisional (hatched).
- Rainy-season percentages are unstable (few detections).
- Detections are not burned area.

## Slide 7: Results and impact
- Fire season November to March; up to 208,332 S-NPP detections a year (2020).
- November 2023: −72.9% in the middle of the fire season.
- Early 2026: January −24.9%, February −32.2%, March +41.6%.
- Who it helps: forest services, researchers, journalists. Next steps: other countries, burned area.
- Use of AI: Claude (Anthropic) wrote code and documentation under our review.
