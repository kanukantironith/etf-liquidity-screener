# Deploying the frontend

## Platform choice

**Render Static Site.** Two reasons:

- The app is pure static files (`web/`, 448 KB). `support.js` pulls React from
  unpkg at runtime and `data/etf-data.js` reads JSON from the same origin — no
  server, no build, no environment variables.
- Render's Static Site type is **free permanently** (100 GB bandwidth/month,
  free TLS, custom domains). It has no paid plan to accidentally land on.

**Railway is not an option under a free-tier-only constraint.** Railway
discontinued its free tier; what remains is a one-time trial credit, after which
the service requires a paid plan. There is no free static-site product there.

## What is already done

- `web/` contains the complete, verified site.
- [`render.yaml`](render.yaml) — Blueprint pinned to `runtime: static`,
  `staticPublishPath: ./web`, no-op build. Static Sites take no `plan:` field,
  so this cannot provision anything billable.
- Local git repo initialized, branch `main`, everything committed.

## Remaining steps (these need your accounts)

Render deploys static sites from a Git repo — it cannot take a local directory
upload — so the code has to reach GitHub first.

**1. Create an empty GitHub repo** (private is fine; Render's free tier reads
private repos through the GitHub app). Do not initialize it with a README.

**2. Push:**

```bash
git remote add origin git@github.com:<you>/etf-screener.git && git push -u origin main
```

**3. In the Render dashboard** → **New** → **Blueprint** → connect the repo.
Render reads `render.yaml` and proposes one service, `illiquidity-illusion`,
of type Static Site. Confirm that the plan shows **Free** before applying.

**4.** First build takes about a minute. The URL will be
`https://illiquidity-illusion.onrender.com` (or a suffixed variant if the name
is taken).

## After deploy

- Static Sites do not spin down. The cold-start delay that affects Render's free
  *web services* does not apply here.
- Pushes to `main` auto-deploy.
- The site is publicly reachable by URL — there is no auth in front of it.

## Refreshing the data

The two JSON snapshots under `web/uploads/` are static. To update them, re-run
`single_etf_screener.py` / `market_surface_scan.py`, convert their CSV output to
the JSON shapes those files use, commit, and push. Going live instead means
replacing the fetcher bodies in `web/data/etf-data.js` — see `web/README.md`.
