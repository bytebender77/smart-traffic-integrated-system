"""
emergency_route.py
==================
Green corridor generator for emergency vehicles.

When an ambulance / fire truck / police car is detected, this module:
  1. Looks up the road network graph (``build_city_graph``).
  2. Computes the fastest route via **Dijkstra** (``calculate_fastest_route``).
  3. Generates a signal plan that turns every intersection along the
     route to GREEN (``generate_green_corridor``).
  4. Overrides the normal signal optimizer (``activate_emergency_mode``).
  5. Returns visualisation-ready coordinate data for the dashboard.

City graph model
----------------
  • **Nodes** = intersections, each with ``(lat, lon)`` for map display.
  • **Edges** = road segments, weighted by travel time in seconds.

Usage
-----
    from traffic_engine.emergency_route import (
        build_city_graph,
        calculate_fastest_route,
        generate_green_corridor,
        activate_emergency_mode,
    )

    graph = build_city_graph()
    route = calculate_fastest_route(graph, "A", "Hospital")
    corridor = generate_green_corridor(route, graph)
    override = activate_emergency_mode(route, graph)

Standalone test:
    python -m traffic_engine.emergency_route
    python traffic_engine/emergency_route.py
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import math
import os
import networkx as nx

from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CITY GRAPH — build_city_graph()
# ═══════════════════════════════════════════════════════════════════════════════

# Simulated GPS coordinates for dashboard map visualisation
# (lat, lon) — placed around a fictional downtown grid
INTERSECTION_COORDS: Dict[str, Tuple[float, float]] = {
    "A":        (28.6139, 77.2090),   # north-west
    "B":        (28.6145, 77.2120),   # north
    "C":        (28.6130, 77.2150),   # north-east
    "D":        (28.6110, 77.2090),   # west
    "E":        (28.6115, 77.2125),   # centre
    "F":        (28.6105, 77.2155),   # east
    "G":        (28.6090, 77.2100),   # south-west
    "H":        (28.6085, 77.2135),   # south
    "Hospital": (28.6070, 77.2160),   # south-east  (destination)
}

# Optional: load a precomputed OSM road graph (offline).
# If the file exists and contains ways, we use it instead of the toy grid.
OSM_DATA_PATH = os.getenv(
    "OSM_DATA_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "osm_connaught_place.json")),
)
OSM_GRAPH: Optional[nx.Graph] = None
OSM_WAYS: List[Dict[str, Any]] = []
OSM_NODE_COORDS: Dict[str, Tuple[float, float]] = {}
OSM_SPEED_MPS = float(os.getenv("OSM_SPEED_MPS", "8.0"))  # ~28.8 km/h

# Approximate destination coordinate (Connaught Place area center).
# Used when destination is "Hospital" and OSM graph is active.
DEFAULT_DESTINATION_COORDS = (28.6315, 77.2167)

# If enabled, each road edge is split into two smaller segments by inserting
# a midpoint node. This increases the number of nodes/waypoints so the
# emergency corridor looks more continuous on the dashboard map.
SPLIT_EDGES_INTO_MIDPOINTS: bool = False


def build_city_graph() -> nx.Graph:
    """
    Build a weighted undirected road network for the simulated city.
    If an offline OSM file exists, build a real-world graph instead.

    Returns
    -------
    nx.Graph
        Nodes carry ``pos`` (lat, lon) as metadata.
        Edges carry ``weight`` = travel time in seconds and ``distance``
        in metres (approximate).

    Graph layout::

        A ──── B ──── C
        │      │      │
        D ──── E ──── F
        │      │      │
        G ──── H ── Hospital

    TODO: Replace with real OpenStreetMap data via ``osmnx`` for production.
    """
    # Prefer OSM graph if available.
    osm_graph = _load_osm_graph()
    if osm_graph is not None:
        return osm_graph

    G = nx.Graph()

    # Midpoint dedup:
    # When we insert mid nodes for multiple edges, some midpoints may land on
    # the same (or extremely close) coordinates due to the simplified layout.
    # To avoid "two nodes at one point" on the map, we reuse an existing node
    # whenever its coordinates are within tolerance.
    def find_node_by_position(pos: Tuple[float, float], tol: float = 1e-6) -> Optional[str]:
        lat, lon = pos
        for nid, data in G.nodes(data=True):
            existing = data.get("pos")
            if not existing:
                continue
            elat, elon = existing
            if abs(elat - lat) <= tol and abs(elon - lon) <= tol:
                return nid
        return None

    # ── Add intersections (nodes) ────────────────────────────────────────────
    for node_id, (lat, lon) in INTERSECTION_COORDS.items():
        G.add_node(node_id, pos=(lat, lon))

    # ── Add roads (edges) ────────────────────────────────────────────────────
    # (node_a, node_b, travel_time_seconds, distance_metres)
    roads = [
        # Row 1: A — B — C
        ("A", "B", 30, 400),
        ("B", "C", 25, 350),
        # Row 2: D — E — F
        ("D", "E", 20, 300),
        ("E", "F", 25, 350),
        # Row 3: G — H — Hospital
        ("G", "H", 30, 400),
        ("H", "Hospital", 20, 280),
        # Column 1: A — D — G
        ("A", "D", 35, 450),
        ("D", "G", 30, 400),
        # Column 2: B — E — H
        ("B", "E", 25, 350),
        ("E", "H", 20, 280),
        # Column 3: C — F — Hospital
        ("C", "F", 30, 380),
        ("F", "Hospital", 25, 320),
        # Diagonal shortcut: A — E (fast inner road)
        ("A", "E", 22, 280),
        # Diagonal shortcut: E — Hospital
        ("E", "Hospital", 35, 500),
        # Extra cross-town shortcuts to create more routing alternatives
        ("B", "D", 28, 420),
        ("C", "E", 18, 260),
        ("B", "F", 30, 450),
        ("E", "G", 20, 300),
        ("F", "H", 18, 250),
        ("D", "H", 28, 420),
    ]

    def midpoint(n1: str, n2: str) -> Tuple[float, float]:
        p1 = G.nodes[n1]["pos"]
        p2 = G.nodes[n2]["pos"]
        return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    for u, v, travel_time, distance in roads:
        if not SPLIT_EDGES_INTO_MIDPOINTS:
            G.add_edge(u, v, weight=travel_time, distance=distance)
            continue

        mid_id = f"{u}_{v}_mid"
        mid_lat, mid_lon = midpoint(u, v)

        # Reuse an existing node if another midpoint already exists here.
        existing_mid = find_node_by_position((mid_lat, mid_lon))
        if existing_mid and existing_mid not in (u, v):
            mid_id = existing_mid
        else:
            # If it didn't already exist, create it.
            G.add_node(mid_id, pos=(mid_lat, mid_lon))

        half_time = travel_time / 2.0
        half_dist = distance / 2.0
        G.add_edge(u, mid_id, weight=half_time, distance=half_dist)
        G.add_edge(mid_id, v, weight=half_time, distance=half_dist)

    logger.info(
        f"City graph built — {G.number_of_nodes()} intersections, "
        f"{G.number_of_edges()} road segments"
    )
    return G


# ═══════════════════════════════════════════════════════════════════════════════
# OSM GRAPH LOADER (offline precomputed)
# ═══════════════════════════════════════════════════════════════════════════════

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters (Haversine)."""
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _load_osm_graph() -> Optional[nx.Graph]:
    """Load an offline OSM road graph from JSON if available."""
    global OSM_GRAPH, OSM_WAYS, OSM_NODE_COORDS

    if OSM_GRAPH is not None:
        return OSM_GRAPH

    if not os.path.exists(OSM_DATA_PATH):
        logger.info("OSM data file not found; using synthetic city graph.")
        return None

    try:
        with open(OSM_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load OSM data: {e}")
        return None

    ways = data.get("ways", [])
    if not ways:
        logger.info("OSM data file is empty; using synthetic city graph.")
        return None

    G = nx.Graph()
    node_id_by_coord: Dict[Tuple[float, float], str] = {}
    node_coords: Dict[str, Tuple[float, float]] = {}
    next_id = 1

    def get_node_id(lat: float, lon: float) -> str:
        nonlocal next_id
        key = (round(lat, 6), round(lon, 6))
        if key not in node_id_by_coord:
            nid = f"N{next_id}"
            next_id += 1
            node_id_by_coord[key] = nid
            node_coords[nid] = key
            G.add_node(nid, pos=key)
        return node_id_by_coord[key]

    osm_ways: List[Dict[str, Any]] = []

    for way in ways:
        coords = way.get("coords") or way.get("geometry") or []
        if len(coords) < 2:
            continue
        # Ensure [lat, lon] format
        cleaned = []
        for c in coords:
            if isinstance(c, dict):
                cleaned.append([c.get("lat"), c.get("lon")])
            else:
                cleaned.append(c)
        coords = [c for c in cleaned if c and c[0] is not None and c[1] is not None]
        if len(coords) < 2:
            continue

        total_dist = 0.0
        prev_id = None
        prev_coord = None
        first_id = None
        for lat, lon in coords:
            nid = get_node_id(lat, lon)
            if first_id is None:
                first_id = nid
            if prev_id and prev_coord:
                dist = _haversine_m(prev_coord[0], prev_coord[1], lat, lon)
                travel_time = dist / OSM_SPEED_MPS if OSM_SPEED_MPS > 0 else dist
                total_dist += dist
                G.add_edge(
                    prev_id,
                    nid,
                    weight=travel_time,
                    distance=dist,
                    highway=way.get("highway"),
                    name=way.get("name"),
                )
            prev_id = nid
            prev_coord = (lat, lon)

        osm_ways.append({
            "from": first_id,
            "to": prev_id,
            "coordinates": coords,
            "name": way.get("name"),
            "highway": way.get("highway"),
            "distance": round(total_dist, 1),
        })

    OSM_GRAPH = G
    OSM_WAYS = osm_ways
    OSM_NODE_COORDS = node_coords

    logger.info(
        f"OSM graph loaded — {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
    )
    return OSM_GRAPH


def get_osm_ways() -> List[Dict[str, Any]]:
    """Return OSM polylines for rendering (if available)."""
    _load_osm_graph()
    return OSM_WAYS


def get_map_intersections(max_nodes: int = 90) -> List[str]:
    """Return a reduced set of intersection nodes for map display."""
    graph = _load_osm_graph()
    if graph is None:
        return list(build_city_graph().nodes)

    # Prefer higher-degree nodes (likely intersections).
    degree_sorted = sorted(graph.degree, key=lambda x: -x[1])
    candidates = [n for n, deg in degree_sorted if deg >= 3]
    if not candidates:
        candidates = [n for n, _ in degree_sorted]
    return candidates[:max_nodes]


def _nearest_node(graph: nx.Graph, lat: float, lon: float) -> Optional[str]:
    """Find nearest graph node to a coordinate."""
    best_id = None
    best_dist = float("inf")
    for nid, data in graph.nodes(data=True):
        pos = data.get("pos")
        if not pos:
            continue
        d = _haversine_m(lat, lon, pos[0], pos[1])
        if d < best_dist:
            best_dist = d
            best_id = nid
    return best_id

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTE: calculate_fastest_route()
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_fastest_route(
    graph: nx.Graph,
    start: str,
    destination: str = "Hospital",
) -> List[str]:
    """
    Compute the fastest route (minimum travel time) using **Dijkstra**.

    Parameters
    ----------
    graph : nx.Graph
        City road network from ``build_city_graph()``.
    start : str
        Source intersection ID.
    destination : str
        Target intersection ID (default ``"Hospital"``).

    Returns
    -------
    list[str]
        Ordered list of intersection IDs forming the shortest path.
        Empty list if no path exists.
    """
    try:
        start_node = start
        dest_node = destination
        if start_node not in graph:
            # If unknown start, try to resolve to nearest OSM node (fallback).
            start_node = _nearest_node(graph, DEFAULT_DESTINATION_COORDS[0], DEFAULT_DESTINATION_COORDS[1])
        if dest_node not in graph and destination == "Hospital":
            dest_node = _nearest_node(graph, DEFAULT_DESTINATION_COORDS[0], DEFAULT_DESTINATION_COORDS[1])
        if not start_node or not dest_node:
            return []

        route = nx.dijkstra_path(graph, source=start_node, target=dest_node, weight="weight")
        travel_time = nx.dijkstra_path_length(graph, source=start_node, target=dest_node, weight="weight")
        logger.info(
            f"Fastest route: {' → '.join(route)}  "
            f"(estimated {travel_time}s)"
        )
        return route
    except nx.NetworkXNoPath:
        logger.error(f"No path from {start} to {destination}")
        return []
    except nx.NodeNotFound as e:
        logger.error(f"Node not found: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# CORRIDOR: generate_green_corridor()
# ═══════════════════════════════════════════════════════════════════════════════

def generate_green_corridor(
    route: List[str],
    graph: nx.Graph,
) -> Dict[str, Any]:
    """
    Create a signal override plan that turns every intersection on the
    emergency route to GREEN and everything else to RED.

    Parameters
    ----------
    route : list[str]
        Ordered intersection IDs from ``calculate_fastest_route()``.
    graph : nx.Graph
        City graph (used to enumerate all intersections).

    Returns
    -------
    dict
        {
            "corridor_signals": {
                "A": "GREEN",       ← on route
                "B": "GREEN",
                "D": "RED",         ← not on route
                ...
            },
            "route": ["A", "B", ...],
            "estimated_travel_time": int,     # seconds
            "total_distance": int,            # metres
        }
    """
    if not route:
        return {
            "corridor_signals": {},
            "route": [],
            "estimated_travel_time": 0,
            "total_distance": 0,
        }

    all_nodes = list(graph.nodes)
    route_set = set(route)

    # ── Signal plan ──────────────────────────────────────────────────────────
    corridor_signals: Dict[str, str] = {}
    for node in all_nodes:
        corridor_signals[node] = "GREEN" if node in route_set else "RED"

    # ── Travel stats ─────────────────────────────────────────────────────────
    travel_time = 0
    total_distance = 0
    for i in range(len(route) - 1):
        edge_data = graph.get_edge_data(route[i], route[i + 1], default={})
        travel_time += edge_data.get("weight", 0)
        total_distance += edge_data.get("distance", 0)

    logger.info(
        f"Green corridor → {len(route)} intersections GREEN, "
        f"{len(all_nodes) - len(route)} RED  "
        f"(ETA {travel_time}s, {total_distance}m)"
    )

    return {
        "corridor_signals": corridor_signals,
        "route": route,
        "estimated_travel_time": travel_time,
        "total_distance": total_distance,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# OVERRIDE: activate_emergency_mode()
# ═══════════════════════════════════════════════════════════════════════════════

def activate_emergency_mode(
    route: List[str],
    graph: nx.Graph,
) -> Dict[str, Any]:
    """
    Full emergency activation — generates the green corridor **and**
    produces all data needed by the signal controller and the dashboard.

    This is the single entry-point that the API / detection callback
    should call.

    Parameters
    ----------
    route : list[str]
        Emergency route from ``calculate_fastest_route()``.
    graph : nx.Graph
        City graph.

    Returns
    -------
    dict
        {
            "status": "EMERGENCY_ACTIVE",
            "corridor": { ...green_corridor dict... },
            "visualization": {
                "route_coords": [(lat, lon), ...],
                "all_intersection_coords": { id: (lat, lon), ...},
                "red_intersections": [ids...],
                "green_intersections": [ids...],
            },
        }
    """
    logger.warning("🚨 EMERGENCY MODE ACTIVATED")

    # ── Corridor ─────────────────────────────────────────────────────────────
    corridor = generate_green_corridor(route, graph)

    # ── Visualisation data ───────────────────────────────────────────────────
    route_coords = []
    for node in route:
        pos = graph.nodes[node].get("pos")
        if pos:
            route_coords.append({"id": node, "lat": pos[0], "lon": pos[1]})

    all_coords = {}
    for node in graph.nodes:
        pos = graph.nodes[node].get("pos")
        if pos:
            all_coords[node] = {"lat": pos[0], "lon": pos[1]}

    green_intersections = [n for n, s in corridor["corridor_signals"].items() if s == "GREEN"]
    red_intersections   = [n for n, s in corridor["corridor_signals"].items() if s == "RED"]

    result = {
        "status": "EMERGENCY_ACTIVE",
        "corridor": corridor,
        "visualization": {
            "route_coords": route_coords,
            "all_intersection_coords": all_coords,
            "green_intersections": green_intersections,
            "red_intersections": red_intersections,
        },
    }

    logger.warning(
        f"🚑 Green corridor: {' → '.join(route)}  |  "
        f"ETA {corridor['estimated_travel_time']}s  |  "
        f"{corridor['total_distance']}m"
    )

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: deactivate emergency mode
# ═══════════════════════════════════════════════════════════════════════════════

def deactivate_emergency_mode(graph: nx.Graph) -> Dict[str, str]:
    """
    Reset all intersections back to normal (signal optimizer takes over).

    Returns
    -------
    dict
        { intersection_id: "NORMAL", ... }
    """
    normal_state = {node: "NORMAL" for node in graph.nodes}
    logger.info("✅ Emergency mode deactivated — signals returned to normal")
    return normal_state


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST — python traffic_engine/emergency_route.py
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    print("=" * 62)
    print("  🚨 Emergency Route Engine (test mode)")
    print("=" * 62)

    # ── Build city ───────────────────────────────────────────────────────────
    print("\n🏙️  Building city road network …")
    city = build_city_graph()
    print(f"   Intersections: {list(city.nodes)}")
    print(f"   Roads:         {city.number_of_edges()}")

    # ── Scenario 1: Ambulance at A → Hospital ────────────────────────────────
    print("\n" + "─" * 62)
    print("  🚑 SCENARIO 1 — Ambulance at intersection A → Hospital")
    print("─" * 62)

    route = calculate_fastest_route(city, "A", "Hospital")
    if route:
        print(f"\n  ✅ Route: {' → '.join(route)}")

        result = activate_emergency_mode(route, city)
        corridor = result["corridor"]

        print(f"\n  🕐 Estimated travel time: {corridor['estimated_travel_time']}s")
        print(f"  📏 Total distance:        {corridor['total_distance']}m")

        print("\n  🚦 Signal states:")
        for intersection, signal in corridor["corridor_signals"].items():
            icon = "🟢" if signal == "GREEN" else "🔴"
            print(f"     {icon} {intersection:<12} → {signal}")

        print("\n  🗺️  Route coordinates (for dashboard map):")
        for point in result["visualization"]["route_coords"]:
            print(f"     📍 {point['id']:<12} ({point['lat']:.4f}, {point['lon']:.4f})")

    # ── Scenario 2: Fire truck at G → Hospital ───────────────────────────────
    print("\n" + "─" * 62)
    print("  🚒 SCENARIO 2 — Fire truck at intersection G → Hospital")
    print("─" * 62)

    route2 = calculate_fastest_route(city, "G", "Hospital")
    if route2:
        print(f"\n  ✅ Route: {' → '.join(route2)}")
        result2 = activate_emergency_mode(route2, city)
        print(f"  🕐 ETA: {result2['corridor']['estimated_travel_time']}s")

        print("\n  🚦 Signal states:")
        for intersection, signal in result2["corridor"]["corridor_signals"].items():
            icon = "🟢" if signal == "GREEN" else "🔴"
            print(f"     {icon} {intersection:<12} → {signal}")

    # ── Deactivate ───────────────────────────────────────────────────────────
    print("\n" + "─" * 62)
    print("  ✅ Deactivating emergency mode …")
    normal = deactivate_emergency_mode(city)
    print(f"  All intersections reset: {list(normal.values())[0]}")

    print("\n" + "=" * 62)
    print("  ✅ All scenarios completed successfully")
    print("=" * 62)
