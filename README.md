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

## Files

- `index.html` — the dashboard UI
- `data.js` — index data and weights
- `server.py` — live backend (news + ACLED timeline, cached)
- `acled-api/` — ACLED helper script
