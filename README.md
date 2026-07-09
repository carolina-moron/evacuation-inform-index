# Evacuation Inform Index (EII)

A composite index for assessing evacuation conditions, with preliminary weights
synthesised from **INFORM**, **ACLED** and **FSI** logic — to be validated by
AHP expert surveys.

**🔗 Live site:** https://ethical-tech-colab.github.io/evacuation-inform-index-carolina/

## Overview

The index scores three weighted dimensions on a 1–5 scale:

- **Impact** (20%)
- **Conditions** (50%)
- **Complexity** (30%)

It is fed by a set of open data sources (see the *Feeds* section of the site),
with a live backend that pulls news and an ACLED conflict timeline.

## Running locally

```bash
cp .env.example .env   # add your API keys
python server.py
```

Then open `index.html` (or the URL the server prints).

## Hosted site (static snapshot)

GitHub Pages serves static files only, so it can't run `server.py`. To make the
hosted site behave like the live app, the backend responses are **baked into
static JSON** and committed under `snapshot/`.

The frontend tries the live `/api/detail` endpoint first (works when you run
`server.py` locally) and falls back to `snapshot/detail/<slug>.json` when no
backend is present — so clicking a crisis on GitHub Pages still shows the Tavily
news and ACLED timeline, with a "📸 Snapshot" note indicating the data is frozen
at capture time.

To refresh the snapshot (re-runs the real Tavily + ACLED calls, needs a
populated `.env`):

```bash
python3 snapshot.py            # fill in missing crises (resumable)
python3 snapshot.py --force    # regenerate all 104 crises
git add snapshot && git commit -m "Refresh snapshot" && git push
```

## Satellite damage assessment (Microsoft HASTE)

The Map tab can overlay AI **building/route damage maps** from
[Microsoft HASTE](https://aka.ms/HASTE) + Planet. HASTE is self-hosted (no public
API), so you run it and paste its damage-layer tile URL into EII — see
[HASTE_SETUP.md](HASTE_SETUP.md). Until connected, the overlay is empty (nothing
is faked). Damage feeds the CERAI lens: infrastructure loss raises endangerment,
blocked routes lower feasibility.

## Files

- `index.html` — the dashboard UI
- `data.js` — index data and weights
- `server.py` — live backend (news + ACLED timeline, cached)
- `snapshot.py` — bakes the static snapshot the hosted site falls back to
- `snapshot/` — pre-generated per-crisis JSON served on GitHub Pages
- `acled-api/` — ACLED helper script
- `HASTE_SETUP.md` — how to run Microsoft HASTE and overlay its damage tiles
