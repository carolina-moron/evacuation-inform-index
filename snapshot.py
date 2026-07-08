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

def main():
    force = "--force" in sys.argv
    days = 60
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])

    env = server.load_env()
    tk = env.get("TAVILY_API_KEY")
    ae, ap = env.get("ACLED_EMAIL"), env.get("ACLED_PASSWORD")
    print(f"keys: tavily={bool(tk)} acled={bool(ae and ap)}")

    os.makedirs(OUT, exist_ok=True)
    crises = load_crises()
    slugs, index = {}, []
    done = skipped = failed = 0

    for i, c in enumerate(crises, 1):
        crisis, country = c["crisis"], c["name"]
        slug = detail_slug(crisis, country)
        if slug in slugs:  # collision guard
            slug = f"{slug}-{i}"
        slugs[slug] = True
        index.append({"crisis": crisis, "country": country, "slug": slug,
                      "lat": c.get("lat"), "lng": c.get("lng")})
        path = os.path.join(OUT, slug + ".json")

        if os.path.exists(path) and not force:
            skipped += 1
            print(f"[{i}/{len(crises)}] skip  {slug}")
            continue

        resp = {"crisis": crisis, "country": country, "cached": False, "days": days,
                "tavily": None, "acled": None, "errors": [],
                "keys": {"tavily": bool(tk), "acled": bool(ae and ap)},
                "snapshot": True}
        if tk:
            try:
                resp["tavily"] = server.tavily_news(
                    tk, f"{country} {crisis} latest conflict, security and humanitarian developments",
                    days=days)
            except Exception as e:
                resp["errors"].append(f"tavily: {e}")
        if ae and ap:
            try:
                resp["acled"] = server.acled_timeline(ae, ap, country)
            except Exception as e:
                resp["errors"].append(f"acled: {e}")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(resp, f, ensure_ascii=False)
        if resp["errors"] and not (resp["tavily"] or resp["acled"]):
            failed += 1
        else:
            done += 1
        n_news = len((resp.get("tavily") or {}).get("items") or [])
        n_mon = len((resp.get("acled") or {}).get("months") or [])
        print(f"[{i}/{len(crises)}] ok    {slug}  news={n_news} acled_months={n_mon} "
              + (f"errors={resp['errors']}" if resp["errors"] else ""))
        time.sleep(0.4)  # be gentle on the APIs

    with open(os.path.join(ROOT, "snapshot", "index.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_days": days, "count": len(index), "items": index}, f, ensure_ascii=False)
    print(f"\nDONE  new={done} skipped={skipped} failed={failed}  -> {OUT}")

if __name__ == "__main__":
    main()
