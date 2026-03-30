#!/usr/bin/env python3
"""
Fetch and save an offline OSM road graph for Connaught Place (New Delhi).

Usage:
  python scripts/fetch_osm_connaught.py

This writes:
  apps/traffic-ai/data/osm_connaught_place.json
"""

import json
import os
import urllib.parse
import urllib.request


BBOX = (28.6225, 77.2064, 28.6405, 77.2270)  # south, west, north, east
HIGHWAYS = ["primary", "secondary", "tertiary"]

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

QUERY = f"""
[out:json][timeout:60];
(
  way["highway"~"{'|'.join(HIGHWAYS)}"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
);
out geom;
"""


def fetch_overpass():
    data = urllib.parse.urlencode({"data": QUERY}).encode("utf-8")
    req = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
    return json.loads(raw)


def main():
    print("Fetching OSM data from Overpass…")
    payload = fetch_overpass()
    elements = payload.get("elements", [])

    ways = []
    for el in elements:
        if el.get("type") != "way":
            continue
        geom = el.get("geometry") or []
        if len(geom) < 2:
            continue
        coords = [[p["lat"], p["lon"]] for p in geom if "lat" in p and "lon" in p]
        if len(coords) < 2:
            continue
        tags = el.get("tags", {})
        ways.append({
            "id": el.get("id"),
            "name": tags.get("name"),
            "highway": tags.get("highway"),
            "coords": coords,
        })

    output = {
        "meta": {
            "name": "Connaught Place (New Delhi)",
            "bbox": list(BBOX),
            "source": "overpass",
            "highways": HIGHWAYS,
        },
        "ways": ways,
    }

    out_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "apps", "traffic-ai", "data", "osm_connaught_place.json")
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f)

    print(f"Saved {len(ways)} ways to {out_path}")


if __name__ == "__main__":
    main()
