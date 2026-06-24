#!/usr/bin/env python3
"""Evacuation Inform Index — local backend.

Serves the static site AND a /api/detail endpoint that pulls, server-side:
  • Tavily  -> live news / developments per crisis (real-time)
  • ACLED   -> structured, dated conflict events for the timeline
Keys are read from a gitignored .env file (or the environment).
Stdlib only — no pip install needed.  Run:  python3 server.py
"""
import json, os, time, hashlib, urllib.request, urllib.parse, http.server
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8000"))
CACHE_DIR = os.path.join(ROOT, ".cache")
CACHE_TTL = 6 * 3600  # 6 hours — repeat clicks within this window are free

# ---- API-usage tracking (so you don't blow through Tavily credits) ----
# Tavily bills per *search* (basic = 1 credit), not per token. We count every
# real outbound call here; cache hits cost nothing and are not counted.
USAGE_PATH = os.path.join(CACHE_DIR, "usage.json")
SESSION_USAGE = {"tavily": 0, "acled": 0, "earth_image": 0}  # since this process started

def usage_bump(kind):
    SESSION_USAGE[kind] = SESSION_USAGE.get(kind, 0) + 1
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        data = json.load(open(USAGE_PATH)) if os.path.exists(USAGE_PATH) else {}
        data[kind] = data.get(kind, 0) + 1
        json.dump(data, open(USAGE_PATH, "w"))
    except Exception:
        pass

def usage_read():
    try:
        return json.load(open(USAGE_PATH)) if os.path.exists(USAGE_PATH) else {}
    except Exception:
        return {}

def _cache_path(key):
    return os.path.join(CACHE_DIR, hashlib.sha1(key.encode()).hexdigest()[:16] + ".json")

def cache_get(key):
    p = _cache_path(key)
    if os.path.exists(p) and time.time() - os.path.getmtime(p) < CACHE_TTL:
        try:
            return json.load(open(p))
        except Exception:
            return None
    return None

def cache_set(key, obj):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        json.dump(obj, open(_cache_path(key), "w"))
    except Exception:
        pass

# ---- ACLED country-name aliases (INFORM name -> ACLED name) ----
ACLED_ALIAS = {
    "DR Congo": "Democratic Republic of Congo",
    "Congo DRC": "Democratic Republic of Congo",
    "DRC": "Democratic Republic of Congo",
    "CAR": "Central African Republic",
    "Syrian Arab Republic": "Syria",
    "occupied Palestinian territory": "Palestine",
    "State of Palestine": "Palestine",
    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Iran (Islamic Republic of)": "Iran",
    "Tanzania": "United Republic of Tanzania",
    "Moldova": "Republic of Moldova",
    "Bolivia": "Bolivia",
}

def load_env():
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("TAVILY_API_KEY", "ACLED_API_KEY", "ACLED_EMAIL", "NASA_API_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env

def http_json(url, data=None, headers=None, method="GET"):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Content-Type": "application/json", "User-Agent": "EII/1.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def tavily_news(key, query, days=60, max_results=10):
    out = http_json("https://api.tavily.com/search", method="POST", data={
        "api_key": key, "query": query, "topic": "news",
        "days": days, "max_results": max_results,
        "include_answer": True, "search_depth": "basic",
    })
    items = []
    for r in out.get("results", []):
        items.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "date": r.get("published_date"),
            "snippet": (r.get("content") or "")[:260],
            "source": urllib.parse.urlparse(r.get("url", "")).netloc.replace("www.", ""),
        })
    return {"answer": out.get("answer"), "items": items}

