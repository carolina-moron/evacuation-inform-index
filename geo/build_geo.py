#!/usr/bin/env python3
"""Validate geo/locations.csv against data.js and emit geo.js.

The INFORM export gives no coordinates, so the original data.js placed every
crisis at a rounded country centroid — and where one country carried several
crises, at that centroid plus a ~0.9-degree offset to stop the markers
overlapping. That put roughly three quarters of the points somewhere the crisis
is not (Gaza in southern Syria, Papua in Sulawesi, Cabo Delgado 800 km south).

locations.csv replaces those with a curated point per crisis and, just as
importantly, records what the point *means*:

  subnational  the crisis names a sub-national area -> centroid of that area
  reception    displacement concentrated in known hosting/transit areas
               -> the main hosting area, named
  country      the crisis is national in scope -> the country's approximate
               population-weighted centroid, NOT its geographic centre. For
               Libya, Algeria, Mali, Chad, Niger, Mauritania and Egypt the two
               are hundreds of kilometres apart, and the geographic centre is
               empty desert.

`confidence` is the honest part: `low` marks a crisis whose name is national but
whose impact is almost certainly localised (INFORM does not publish the affected
admin areas), so the point is a country-level stand-in and the UI says so.

Run:  python3 geo/build_geo.py   [--check]
      --check validates and reports without writing geo.js
"""
import csv, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "geo", "locations.csv")
OUT_PATH = os.path.join(ROOT, "geo.js")

SCOPES = {"subnational", "reception", "country"}
CONFIDENCE = {"high", "medium", "low"}

# Rough per-country bounding boxes (minLon, minLat, maxLon, maxLat), used only to
# catch gross placement errors — a point outside its own country. Mainland only:
# Ecuador excludes the Galapagos and Spain the Canaries, neither of which hosts
# the crisis in question. This is a guard rail, not a source of truth; a point
# can sit inside the box and still be wrong, which is what `basis` is for.
BBOX = {
    "AFG": (60.5, 29.4, 74.9, 38.5), "AGO": (11.7, -18.0, 24.1, -4.4),
    "BDI": (29.0, -4.5, 30.9, -2.3), "BEN": (0.8, 6.2, 3.9, 12.4),
    "BFA": (-5.5, 9.4, 2.4, 15.1),   "BGD": (88.0, 20.7, 92.7, 26.6),
    "BRA": (-74.0, -33.8, -34.8, 5.3), "CAF": (14.4, 2.2, 27.5, 11.0),
    "CHL": (-75.7, -56.0, -66.4, -17.5), "CIV": (-8.6, 4.3, -2.5, 10.7),
    "CMR": (8.5, 1.7, 16.2, 13.1),   "COD": (12.2, -13.5, 31.3, 5.4),
    "COL": (-79.0, -4.3, -66.9, 12.5), "CRI": (-85.95, 8.0, -82.5, 11.2),
    "CUB": (-85.0, 19.8, -74.1, 23.3), "DJI": (41.7, 10.9, 43.4, 12.7),
    "DOM": (-72.0, 17.5, -68.3, 19.9), "DZA": (-8.7, 19.0, 12.0, 37.1),
    "ECU": (-81.1, -5.0, -75.2, 1.4), "EGY": (24.7, 22.0, 36.9, 31.7),
    "ERI": (36.4, 12.4, 43.1, 18.0), "ESP": (-9.3, 36.0, 3.3, 43.8),
    "ETH": (33.0, 3.4, 48.0, 14.9),  "GRC": (19.4, 34.8, 29.6, 41.7),
    "GTM": (-92.2, 13.7, -88.2, 17.8), "HND": (-89.4, 12.9, -83.1, 16.5),
    "HTI": (-74.5, 18.0, -71.6, 20.1), "IDN": (95.0, -11.0, 141.0, 6.1),
    "IRN": (44.0, 25.1, 63.3, 39.8), "IRQ": (38.8, 29.1, 48.6, 37.4),
    "ITA": (6.6, 36.6, 18.5, 47.1),  "JAM": (-78.4, 17.7, -76.2, 18.5),
    "JOR": (34.9, 29.2, 39.3, 33.4), "KEN": (33.9, -4.7, 41.9, 5.5),
    "KHM": (102.3, 10.4, 107.6, 14.7), "LBN": (35.1, 33.0, 36.6, 34.7),
    "LBY": (9.3, 19.5, 25.2, 33.2),  "LKA": (79.6, 5.9, 81.9, 9.9),
    "MAR": (-13.2, 27.7, -1.0, 35.9), "MDG": (43.2, -25.6, 50.5, -11.9),
    "MEX": (-118.4, 14.5, -86.7, 32.7), "MLI": (-12.2, 10.1, 4.3, 25.0),
    "MMR": (92.2, 9.8, 101.2, 28.5), "MOZ": (30.2, -26.9, 40.8, -10.5),
    "MRT": (-17.1, 14.7, -4.8, 27.3), "MWI": (32.7, -17.1, 35.9, -9.4),
    "MYS": (99.6, 0.85, 119.3, 7.4), "NAM": (11.7, -28.97, 25.3, -16.9),
    "NER": (0.2, 11.7, 16.0, 23.5),  "NGA": (2.7, 4.2, 14.7, 13.9),
    "PAK": (60.9, 23.7, 77.8, 37.1), "PAN": (-83.1, 7.2, -77.1, 9.7),
    "PER": (-81.4, -18.4, -68.6, -0.03), "PHL": (116.9, 4.6, 126.6, 21.1),
    "PSE": (34.2, 31.2, 35.6, 32.6), "SDN": (21.8, 8.7, 38.6, 22.2),
    "SLV": (-90.1, 13.1, -87.7, 14.5), "SOM": (40.9, -1.7, 51.4, 12.0),
    "SSD": (24.1, 3.5, 35.9, 12.2),  "SYR": (35.7, 32.3, 42.4, 37.3),
    "TCD": (13.5, 7.4, 24.0, 23.5),  "TGO": (-0.15, 6.1, 1.8, 11.1),
    "THA": (97.3, 5.6, 105.6, 20.5), "TTO": (-61.95, 10.0, -60.5, 11.4),
    "TUN": (7.5, 30.2, 11.6, 37.5),  "TUR": (26.0, 35.8, 44.8, 42.1),
    "TZA": (29.3, -11.8, 40.5, -0.9), "UGA": (29.5, -1.5, 35.0, 4.2),
    "UKR": (22.1, 44.4, 40.2, 52.4), "VEN": (-73.4, 0.6, -59.8, 12.2),
    "YEM": (42.5, 12.1, 54.5, 19.0),
}


