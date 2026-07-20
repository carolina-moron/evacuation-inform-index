# Connecting Microsoft HASTE (satellite damage assessment) to EII

[HASTE](https://aka.ms/HASTE) (Microsoft + Planet) turns satellite imagery into
AI **building/route damage maps**. EII can overlay those damage tiles on the Map
tab, so an evacuation assessment sees *what is physically destroyed* alongside
INFORM/ACLED/CERAI.

> **HASTE has no public API.** It is a self-hosted, Azure-oriented full stack
> (React UI, Python Azure Functions, GPU batch workers, Cosmos/Blob, a TiTiler
> tile server). You must run it yourself, then paste its damage-layer tile URL
> into EII. Nothing is faked — until you connect a deployment, the overlay is
> simply empty.

## 1. Run HASTE locally

Prerequisites (this is a heavy stack — plan accordingly):

- **Docker + Docker Compose** installed and running
- **~40–60 GB free disk** for images and data
- A **GPU** for real ML inference (`HASTE_ENABLE_GPU`); on a Mac, Docker has no
  GPU passthrough, so inference won't run — use a Linux/GPU host or Azure
- Planet imagery access for real disaster imagery

```bash
# Ethical-Tech-CoLab fork of microsoft/haste (kept alongside this index)
git clone https://github.com/Ethical-Tech-CoLab/haste.git
cd haste
docker compose -f docker/docker-compose.yml up
```

> This project uses a fork of HASTE — **[Ethical-Tech-CoLab/haste](https://github.com/Ethical-Tech-CoLab/haste)**
> (MIT, forked from [microsoft/haste](https://github.com/microsoft/haste)) — so the
> evacuation index and its damage-assessment backend live under the same org.

Local endpoints once it's up:

| Service | URL |
|---|---|
| HASTE web UI | http://localhost:4280 |
| REST API (via nginx/CORS proxy) | http://localhost:7071/api/ |
| TiTiler tile server (public) | http://localhost:7071/api/titiler/ |

## 2. Produce a damage layer

In the HASTE UI (http://localhost:4280): create a project for a disaster AOI,
add pre-/post-event Planet imagery, and run inference. HASTE generates four
layers per project — pre-event, post-disaster, **predicted damage**, and
**predictions** (colormap: green = intact, red = damaged).

## 3. Get the tile URL

Each layer is served by TiTiler as an XYZ template, e.g.:

```
http://localhost:7071/api/titiler/cog/tiles/WebMercatorQuad/{z}/{x}/{y}?scale=1&url=<COG_URL>&colormap=<...>
```

You can copy it from the HASTE UI, or from the API:

```
GET http://localhost:7071/api/GetVisualizerResults?...   ->  predictionsLayer.url
```

## 4. Overlay it in EII

On the EII **Map** tab, paste that URL into **🛰 Damage assessment (HASTE)** →
**Overlay**. It renders as a tile layer you can toggle in the layer control
(top-left) and adjust against the crisis markers. The URL is saved in your
browser (localStorage) for next time; **Clear** removes it.

EII reports the overlay's real state rather than assuming it: pasting a URL
shows **⏳ Requesting damage tiles…**, and the status only turns **🟢** once tiles
actually load. If none load it turns **🔴 not connected**; if some load and some
404 it turns **🟡 partial**, which is normal — TiTiler serves nothing outside the
project AOI, so pan to the disaster area.

## Mixed content (HTTPS → HTTP)

The dev compose uses wildcard CORS, but the transport still matters:

| EII served from | HASTE at | Works? |
|---|---|---|
| `python3 server.py` (http) | `http://localhost:7071` | ✅ yes |
| GitHub Pages (https) | `http://localhost:7071` | ⚠️ Chrome/Firefox yes (localhost is a trustworthy origin); **Safari blocks it** |
| GitHub Pages (https) | `http://<remote-host>` | ❌ blocked as mixed content — EII refuses the URL up front |

For a shared deployment, host HASTE on Azure behind **HTTPS** and paste that
public tile URL.
