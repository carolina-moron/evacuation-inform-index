#!/usr/bin/env python3
"""Aggregate the per-crisis road-access findings into one file the map can draw.

The road-access reports live in snapshot/detail/<slug>.json, one file per
crisis, and the drawer fetches a single file when you open a crisis. Drawing
pins for the whole world needs every crisis at once, and 104 requests to paint
one layer is not a trade worth making — so this flattens the road block out of
each detail file into snapshot/roads.json.

Coverage is the thing this file has to be honest about. Of the 104 crises, the
road search has only ever run for some of them; the rest carry "roads": null
and have never been looked at. A crisis with no pin is therefore ambiguous
between "searched, nothing found" and "never searched", and those two mean
very different things on a map about whether people can leave. So the output
records all three states explicitly and the map reports the split.

Usage:
    python3 build_roads_layer.py            # rebuild snapshot/roads.json

Cheap and offline: it only reads files snapshot.py / snapshot_roads.py already
wrote, so it costs no API credits and can be re-run at will.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(ROOT, "snapshot")
INDEX = os.path.join(SNAP, "index.json")
DETAIL = os.path.join(SNAP, "detail")
OUT = os.path.join(SNAP, "roads.json")

# Kept in the same order the drawer lists them, worst first, so the map can take
# the first status present as the one to colour a pin by.
ORDER = ["blocked", "damaged", "checkpoint", "reopened"]

# The map popup shows the same fields the drawer does; anything else in an item
# is search-engine bookkeeping the reader has no use for.
ITEM_FIELDS = ("title", "url", "date", "source", "status", "tags")


def main():
    if not os.path.exists(INDEX):
        sys.exit(f"missing {INDEX} — run snapshot.py first")

    index = json.load(open(INDEX, encoding="utf-8"))
    items = index.get("items", [])

    out, searched, unsearched, with_reports = [], 0, 0, 0

    for entry in items:
        slug = entry.get("slug")
        path = os.path.join(DETAIL, f"{slug}.json")
        if not os.path.exists(path):
            unsearched += 1
            continue

        detail = json.load(open(path, encoding="utf-8"))
        roads = detail.get("roads")

        # null means the road search never ran for this crisis — not that it ran
        # and found nothing. Recorded as a count, not as a pin.
        if not roads:
            unsearched += 1
            continue

        searched += 1
        reports = roads.get("items") or []
        if not reports:
            continue
        with_reports += 1

        counts = roads.get("counts") or {}
        # Colour the pin by the most serious status actually reported.
        worst = next((s for s in ORDER if counts.get(s)), None)

        out.append({
            "slug": slug,
            "crisis": entry.get("crisis"),
            "country": entry.get("country"),
            "lat": entry.get("lat"),
            "lng": entry.get("lng"),
            "counts": {k: v for k, v in counts.items() if v},
            "worst": worst,
            "signal": roads.get("signal"),
            "considered": roads.get("considered"),
            "query_days": roads.get("query_days"),
            "items": [
                {k: it.get(k) for k in ITEM_FIELDS if it.get(k) is not None}
                for it in reports
            ],
        })

    payload = {
        "total": len(items),
        "searched": searched,
        "unsearched": unsearched,
        "with_reports": with_reports,
        "crises": out,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    print(f"  {len(items)} crises: {searched} searched, {unsearched} never searched")
    print(f"  {with_reports} carry road-access reports and will be pinned")
    print(f"  {sum(len(c['items']) for c in out)} reports total")


if __name__ == "__main__":
    main()