def detail_slug(crisis, country):
    """Deterministic key — MUST match detailSlug() in index.html and snapshot.py."""
    return re.sub(r"[^a-z0-9]+", "-", f"{crisis}__{country}".lower()).strip("-")


def load_crises():
    txt = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
    m = re.search(r"window\.EDI_DATA\s*=\s*(\[.*?\])\s*;", txt, re.S)
    if not m:
        sys.exit("could not parse window.EDI_DATA from data.js")
    crises, seen = [], {}
    for i, c in enumerate(json.loads(m.group(1)), 1):
        s = detail_slug(c["crisis"], c["name"])
        if s in seen:                      # same collision guard as snapshot.py
            s = f"{s}-{i}"
        seen[s] = 1
        c["_slug"] = s
        crises.append(c)
    return crises


def main():
    check_only = "--check" in sys.argv
    crises = load_crises()
    rows = {}
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            slug = r["slug"].strip()
            if slug in rows:
                sys.exit(f"duplicate slug in locations.csv: {slug}")
            rows[slug] = r

    errors, warnings = [], []

    missing = [c["_slug"] for c in crises if c["_slug"] not in rows]
    if missing:
        errors.append(f"{len(missing)} crises have no row in locations.csv: {missing[:5]}")
    orphan = [s for s in rows if s not in {c["_slug"] for c in crises}]
    if orphan:
        errors.append(f"{len(orphan)} rows in locations.csv match no crisis: {orphan[:5]}")

    out, moved = {}, []
    for c in crises:
        r = rows.get(c["_slug"])
        if not r:
            continue
        try:
            lat, lng = float(r["lat"]), float(r["lng"])
        except ValueError:
            errors.append(f"{c['_slug']}: lat/lng not numeric")
            continue
        scope, conf = r["scope"].strip(), r["confidence"].strip()
        if scope not in SCOPES:
            errors.append(f"{c['_slug']}: unknown scope {scope!r}")
        if conf not in CONFIDENCE:
            errors.append(f"{c['_slug']}: unknown confidence {conf!r}")
        if not r["place"].strip():
            errors.append(f"{c['_slug']}: empty place label")
        box = BBOX.get(c["iso3"])
        if not box:
            warnings.append(f"{c['_slug']}: no bounding box for {c['iso3']} — not checked")
        elif not (box[0] <= lng <= box[2] and box[1] <= lat <= box[3]):
            errors.append(f"{c['_slug']}: {lat},{lng} lies outside {c['iso3']} {box}")

        d = haversine(lat, lng, c["lat"], c["lng"])
        if d >= 25:
            moved.append((d, c["_slug"], r["place"].strip()))
        out[c["_slug"]] = {
            "lat": lat, "lng": lng, "scope": scope,
            "place": r["place"].strip(), "basis": r["basis"].strip(),
            "confidence": conf,
        }

    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARN    {w}")

    by_scope = {s: sum(1 for v in out.values() if v["scope"] == s) for s in SCOPES}
    by_conf = {k: sum(1 for v in out.values() if v["confidence"] == k) for k in CONFIDENCE}
    print(f"\n{len(out)}/{len(crises)} crises located  "
          f"· scope {by_scope}  · confidence {by_conf}")
    moved.sort(reverse=True)
    print(f"{len(moved)} points moved 25 km or more. Largest corrections:")
    for d, slug, place in moved[:10]:
        print(f"  {d:6.0f} km  {slug}  ->  {place}")

    if errors:
        sys.exit("\nvalidation failed — geo.js not written")
    if check_only:
        print("\n--check: geo.js not written")
        return

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("/* GENERATED by geo/build_geo.py from geo/locations.csv — do not edit.\n"
                "   Curated crisis locations replacing the country-centroid placeholders\n"
                "   that shipped in data.js. `scope` says what the point represents;\n"
                "   `confidence` is low where INFORM names no sub-national area. */\n")
        f.write("window.EII_GEO=")
        json.dump(out, f, ensure_ascii=False, sort_keys=True)
        f.write(";\n")
    print(f"\nwrote {OUT_PATH}")


def haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, asin, sqrt
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    return 2 * 6371 * asin(sqrt(sin((lat2 - lat1) / 2) ** 2
                                + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2))


if __name__ == "__main__":
    main()
