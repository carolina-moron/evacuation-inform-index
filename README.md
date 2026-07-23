# Evacuation Inform Index (EII)

**[Live site](https://ethical-tech-colab.github.io/evacuation-inform-index-carolina/)** ·
**[Research report](EII-Paper.md)** (plain-language, non-technical)

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
with a live backend that pulls news, reported road blockages, and an ACLED
conflict timeline.

## Map

The map opens on **high-resolution Esri satellite imagery** (zoomable to ~1 m,
with a transparent place-name layer on top) and renders crises as a **heatmap**
of the selected metric. Crisis dots stay on top of the heat as click targets —
the heat carries the value, the dots carry the data. A *Display as* control
switches between heatmap, graduated circles, or both.

One caveat is stated on the map itself: a heatmap blurs between points, so the
colour *between* two crises is a rendering effect, not a measurement. EII scores
discrete crises, not a continuous risk surface.

## Road access

Whether the roads out are usable is the most decisive input to evacuation
feasibility, and no open global feed reports it for conflict zones — so the
backend runs a second Tavily search per crisis for road closures, destroyed
bridges, checkpoints and impassable routes, classifies each item
(blocked / damaged / checkpoint / reopened), and turns the weighted counts into
a feasibility penalty in the CERAI lens, capped at 12 points.

The limits are shown in the UI, not buried: the status is keyword-derived from
headlines rather than verified, news prose carries no coordinates so blockages
cannot be drawn as routes on the map, and **zero reports is not evidence that
roads are open**. This doubles the Tavily cost of a detail call to 2 credits;
pass `?roads=0` (or `snapshot.py --no-roads`) to skip it.

## Running locally

```bash
cp .env.example .env   # add your API keys
python server.py
```

Then open `index.html` (or the URL the server prints).

Every key is optional. With none set, the map, scores, weather and satellite
layers still work; only the news and conflict panels go quiet, each naming the
key it is missing. See **[INTEGRATIONS.md](INTEGRATIONS.md)** for every external
service the project calls, why each is called from the server or the browser,
and what to check when one misbehaves.

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
python3 snapshot.py --force    # regenerate all 104 crises (~208 Tavily credits)
python3 snapshot.py --no-roads # skip road access, halving the credit cost
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
- `INTEGRATIONS.md` — every external API, how it is called, and how to debug it
- `HASTE_SETUP.md` — how to run Microsoft HASTE and overlay its damage tiles
- `EII-Paper.md` — plain-language research report on what the index does

---

## Peer Review

The full independent academic peer review of this report is in [PEER-REVIEW.md](PEER-REVIEW.md) (also available as [Word](peer-review/EII-Peer-Review.docx) under [`peer-review/`](peer-review/)).

**Recommendation:** Major revisions

**What the review found:**

- The central proxy is unvalidated: INFORM Complexity (humanitarian access for responders) is used as a stand-in for civilian-evacuation risk, and the report never shows where the two diverge. — **Fixed: examined against the live 104-crisis dataset (new S4.2a).**
- The headline ratio is fragile: the arbitrary 0.5 floor can swing it ~2.5x, and equal ratios hide very different absolute stakes. — **Partly fixed: the floor is shown to be inert on real data; the compression problem is now quantified.**
- No worked example: a tool meant to make a comparison visible never walks one real crisis through the numbers. — **Fixed: two crises walked end to end (new S4.2b).**

**Noted strength:** Scoring leaving-vs-staying and danger-vs-feasibility as separate dimensions is a genuine contribution, paired with unusually honest self-disclosure.


### Revisions applied (peer review, Tier 3)

**The INFORM Complexity proxy is now examined rather than merely labelled** (new S4.2a), against the live April 2026 dataset of 104 crises:

- **Correlation between Conditions (RSS) and Complexity (RSE) is r = 0.62** — a real association that still leaves over half the variance unshared. Complexity is a different measurement, not a noisy copy.
- **The bias has a specific direction.** Complexity is largely a property of the *country* (conflict-driven operating environment for responders); Conditions is a property of *this crisis*. When a low-intensity crisis sits inside a high-conflict state, the two pull apart and the index reads an aid-delivery fact as a civilian-movement fact.
- **The worked divergence case is Yemen.** "2026 Floods in Yemen" carries the **highest EDI in the index (2.60)** — RSS 1.36 (the dataset minimum) against RSE 3.53. It earns that score because Yemen's *war* inflates Complexity, not because fleeing floodwater is dangerous. The favourable case is Bangladesh (EDI 0.50), where low Complexity genuinely reflects a well-rehearsed cyclone-evacuation system.
- **New finding the review did not anticipate: the ratio is least informative where stakes are highest.** Across the seventeen severity-5 crises, EDI spans only 0.83–1.13, with Somalia, Burkina Faso and Mali all at exactly 1.00. Both components saturate near the ceiling and the ratio collapses toward unity. Every large EDI in the index comes from a low- or mid-severity crisis.
- **The 0.5 floor is inert on real data:** zero of 104 crises have RSS below 0.5 (observed minimum 1.36), so the safeguard distorts no published figure.

**Two crises are now walked end to end** (new S4.2b): Sudan's complex crisis (RSS 4.87, RSE 4.73, EDI 0.97 — the compression case) and the 2026 Yemen floods (RSS 1.36, RSE 3.53, EDI 2.60 — the misreading case), each with the floor check shown.

**Also noted** (S5.3): Feasibility and the Risk Score for Evacuating are the same quantity under two names, both derived from INFORM Complexity and pointing in opposite directions. They do not contradict each other arithmetically, but presenting them as separate concepts implies two independent readings of movement where there is one.
