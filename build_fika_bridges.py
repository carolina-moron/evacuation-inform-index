#!/usr/bin/env python3
"""Turn Fika's published trail-bridge register into the layer the map draws.

Fika (formerly Bridges to Prosperity) builds pedestrian trail bridges over the
rivers that cut rural communities off from clinics, markets and each other, and
publishes the register of every bridge it has built, supported or influenced as
a CSV on its public data bucket. On a map about whether people can physically
leave a place, a built river crossing is the rarest thing there is: a named,
surveyed point where a route is known to exist.

    https://public-b2p-geodata.s3.us-east-1.amazonaws.com/webmap-bridges/webmap-bridges.csv

This vendors that CSV into fika/bridges.json rather than fetching it live, for
the same reason snapshot/ exists: the map should keep drawing what it drew last
time even if the bucket is renamed, and the file it draws should be reviewable
in the diff. Re-run this to refresh it.

Coverage is what this file has to be honest about, and the honesty cuts the
opposite way from the road layer. The bridges are precisely located — these are
surveyed structures, not a country centroid — but they exist only where Fika
has worked, which is nowhere near the whole crisis map. Most EII crises are in
countries with no Fika bridge at all, and the countries with the most bridges
(Rwanda, Bolivia, Nicaragua) carry no EII crisis. So absence of a bridge here
means "Fika has not built here", never "there is no crossing" — and the layer
says so where it is switched on, because the silent reading of a sparse map is
that the sparse places lack crossings.

Usage:
    python3 build_fika_bridges.py           # refresh fika/bridges.json

Licence: the source data is CC-BY 4.0. Attribution rides in the output file and
is rendered in the map's attribution control.
"""
import csv
import io
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "fika")
OUT = os.path.join(OUT_DIR, "bridges.json")

SRC = ("https://public-b2p-geodata.s3.us-east-1.amazonaws.com"
       "/webmap-bridges/webmap-bridges.csv")

# Salesforce field names, which is what the export is dumped from.
F_COUNTRY, F_NAME = "Country__c", "Bridge_Name__c"
F_KIND, F_STAGE = "Project_Type__c", "StageName"
F_SERVED, F_TYPE = "Individuals_Directly_Served__c", "Bridge_Type__c"
F_SPAN, F_YEAR = "Span_m__c", "Fiscal_Year__c"
F_LAT, F_LNG = "GPS__Latitude__s", "GPS__Longitude__s"

# The export writes the string "null" into empty cells rather than leaving them
# blank, so an unguarded read yields the literal text "null" in a popup.
def clean(v):
    v = (v or "").strip()
    return "" if v.lower() in ("", "null", "none", "n/a") else v


def num(v):
    v = clean(v)
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def main():
    print(f"fetching {SRC}")
    with urllib.request.urlopen(SRC, timeout=120) as r:
        raw = r.read().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(raw)))
    print(f"  {len(rows)} rows")

    out, skipped = [], 0
    for r in rows:
        lat, lng = num(r.get(F_LAT)), num(r.get(F_LNG))
        # A bridge with no usable coordinate cannot be drawn, and dropping it is
        # better than parking it at (0, 0) in the Gulf of Guinea. Counted, so
        # the total on screen can be reconciled against the source row count.
        if lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            skipped += 1
            continue
        if lat == 0 and lng == 0:
            skipped += 1
            continue
        rec = {
            "n": clean(r.get(F_NAME)),
            "c": clean(r.get(F_COUNTRY)),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "stage": clean(r.get(F_STAGE)),
            "kind": clean(r.get(F_KIND)),
            "type": clean(r.get(F_TYPE)),
        }
        served, span, year = num(r.get(F_SERVED)), num(r.get(F_SPAN)), clean(r.get(F_YEAR))
        if served is not None:
            rec["served"] = int(served)
        if span is not None:
            rec["span"] = round(span, 1)
        if year:
            rec["year"] = year
        out.append(rec)

    countries = {}
    for b in out:
        countries[b["c"] or "unknown"] = countries.get(b["c"] or "unknown", 0) + 1

    payload = {
        "source": SRC,
        "attribution": "Trail bridges © Fika (Bridges to Prosperity), CC-BY 4.0",
        "license": "CC-BY-4.0",
        "note": ("Bridges Fika has built, supported or influenced. Coordinates are "
                 "surveyed structure locations. The register covers only countries "
                 "where Fika works — no bridge here does not mean no crossing."),
        "total": len(out),
        "dropped_no_coords": skipped,
        "countries": dict(sorted(countries.items(), key=lambda kv: -kv[1])),
        "bridges": out,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    print(f"  {len(out)} bridges drawable, {skipped} dropped for missing coordinates")
    top = list(payload["countries"].items())[:6]
    print("  " + ", ".join(f"{c} {n}" for c, n in top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
