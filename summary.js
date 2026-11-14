// Summary sentences generated from the monthly aggregates only (no figure written by hand).
// Pure: same input, same text. Used by index.html and tested by tests/summary_test.html.
(function (root) {
  "use strict";
  const LONG = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const fmtDate = d => new Date(d + "T00:00:00Z").toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const pct = v => Math.round(v) === 0 ? "at" : `${Math.abs(Math.round(v))}% ${v > 0 ? "above" : "below"}`;

  /**
   * lead: the latest FINAL month of the main series (complete and not provisional), and how many final
   * months of that year were above usual. provisional: the latest provisional month, shown apart.
   * months: [{year, month, anomaly_pct, provisional}], in time order; snppEnd: "YYYY-MM-DD".
   */
  function summaryParts(months, snppEnd) {
    const withValue = months.filter(r => r.anomaly_pct != null);
    const finals = withValue.filter(r => !r.provisional);
    const last = finals[finals.length - 1] || null;
    const provs = withValue.filter(r => r.provisional);
    const prov = provs[provs.length - 1] || null;
    let lead = "No final month of the main series yet.";
    if (last) {
      const year = finals.filter(r => r.year === last.year);
      const above = year.filter(r => r.anomaly_pct > 0).length;
      lead = `Latest final month of the main series: ${LONG[last.month - 1]} ${last.year}, ${pct(last.anomaly_pct)} its usual level. ` +
        `In ${last.year}, ${above} of ${year.length} final months were above usual.`;
    }
    let provisional = null;
    if (prov && (!last || prov.year * 12 + prov.month > last.year * 12 + last.month)) {
      provisional = `Provisional: ${LONG[prov.month - 1]} ${prov.year} reads ${pct(prov.anomaly_pct)} its usual level, from near real-time data that may still change.`;
    }
    const end = snppEnd ? `Main series (Suomi NPP) data end on ${fmtDate(snppEnd)}.` : "";
    return { lead, provisional, end };
  }

  root.FireSummary = { summaryParts, fmtDate };
})(typeof window !== "undefined" ? window : this);
