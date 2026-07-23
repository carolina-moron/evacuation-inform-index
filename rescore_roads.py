#!/usr/bin/env python3
"""Re-apply the road relevance gate to already-baked snapshots. Costs nothing.

Snapshots fetched before a gate fix hold items that the current rules would
reject — most importantly for "CAR" and "DRC", whose abbreviations produced no
place token, which disabled the location check entirely and let unrelated news
score as road obstruction.

This re-filters the stored items and recomputes counts and signal locally. It
can only ever *remove* items: anything the old gate discarded was never written
to the file, so a crisis whose gate has since become more permissive (the new
Gaza / West Bank aliases, for example) stays under-counted until it is
re-fetched. Those are reported at the end so they can be refreshed when API
credits allow.

Usage:
    python3 rescore_roads.py --dry-run   # report changes, write nothing
    python3 rescore_roads.py             # apply
"""
import json, glob, os, sys
import server

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "snapshot", "detail")


def main():
    dry = "--dry-run" in sys.argv
    changed, stale = [], []

    for path in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        d = json.load(open(path, encoding="utf-8"))
        roads = d.get("roads")
        if not roads:
            continue
        country, crisis = d.get("country"), d.get("crisis")

        kept, counts = [], {"blocked": 0, "damaged": 0, "checkpoint": 0, "reopened": 0}
        for it in roads.get("items") or []:
            blob = f"{it.get('title','')} {it.get('snippet','')}"
            if not server.road_item_is_relevant(blob, country):
                continue
            # Re-classify too: the status patterns were corrected alongside the
            # gate ("shuts" did not match \bshut\b, so closures read as reopenings).
            status, tags = server.classify_road(blob)
            if status == "unclear":
                continue
            counts[status] += 1
            kept.append(dict(it, status=status, tags=tags))

        score = sum(server.ROAD_WEIGHTS[s] * n for s, n in counts.items())
        signal = round(max(0.0, min(1.0, score / server.ROAD_SATURATE)), 3)
        before = roads.get("signal")

        if kept != (roads.get("items") or []) or signal != before:
            changed.append((os.path.basename(path), country, before, signal,
                            len(roads.get("items") or []), len(kept)))
            if not dry:
                roads["items"] = kept
                roads["counts"] = counts
                roads["signal"] = signal
                roads["rescored"] = True
                json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)

        # Crises whose alias list grew were searched under a stricter gate than
        # the one now in force, so their stored items may be incomplete.
        if country in server.PLACE_ALIASES:
            stale.append(country)

    print(f"{'[dry run] ' if dry else ''}{len(changed)} snapshots changed\n")
    for name, country, b, a, n_before, n_after in sorted(
            changed, key=lambda r: -(r[2] or 0)):
        print(f"  {country:22} signal {b:<6} -> {a:<6} items {n_before} -> {n_after}")

    if stale:
        uniq = sorted(set(stale))
        print(f"\n{len(uniq)} crises should be re-fetched when credits allow "
              f"(their alias set expanded, so the stored items may be incomplete):")
        print("  " + ", ".join(uniq))


if __name__ == "__main__":
    main()
