# Frontend — The Illiquidity Illusion

Imported from the Claude Design project *Interactive ETF prototype frontend*
(`ee4011e7-9a93-469c-81ab-69c50c64b15c`).

```
Illiquidity Illusion.dc.html   the app (x-dc template + component script)
support.js                     dc-runtime; pulls React/ReactDOM/Babel from unpkg
data/etf-data.js               the only data-access module
uploads/etf_lookthrough.json   look-through snapshot (single_etf_screener.py output)
uploads/etf_surface_scan.json  surface-scan snapshot (market_surface_scan.py output)
index.html                     redirect to the app
```

## Run

Needs a real HTTP server — the app uses `import()` and `fetch`, which `file://`
blocks.

```bash
python3 -m http.server 8127 --directory web
```

Then open http://localhost:8127.

## Going live

`data/etf-data.js` is the single seam. It currently reads the static JSON in
`uploads/`; swap the fetcher bodies for calls to the URLs already sketched in
its `ENDPOINTS` export and keep the exported signatures. Nothing else changes.

The JSON snapshots correspond to the Python pipeline in the repo root:
`single_etf_screener.py` produces the per-ETF look-through, `market_surface_scan.py`
the market-wide surface scan.

## Note

The browser console logs a handful of `Expected length, "{{ t.x1 }}"` SVG
attribute errors on load. That is the browser parsing the uncompiled `<x-dc>`
template before the runtime takes over; it is harmless and not a runtime failure.