def acled_timeline(key, email, country, months=18):
    name = ACLED_ALIAS.get(country, country)
    since = (datetime.utcnow() - timedelta(days=months * 31)).strftime("%Y-%m-%d")
    url = "https://api.acleddata.com/acled/read?" + urllib.parse.urlencode({
        "key": key, "email": email, "country": name,
        "event_date": since, "event_date_where": ">=",
        "fields": "event_date|event_type|fatalities", "limit": 5000,
    })
    out = http_json(url)
    buckets, types = {}, {}
    for e in out.get("data", []):
        m = (e.get("event_date") or "")[:7]
        if not m:
            continue
        b = buckets.setdefault(m, {"month": m, "events": 0, "fatalities": 0})
        b["events"] += 1
        try:
            b["fatalities"] += int(e.get("fatalities") or 0)
        except (TypeError, ValueError):
            pass
        t = e.get("event_type") or "Other"
        types[t] = types.get(t, 0) + 1
    return {
        "country_used": name,
        "months": sorted(buckets.values(), key=lambda x: x["month"]),
        "by_type": sorted(types.items(), key=lambda x: -x[1]),
        "total_events": sum(b["events"] for b in buckets.values()),
        "total_fatalities": sum(b["fatalities"] for b in buckets.values()),
    }

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass  # quiet

    def send_json(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/api/detail"):
            return self.api_detail()
        if self.path.startswith("/api/earth-image"):
            return self.api_earth_image()
        if self.path.startswith("/api/usage"):
            return self.api_usage()
        return super().do_GET()

    def api_earth_image(self):
        """Proxy NASA's keyed Earth Imagery API -> a Landsat snapshot for one
        location. Key stays server-side; image bytes are disk-cached (the NASA
        endpoint is slow), and any failure returns JSON so the client hides it."""
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        try:
            lat = float((q.get("lat") or [""])[0])
            lon = float((q.get("lon") or [""])[0])
        except ValueError:
            return self.send_json({"error": "bad_coords"}, 400)
        dim = (q.get("dim") or ["0.5"])[0]
        key = load_env().get("NASA_API_KEY")
        if not key:
            return self.send_json({"error": "no_nasa_key"}, 404)
        cpath = os.path.join(CACHE_DIR, "img_" + hashlib.sha1(
            f"earth|{lat}|{lon}|{dim}".encode()).hexdigest()[:16] + ".png")
        data = None
        if os.path.exists(cpath) and time.time() - os.path.getmtime(cpath) < 7 * 86400:
            try:
                data = open(cpath, "rb").read()
            except Exception:
                data = None
        if data is None:
            url = "https://api.nasa.gov/planetary/earth/imagery?" + urllib.parse.urlencode(
                {"lon": lon, "lat": lat, "dim": dim, "api_key": key})
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "EII/1.0"})
                with urllib.request.urlopen(req, timeout=35) as r:
                    ctype = r.headers.get("Content-Type", "")
                    data = r.read()
                if not ctype.startswith("image"):
                    return self.send_json(
                        {"error": "nasa_no_image",
                         "detail": data[:200].decode("utf-8", "ignore")}, 502)
                os.makedirs(CACHE_DIR, exist_ok=True)
                open(cpath, "wb").write(data)
                usage_bump("earth_image")
            except Exception as e:
                return self.send_json({"error": "nasa_unreachable", "detail": str(e)}, 502)
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Cache-Control", "public, max-age=604800")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def api_usage(self):
        """Report API spend so the user can watch their Tavily credits."""
        self.send_json({
            "total": usage_read(),          # cumulative across all runs (persisted)
            "session": SESSION_USAGE,        # since this server process started
            "note": "Tavily basic search = 1 API credit. Cached results (≤6h) cost 0. "
                    "Check your monthly credit limit at app.tavily.com.",
        })

    def api_detail(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        crisis = (q.get("crisis") or [""])[0]
        country = (q.get("country") or [""])[0]
        try:
            days = max(1, min(365, int((q.get("days") or ["60"])[0])))
        except ValueError:
            days = 60
        env = load_env()
        tk = env.get("TAVILY_API_KEY")
        ak, ae = env.get("ACLED_API_KEY"), env.get("ACLED_EMAIL")
        nocache = "nocache" in q
        ckey = f"{crisis}|{country}|d{days}|t{bool(tk)}|a{bool(ak and ae)}"
        if not nocache:
            hit = cache_get(ckey)
            if hit:
                hit["cached"] = True
                return self.send_json(hit)
        resp = {"crisis": crisis, "country": country, "cached": False, "days": days,
                "tavily": None, "acled": None, "errors": [], "keys": {}}
        resp["keys"]["tavily"] = bool(tk)
        if tk:
            try:
                resp["tavily"] = tavily_news(
                    tk, f"{country} {crisis} latest conflict, security and humanitarian developments",
                    days=days)
                usage_bump("tavily")  # a real search credit was spent
            except Exception as e:
                resp["errors"].append(f"tavily: {e}")
        else:
            resp["errors"].append("no_tavily_key")
        resp["keys"]["acled"] = bool(ak and ae)
        if ak and ae:
            try:
                resp["acled"] = acled_timeline(ak, ae, country)
                usage_bump("acled")
            except Exception as e:
                resp["errors"].append(f"acled: {e}")
        else:
            resp["errors"].append("no_acled_key")
        if resp.get("tavily") or resp.get("acled"):
            cache_set(ckey, resp)  # only cache real data
        self.send_json(resp)

if __name__ == "__main__":
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"EII backend on http://localhost:{PORT}  (LAN + /api/detail live)")
    httpd.serve_forever()
