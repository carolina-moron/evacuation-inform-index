#!/usr/bin/env python3
"""Backfill the road-access field into snapshots that predate the roads feature.

The road-access search shipped after snapshot/detail/*.json were generated, so
every baked file has `"roads": null` and the hosted site reports road access as
"not searched". This adds only that field.

Why not `snapshot.py --force`? Two reasons:
  1. It re-fetches the Tavily news for all 104 crises, which is already present
     and correct — 104 credits spent to rewrite identical data.
  2. It re-fetches ACLED, and with ACLED_PASSWORD unset that overwrites 96
     working conflict timelines with error stubs.

This script touches nothing but `roads`, so it costs 1 credit per crisis
instead of 2 and cannot damage data it did not fetch.

Usage:
    python3 snapshot_roads.py               # backfill crises missing roads
    python3 snapshot_roads.py --force       # refetch roads even where present
    python3 snapshot_roads.py --limit 5     # stop after N fetches (try it first)
    python3 snapshot_roads.py --days 60     # news window, must match snapshot.py

Resumable: each file is written as it completes, so an interrupted run picks up
where it stopped. Keys are read from the gitignored .env, exactly like
snapshot.py.
"""
import os, sys, json, glob, time, urllib.error
import server  # reuse load_env / tavily_roads

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "snapshot", "detail")

# Development keys (tvly-dev-*) are rate-limited hard enough that a tight loop
# gets 429/432 within a few dozen calls, and a failed call still costs the
# wall-clock of a round trip. Pace conservatively and back off rather than
# burning through the run producing error stubs.
PACE_SECONDS = 2.0
MAX_RETRIES = 5


def fetch_with_backoff(tk, country, crisis, days):
    """One roads fetch, retrying on throttling with exponential backoff.

    429 (too many requests) and 432 (plan limit) are both transient under a dev
    key, so they are retried; anything else is a real error and propagates
    immediately instead of wasting five sleeps on it.
    """
    delay = 4.0
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return server.tavily_roads(tk, country, crisis, days=days)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 432) or attempt == MAX_RETRIES:
                raise
            print(f"      throttled (HTTP {e.code}), retry {attempt}/{MAX_RETRIES - 1} "
                  f"in {delay:.0f}s")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def main():
    force = "--force" in sys.argv
    days = 60
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    env = server.load_env()
    tk = env.get("TAVILY_API_KEY")
    if not tk:
        sys.exit("TAVILY_API_KEY is not set in .env — nothing to do.")

    files = sorted(glob.glob(os.path.join(OUT, "*.json")))
    if not files:
        sys.exit(f"no snapshots found in {OUT}")

    todo = []
    for path in files:
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print(f"skip (unreadable) {os.path.basename(path)}: {e}")
            continue
        if d.get("roads") is not None and not force:
            continue
        todo.append((path, d))

    print(f"{len(files)} snapshots, {len(todo)} need roads"
          f"{f' (limited to {limit})' if limit else ''}")
    print(f"cost: 1 Tavily credit each -> ~{min(len(todo), limit or len(todo))} credits\n")

    done = failed = 0
    for i, (path, d) in enumerate(todo, 1):
        if limit and done + failed >= limit:
            print(f"\nstopped at --limit {limit}")
            break
        crisis, country = d.get("crisis"), d.get("country")
        try:
            roads = fetch_with_backoff(tk, country, crisis, days)
        except Exception as e:
            failed += 1
            # Record the failure rather than leaving null, so the UI can tell
            # "searched and found nothing" apart from "never searched". Drop any
            # earlier roads error first: this script is re-run after throttling,
            # and without this each pass would stack another stub on the same file.
            errs = [x for x in (d.get("errors") or [])
                    if not str(x).startswith("roads:")]
            errs.append(f"roads: {e}")
            d["errors"] = errs
            json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"[{i}/{len(todo)}] FAIL  {os.path.basename(path)}: {e}")
            continue

        d["roads"] = roads
        # Write immediately so an interrupted run keeps completed work.
        json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        done += 1
        n = len(roads.get("items") or [])
        sig = roads.get("signal")
        print(f"[{i}/{len(todo)}] ok    {os.path.basename(path)}  "
              f"items={n} signal={sig if sig is None else round(sig, 2)}")
        time.sleep(PACE_SECONDS)  # stay under the dev-key rate limit

    print(f"\ndone={done} failed={failed}")
    if done:
        print("Commit snapshot/detail/ and push — GitHub Pages serves these files.")


if __name__ == "__main__":
    main()
