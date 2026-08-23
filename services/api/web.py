"""The viewer's pins and static files (E5.3 commit 1).

TOOL HASHES, RECORDED, ASSERTED WITHOUT A NETWORK. The page loads two
libraries from a CDN with exact versions and Subresource Integrity. E5.0
observed "latest" resolving differently across two CDNs — the supply-chain
argument made concrete — so the versions are exact, and the integrity
hashes are recorded HERE (a tool hash, not data: the quantile-forest
precedent, E2.3, Karl 2026-08-14) and `tests/test_viewer_model.py` asserts
the page's `integrity` attributes equal them with no network call. That
assertion is the only thing standing between a pinned dependency and a
silently-swapped one. Recomputing against the CDN is a deliberate command
(`openssl dgst -sha384 -binary | openssl base64 -A`), never a test.

Measured 2026-08-23 on unpkg AND jsdelivr, byte-identical on both:
  maplibre-gl@5.24.0/dist/maplibre-gl.js   1,056,837 B  (the last UMD build; 6.x is ESM-only — E5.0 §5)
  maplibre-gl@5.24.0/dist/maplibre-gl.css     70,024 B  (E5.0's 83,195 B was 6.5.0's CSS — corrected)
  deck.gl@9.3.10/dist.min.js               1,648,135 B

NO TILE BASEMAP (Karl's decision 3, 2026-08-23). Zero Natural Earth 110m
coastline features intersect the study extent (nearest coast 10.4° away;
five in the whole CCZ box), so a basemap here renders ocean and buys an
uptime dependency, a licence and a runtime fetch for nothing. The page
draws a dark background, a graticule, and the VENDORED Natural Earth 110m
coastline — public domain, deterministic, offline-capable. It is the first
context geometry and the first vendored non-Python file; its hash and
citation are recorded here, and it sits under apps/web/, outside the origin
audit's walk (`git ls-files -- data tests/fixtures`; E5.0 §5, confirmed at
E5.3).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WEB_DIR = REPO_ROOT / "apps" / "web"
INDEX_HTML = WEB_DIR / "index.html"

CDN_PINS: tuple[dict, ...] = (
    {
        "package": "maplibre-gl", "version": "5.24.0", "license": "BSD-3-Clause",
        "url": "https://cdn.jsdelivr.net/npm/maplibre-gl@5.24.0/dist/maplibre-gl.js",
        "bytes": 1056837, "integrity": "sha384-5+cfbwT0iiub6VsQAdn6yz16nr6sDiQoHx6tm4O8OVYXHYOxcffFmCJBL0dgdvGp",
        "tag": "script",
    },
    {
        "package": "maplibre-gl", "version": "5.24.0", "license": "BSD-3-Clause",
        "url": "https://cdn.jsdelivr.net/npm/maplibre-gl@5.24.0/dist/maplibre-gl.css",
        "bytes": 70024, "integrity": "sha384-uTttxo/aOKbdE5RlD/SPzSDoDmNvGlUYPjONi2MN/b7c9HPSvW07OIuyP7uL6jxK",
        "tag": "link",
    },
    {
        "package": "deck.gl", "version": "9.3.10", "license": "MIT",
        "url": "https://cdn.jsdelivr.net/npm/deck.gl@9.3.10/dist.min.js",
        "bytes": 1648135, "integrity": "sha384-ShkZCI1SsjyiuEQSfDaj9OLN9xhntMrIMZsOcAEp1kQhFz1vqAGjN/IhnDY3EZ0I",
        "tag": "script",
    },
)

COASTLINE = {
    "file": "ne_110m_coastline.geojson",
    "sha256": "sha256:851f581ff5ffb844deed8ae1a9ce22e3c4bb3d74fa342cadb5d8e39b41ae7c3c",
    "bytes": 139907,
    "source": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_coastline.geojson",
    "citation": "Natural Earth, 1:110m coastline (naturalearthdata.com; nvkelso/natural-earth-vector), public domain",
    "license": "public domain",
    # the taxonomy's nearest class for a published, compiled cartographic product
    # held as a file with its hash: a CITED dataset, not a measurement this project
    # made — declared here because apps/web/ is outside the audit's walk
    "data_origin": "LITERATURE",
    "attribution_text": "Coastline: Natural Earth (public domain)",
    "role": "context geometry for the basemap — never a value layer; drawn as an outline",
}

# the only static files the API serves from apps/web/ — an allow-list, never a listing
STATIC_FILES: dict[str, str] = {
    "index.html": "text/html; charset=utf-8",
    COASTLINE["file"]: "application/geo+json",
}


def attribution() -> dict:
    return {
        "libraries": [f"{p['package']} {p['version']} ({p['license']})" for p in CDN_PINS if p["tag"] == "script"],
        "coastline": COASTLINE["attribution_text"],
        "basemap": "none — dark background and graticule (no tile service; E5.3 §0.5)",
    }
