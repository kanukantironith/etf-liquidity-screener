/**
 * etf-data.js — THE SINGLE DATA ACCESS MODULE.
 *
 * Every number rendered by the UI comes through this file and nothing else.
 * Today it reads static JSON snapshots from /uploads. To go live, replace the
 * bodies of the fetchers below with API calls (URLs already sketched in
 * ENDPOINTS) and leave the exported function signatures untouched — no other
 * file needs to change.
 */

const SOURCES = {
  lookthrough: 'uploads/etf_lookthrough.json',
  surfaceScan: 'uploads/etf_surface_scan.json',
};

// Live backend contract, for the swap. Not called in this build.
export const ENDPOINTS = {
  lookthrough: (t) => `/api/etf/${t}`,
  status: (t) => `/api/etf/${t}/status`,
  scan: '/api/scan',
  scanHistory: (t) => `/api/scan/history/${t}`,
  universeSearch: (q) => `/api/universe/search?q=${encodeURIComponent(q)}`,
  health: '/api/health',
};

const cache = {};
async function readSource(key) {
  if (!cache[key]) {
    cache[key] = fetch(SOURCES[key]).then((r) => {
      if (!r.ok) throw new Error(`${key}: ${r.status}`);
      return r.json();
    });
  }
  return cache[key];
}

/** Tickers with a look-through analysis available in the current source. */
export async function listLookthroughTickers() {
  return Object.keys(await readSource('lookthrough'));
}

/**
 * Full look-through analysis for one ETF, exactly as produced by the pipeline.
 * Returns null when the source has no analysis for that ticker.
 */
export async function getLookthrough(ticker) {
  const all = await readSource('lookthrough');
  return all[String(ticker).toUpperCase()] || null;
}

/** Latest completed surface scan: { generated_at, universe_scanned, universe_usable, weights, rows }. */
export async function getSurfaceScan() {
  return readSource('surfaceScan');
}

/** Surface-risk time series for sparklines. Not present in the snapshot. */
export async function getScanHistory() {
  return null;
}

/** Typeahead across everything the current source knows about. */
export async function searchUniverse(q) {
  const query = String(q || '').trim().toUpperCase();
  const [look, scan] = await Promise.all([
    readSource('lookthrough'),
    readSource('surfaceScan'),
  ]);
  const deep = new Set(Object.keys(look));
  const seen = new Set();
  const out = [];
  const push = (ticker) => {
    if (seen.has(ticker)) return;
    if (query && !ticker.startsWith(query)) return;
    seen.add(ticker);
    out.push({ ticker, lookthrough: deep.has(ticker) });
  };
  Object.keys(look).forEach(push);
  scan.rows.forEach((r) => push(r.ticker));
  return out.slice(0, 12);
}
