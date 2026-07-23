#!/usr/bin/env python3
"""Bake a static snapshot of the live /api/detail responses.

Runs the same Tavily + ACLED backend logic as server.py, once per crisis, and
writes snapshot/detail/<slug>.json. The static site (GitHub Pages) falls back to
these files when the Python backend isn't running — so the hosted app mimics the
live one with data frozen at snapshot time.

Usage:
    python3 snapshot.py            # generate missing snapshots (resumable)
    python3 snapshot.py --force    # regenerate everything
    python3 snapshot.py --days 60  # time window for Tavily news (default 60)
    python3 snapshot.py --no-roads # skip the road-access search (halves credits)

Each crisis costs 2 Tavily credits (news + road access), so a full 104-crisis
run spends ~208. --no-roads brings that back to ~104.

Keys are read from the gitignored .env, exactly like server.py.
"""
import os, sys, re, json, time
import server  # reuse load_env / tavily_news / acled_timeline

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "snapshot", "detail")

def detail_slug(crisis, country):
    """Deterministic key — MUST match detailSlug() in index.html."""
    s = f"{crisis}__{country}".lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

def load_crises():
    txt = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
    m = re.search(r"window\.EDI_DATA\s*=\s*(\[.*?\])\s*;", txt, re.S)
    if not m:
        sys.exit("could not parse window.EDI_DATA from data.js")
    return json.loads(m.group(1))

def load_geo():
    """Curated crisis locations from geo.js (built by geo/build_geo.py).

    Supplies both the coordinates written into snapshot/index.json and the
    `place` term that anchors each Tavily search on the actual affected area.
    """
    p = os.path.join(ROOT, "geo.js")
    if not os.path.exists(p):
        print("warn: geo.js not found — run python3 geo/build_geo.py. "
              "Falling back to the country-centroid coordinates in data.js.")
        return {}
    m = re.search(r"window\.EII_GEO\s*=\s*(\{.*\})\s*;", open(p, encoding="utf-8").read(), re.S)
    if not m:
        sys.exit("could not parse window.EII_GEO from geo.js")
    return json.loads(m.group(1))

def main():
    force = "--force" in sys.argv
    roads = "--no-roads" not in sys.argv
    days = 60
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])

    env = server.load_env()
    tk = env.get("TAVILY_API_KEY")
    ae, ap = env.get("ACLED_EMAIL"), env.get("ACLED_PASSWORD")
    print(f"keys: tavily={bool(tk)} acled={bool(ae and ap)}  roads={roads}")
    if tk and roads:
        print("note: 2 Tavily credits per crisis (news + roads); --no-roads halves it")

    os.makedirs(OUT, exist_ok=True)
    crises = load_crises()
    geo = load_geo()
    slugs, index = {}, []
    done = skipped = failed = 0

    for i, c in enumerate(crises, 1):
        crisis, country = c["crisis"], c["name"]
        slug = detail_slug(crisis, country)
        if slug in slugs:  # collision guard
            slug = f"{slug}-{i}"
        slugs[slug] = True
        g = geo.get(slug) or {}
        # Only a real sub-national location sharpens the search; a country-scope
        # label ("Somalia — national") would just repeat the country term.
        place = g.get("place") if g.get("scope") in ("subnational", "reception") else None
        index.append({"crisis": crisis, "country": country, "slug": slug,
                      "lat": g.get("lat", c.get("lat")), "lng": g.get("lng", c.get("lng")),
                      "place": g.get("place"), "scope": g.get("scope"),
                      "confidence": g.get("confidence")})
        path = os.path.join(OUT, slug + ".json")

        if os.path.exists(path) and not force:
            skipped += 1
            print(f"[{i}/{len(crises)}] skip  {slug}")
            continue

        resp = {"crisis": crisis, "country": country, "place": place,
                "cached": False, "days": days,
                "tavily": None, "acled": None, "roads": None, "errors": [],
                "keys": {"tavily": bool(tk), "acled": bool(ae and ap)},
                "snapshot": True}
        if tk:
            try:
                resp["tavily"] = server.tavily_news(
                    tk, f"{server.crisis_query(country, crisis, place)} "
                        "latest conflict, security and humanitarian developments",
                    days=days)
                server.usage_bump("tavily")   # a real search credit was spent
            except Exception as e:
                resp["errors"].append(f"tavily: {e}")
            if roads:
                try:
                    resp["roads"] = server.tavily_roads(tk, country, crisis,
                                                        days=days, place=place)
                    server.usage_bump("tavily")   # second search = second credit
                except Exception as e:
                    resp["errors"].append(f"roads: {e}")
        if ae and ap:
            try:
                resp["acled"] = server.acled_timeline(ae, ap, country)
            except Exception as e:
                resp["errors"].append(f"acled: {e}")

        # Never overwrite a good snapshot with an empty one. A run against an
        # expired or missing API key returns nothing but errors for every
        # crisis, and blindly writing that result destroys the committed
        # snapshot the hosted site depends on — the failure mode is silent,
        # because each crisis still reports "ok". server.py already refuses to
        # cache empty responses for the same reason.
        got_data = bool(resp["tavily"] or resp["acled"] or resp["roads"])
        if not got_data:
            failed += 1
            print(f"[{i}/{len(crises)}] FAIL  {slug}  no data returned — "
                  f"existing snapshot left untouched. errors={resp['errors']}")
            if failed >= 5 and done == 0:
                sys.exit("\nAborting: the first 5 crises all returned nothing. "
                         "This is almost certainly a credentials problem, not 104 "
                         "separate outages — check TAVILY_API_KEY / ACLED_* in .env. "
                         "No snapshot files were modified.")
            time.sleep(0.4)
            continue

        with open(path, "w", encoding="utf-8") as f:
            json.dump(resp, f, ensure_ascii=False)
        done += 1
        n_news = len((resp.get("tavily") or {}).get("items") or [])
        n_mon = len((resp.get("acled") or {}).get("months") or [])
        n_road = len((resp.get("roads") or {}).get("items") or [])
        print(f"[{i}/{len(crises)}] ok    {slug}  news={n_news} acled_months={n_mon} roads={n_road} "
              + (f"errors={resp['errors']}" if resp["errors"] else ""))
        time.sleep(0.4)  # be gentle on the APIs

    with open(os.path.join(ROOT, "snapshot", "index.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_days": days, "count": len(index), "items": index}, f, ensure_ascii=False)
    print(f"\nDONE  new={done} skipped={skipped} failed={failed}  -> {OUT}")

if __name__ == "__main__":
    main()
