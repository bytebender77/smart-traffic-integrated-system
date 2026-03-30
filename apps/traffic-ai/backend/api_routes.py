"""
api_routes.py
=============
All FastAPI route definitions for the Traffic AI system.

Endpoints
---------
  Health
    GET   /health               → system heartbeat

  Traffic Detection & Analysis
    POST  /traffic/detect       → run vehicle detection on a video
    POST  /traffic/density      → compute density from vehicle counts
    POST  /traffic/signals      → optimise signal timings from density data

  Emergency
    POST  /emergency/check      → detect emergency vehicles in a video
    POST  /emergency/route      → compute green corridor
    POST  /emergency/check/upload → upload video for emergency detection

  System
    GET   /system/status        → global system state
    POST  /system/reset         → clear emergency mode
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import os
import shutil

from backend.config import DEFAULT_LANE_CAPACITY, CYCLE_TIME, UPLOAD_DIR
from traffic_engine.density_calculator import (
    calculate_density,
    calculate_intersection_density,
)
from traffic_engine.signal_optimizer import (
    optimize_signal_timings,
    generate_signal_sequence,
    update_signal_plan,
)
from traffic_engine.emergency_route import (
    build_city_graph,
    calculate_fastest_route,
    generate_green_corridor,
    activate_emergency_mode,
    deactivate_emergency_mode,
    get_osm_ways,
    get_map_intersections,
)
from utils.logger import get_logger
from vision.vehicle_detection import stream_vehicle_detection

logger = get_logger(__name__)
router = APIRouter()


def _parse_video_source(value: str):
    """
    Accept file paths, RTSP/HTTP URLs, or camera identifiers.

    Supported formats:
      - /path/to/video.mp4 (must exist)
      - rtsp://user:pass@host:port/stream
      - http(s)://...
      - camera:0 (USB/webcam index)
      - "0" (camera index shorthand)
    """
    if value is None or str(value).strip() == "":
        raise HTTPException(status_code=400, detail="Missing video_path/source.")

    source = str(value).strip()
    if source.startswith("camera:"):
        camera_id = source.split("camera:", 1)[1].strip()
        if not camera_id.isdigit():
            raise HTTPException(status_code=400, detail="Invalid camera id. Use camera:0.")
        return int(camera_id)

    if source.isdigit():
        return int(source)

    if source.lower().startswith(("rtsp://", "http://", "https://")):
        return source

    if os.path.isfile(source):
        return source

    raise HTTPException(status_code=404, detail=f"Video source not found: {source}")


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL STATE — shared across requests (in-memory for hackathon)
# ═══════════════════════════════════════════════════════════════════════════════

city_graph = build_city_graph()

system_state = {
    "traffic_state": "NORMAL",                   # NORMAL | CONGESTED | EMERGENCY
    "emergency_mode": False,
    "active_intersections": city_graph.number_of_nodes(),
    "current_signal_plan": None,                  # latest signal plan dict
    "current_emergency_route": None,              # latest emergency corridor
    "last_density_data": None,                    # latest per-lane density
    "last_vehicle_counts": None,                  # latest detection output
}


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

# ── Traffic Detection ────────────────────────────────────────────────────────

class DetectRequest(BaseModel):
    """POST /traffic/detect — run vehicle detection on a file, RTSP/HTTP stream, or camera."""
    video_path: str = Field(..., description="File path, RTSP/HTTP URL, or camera:0")
    start_frame: int = Field(0, description="Start frame offset for file sources")
    max_frames: int = Field(30, description="Max frames to process")

class VehicleCounts(BaseModel):
    """Structured vehicle count output."""
    cars: int = 0
    buses: int = 0
    trucks: int = 0
    motorcycles: int = 0
    total_vehicles: int = 0


# ── Density ──────────────────────────────────────────────────────────────────

class DensityRequest(BaseModel):
    """POST /traffic/density — compute density from vehicle counts."""
    vehicle_counts: Dict[str, int] = Field(
        ...,
        example={"cars": 10, "buses": 2, "trucks": 3, "motorcycles": 5, "total_vehicles": 20},
    )
    lane_capacity: int = Field(DEFAULT_LANE_CAPACITY, description="Max PCU per lane")

class IntersectionDensityRequest(BaseModel):
    """POST /traffic/density/intersection — multi-lane density."""
    lane_data: Dict[str, Dict[str, int]] = Field(
        ...,
        example={
            "lane_A": {"cars": 10, "buses": 2, "trucks": 1, "motorcycles": 3, "total_vehicles": 16},
            "lane_B": {"cars": 5, "buses": 0, "trucks": 0, "motorcycles": 8, "total_vehicles": 13},
        },
    )
    lane_capacity: int = Field(DEFAULT_LANE_CAPACITY)


# ── Signal Optimisation ─────────────────────────────────────────────────────

class SignalRequest(BaseModel):
    """POST /traffic/signals — optimise signal timings."""
    lane_density_data: Dict[str, Dict[str, Any]] = Field(
        ...,
        example={
            "lane_A": {"density_percent": 85.0, "congestion_level": "HIGH", "speed_kmph": 18.5},
            "lane_B": {"density_percent": 45.0, "congestion_level": "MEDIUM", "speed_kmph": 28.0},
            "lane_C": {"density_percent": 20.0, "congestion_level": "LOW", "speed_kmph": 36.0},
        },
    )
    cycle_time: int = Field(CYCLE_TIME)


# ── Emergency ───────────────────────────────────────────────────────────────

class EmergencyCheckRequest(BaseModel):
    """POST /emergency/check — detect emergency vehicle in file, stream, or camera."""
    video_path: str = Field(..., description="File path, RTSP/HTTP URL, or camera:0")
    start_frame: int = Field(0, description="Start frame offset for file sources")
    max_frames: int = Field(60)

class EmergencyRouteRequest(BaseModel):
    """POST /emergency/route — compute green corridor."""
    start: str = Field(..., description="Source intersection ID", example="A")
    destination: str = Field("Hospital", description="Target intersection ID")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/health")
def health_check():
    """Health check — confirms the backend is running."""
    return {"status": "Traffic AI backend running"}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TRAFFIC DETECTION — POST /traffic/detect
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/traffic/detect")
def detect_vehicles(request: DetectRequest):
    """
    Run YOLOv8 vehicle detection on a video file.
    Returns per-frame average vehicle counts.
    """
    source = _parse_video_source(request.video_path)

    try:
        from vision.vehicle_detection import detect_vehicles_from_video

        counts = detect_vehicles_from_video(
            source,
            confidence=0.4,
            show=False,
            max_frames=request.max_frames,
            start_frame=request.start_frame,
        )

        # Update global state
        system_state["last_vehicle_counts"] = counts
        logger.info(f"/traffic/detect → {counts}")

        return counts

    except Exception as e:
        logger.error(f"/traffic/detect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/traffic/detect/upload")
async def detect_vehicles_upload(file: UploadFile = File(...)):
    """
    Upload a video file and run vehicle detection.
    The file is saved temporarily and processed.
    """
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        from vision.vehicle_detection import detect_vehicles_from_video

        counts = detect_vehicles_from_video(
            file_path, confidence=0.4, show=False, max_frames=30,
        )
        system_state["last_vehicle_counts"] = counts
        return counts

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/traffic/upload")
async def upload_traffic_video(file: UploadFile = File(...)):
    """
    Upload a video file and store it for live streaming.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"path": file_path}


@router.get("/traffic/stream")
def stream_traffic(
    request: Request,
    video_path: str = "",
    source: Optional[str] = None,
    confidence: float = 0.4,
    frame_skip: int = 1,
    max_frames: int = 0,
):
    """
    Stream live annotated traffic video with detection boxes.
    """
    selected_source = source or video_path
    parsed_source = _parse_video_source(selected_source)

    frame_generator = stream_vehicle_detection(
        parsed_source,
        confidence=confidence,
        max_frames=max_frames,
        frame_skip=frame_skip,
    )

    async def event_stream():
        try:
            for frame in frame_generator:
                if await request.is_disconnected():
                    break
                yield frame
        finally:
            try:
                frame_generator.close()
            except Exception:
                pass

    return StreamingResponse(event_stream(), media_type="multipart/x-mixed-replace; boundary=frame")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TRAFFIC DENSITY — POST /traffic/density
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/traffic/density")
def compute_density(request: DensityRequest):
    """
    Compute weighted traffic density from vehicle counts (single lane).
    """
    result = calculate_density(request.vehicle_counts, request.lane_capacity)
    system_state["last_density_data"] = result

    # Auto-update traffic state based on congestion
    level = result.get("congestion_level", "LOW")
    if level == "SEVERE":
        system_state["traffic_state"] = "CONGESTED"
    elif level in ("HIGH", "MEDIUM"):
        system_state["traffic_state"] = "MODERATE"
    else:
        system_state["traffic_state"] = "NORMAL"

    return result


@router.post("/traffic/density/intersection")
def compute_intersection_density(request: IntersectionDensityRequest):
    """
    Compute density across all lanes of an intersection.
    """
    result = calculate_intersection_density(request.lane_data, request.lane_capacity)
    system_state["last_density_data"] = result
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SIGNAL OPTIMISATION — POST /traffic/signals
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/traffic/signals")
def optimise_signals(request: SignalRequest):
    """
    Compute optimal signal timings from lane density data.
    Returns signal plan and rotation sequence.
    """
    plan = optimize_signal_timings(
        request.lane_density_data,
        cycle_time=request.cycle_time,
    )
    sequence = generate_signal_sequence(plan)

    system_state["current_signal_plan"] = plan

    return {
        "signal_plan": plan,
        "rotation_sequence": sequence,
    }


@router.post("/traffic/signals/update")
def update_signals(request: SignalRequest):
    """
    Re-optimise signal timings (real-time adaptation).
    Uses the current plan as baseline.
    """
    current = system_state.get("current_signal_plan")
    if current is None:
        # No existing plan — create one from scratch
        return optimise_signals(request)

    new_plan = update_signal_plan(current, request.lane_density_data)
    sequence = generate_signal_sequence(new_plan)

    system_state["current_signal_plan"] = new_plan

    return {
        "signal_plan": new_plan,
        "rotation_sequence": sequence,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EMERGENCY CHECK — POST /emergency/check
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/emergency/check")
def check_emergency(request: EmergencyCheckRequest):
    """
    Detect emergency vehicles in a video.
    Returns detection result and triggers alert if found.
    """
    source = _parse_video_source(request.video_path)

    try:
        from vision.emergency_vehicle_detection import detect_emergency_from_video

        events = detect_emergency_from_video(
            source,
            confidence=0.45,
            show=False,
            max_frames=request.max_frames,
            start_frame=request.start_frame,
        )

        if events:
            best = max(events, key=lambda e: e["detection"]["confidence"])
            detection = best["detection"]

            return {
                "detected": True,
                "vehicle_type": detection["vehicle_type"],
                "confidence": detection["confidence"],
                "total_detections": len(events),
                "message": f"🚨 Emergency vehicle ({detection['vehicle_type']}) detected!",
            }

        return {
            "detected": False,
            "vehicle_type": None,
            "confidence": None,
            "total_detections": 0,
            "message": "No emergency vehicles detected.",
        }

    except Exception as e:
        logger.error(f"/emergency/check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Emergency check (upload) ────────────────────────────────────────────────
@router.post("/emergency/check/upload")
async def check_emergency_upload(file: UploadFile = File(...)):
    """
    Upload a video file and run emergency vehicle detection.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        from vision.emergency_vehicle_detection import detect_emergency_from_video

        events = detect_emergency_from_video(
            file_path,
            confidence=0.45,
            show=False,
            max_frames=60,
        )

        if events:
            best = max(events, key=lambda e: e["detection"]["confidence"])
            detection = best["detection"]

            return {
                "detected": True,
                "vehicle_type": detection["vehicle_type"],
                "confidence": detection["confidence"],
                "total_detections": len(events),
                "message": f"🚨 Emergency vehicle ({detection['vehicle_type']}) detected!",
            }

        return {
            "detected": False,
            "vehicle_type": None,
            "confidence": None,
            "total_detections": 0,
            "message": "No emergency vehicles detected.",
        }

    except Exception as e:
        logger.error(f"/emergency/check/upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ═══════════════════════════════════════════════════════════════════════════════
# 6. GREEN CORRIDOR — POST /emergency/route
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/emergency/route")
def emergency_route(request: EmergencyRouteRequest):
    """
    Compute the fastest emergency route and activate the green corridor.
    Overrides the normal signal optimizer.
    """
    # ── Calculate route ──────────────────────────────────────────────────────
    # Use congestion-aware edge weights so the emergency corridor prefers
    # LOW / less congested nodes. We compute node density factors, then
    # apply them to each edge ONCE using the worst endpoint (max density),
    # so a single congested node on an edge makes that edge expensive.
    routing_graph = build_city_graph()

    all_nodes = {}
    try:
        all_nodes = sim_state.get("nodes", {})  # from traffic_simulator
    except Exception:
        all_nodes = {}

    density_by_node = {
        nid: (all_nodes.get(nid, {}).get("density_percent", 0) or 0)
        for nid in routing_graph.nodes
    }

    for u, v in routing_graph.edges:
        original_travel_time = routing_graph.edges[u, v]["weight"]
        max_density = max(density_by_node.get(u, 0), density_by_node.get(v, 0))
        congestion_factor = 1.0 + (max_density / 100.0)
        routing_graph.edges[u, v]["weight"] = original_travel_time * congestion_factor

    route = calculate_fastest_route(routing_graph, request.start, request.destination)
    if not route:
        raise HTTPException(
            status_code=404,
            detail=f"No route from {request.start} to {request.destination}",
        )

    # ── Activate emergency mode ──────────────────────────────────────────────
    result = activate_emergency_mode(route, routing_graph)

    # ── Update global state ──────────────────────────────────────────────────
    system_state["emergency_mode"] = True
    system_state["traffic_state"] = "EMERGENCY"
    system_state["current_emergency_route"] = result

    return {
        "route": result["corridor"]["route"],
        "signals": result["corridor"]["corridor_signals"],
        "estimated_travel_time": result["corridor"]["estimated_travel_time"],
        "total_distance": result["corridor"]["total_distance"],
        "visualization": result["visualization"],
        "message": f"🚑 Green corridor activated: {' → '.join(route)}",
    }


@router.post("/emergency/deactivate")
def deactivate_emergency():
    """
    Deactivate emergency mode and return signals to normal control.
    """
    deactivate_emergency_mode(city_graph)

    system_state["emergency_mode"] = False
    system_state["traffic_state"] = "NORMAL"
    system_state["current_emergency_route"] = None

    return {
        "status": "NORMAL",
        "message": "✅ Emergency mode deactivated — signals returned to normal",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 7. SYSTEM STATUS — GET /system/status
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/system/status")
def system_status():
    """
    Returns the current global state of the traffic system.
    """
    return {
        "active_intersections": system_state["active_intersections"],
        "traffic_state": system_state["traffic_state"],
        "emergency_mode": system_state["emergency_mode"],
        "has_signal_plan": system_state["current_signal_plan"] is not None,
        "has_emergency_route": system_state["current_emergency_route"] is not None,
    }


@router.get("/system/intersections")
def list_intersections():
    """
    Returns all intersections in the city graph with their coordinates.
    """
    intersections = []
    # Prefer a reduced set of OSM intersection nodes if available.
    node_ids = get_map_intersections()
    if not node_ids:
        node_ids = list(city_graph.nodes)

    for node in node_ids:
        pos = city_graph.nodes[node].get("pos")
        intersections.append({
            "id": node,
            "lat": pos[0] if pos else None,
            "lon": pos[1] if pos else None,
        })
    return {"intersections": intersections}


@router.get("/system/road-network")
def road_network():
    """
    Returns the simulated road network used by the routing engine.

    Output:
      {
        "edges": [
          { "from": "A", "to": "E", "coordinates": [[lat, lon],[lat, lon]], ... }
        ]
      }
    """
    edges = []
    osm_edges = get_osm_ways()
    if osm_edges:
        for way in osm_edges:
            coords = way.get("coordinates") or []
            if not coords:
                continue
            edges.append({
                "from": way.get("from"),
                "to": way.get("to"),
                "coordinates": coords,
                "weight": way.get("distance"),
                "distance": way.get("distance"),
                "name": way.get("name"),
                "highway": way.get("highway"),
            })
    else:
        for u, v, data in city_graph.edges(data=True):
            pos_u = city_graph.nodes[u].get("pos")
            pos_v = city_graph.nodes[v].get("pos")
            if not pos_u or not pos_v:
                continue
            edges.append({
                "from": u,
                "to": v,
                "coordinates": [
                    [pos_u[0], pos_u[1]],
                    [pos_v[0], pos_v[1]],
                ],
                "weight": data.get("weight"),
                "distance": data.get("distance"),
            })

    return {"edges": edges}


@router.get("/system/full-state")
def full_system_state():
    """
    Returns the complete system state including signal plans and density.
    For the dashboard to consume.
    """
    return {
        "status": system_state["traffic_state"],
        "emergency_mode": system_state["emergency_mode"],
        "active_intersections": system_state["active_intersections"],
        "signal_plan": system_state["current_signal_plan"],
        "emergency_route": system_state["current_emergency_route"],
        "last_density": system_state["last_density_data"],
        "last_vehicle_counts": system_state["last_vehicle_counts"],
    }


@router.post("/system/reset")
def reset_system():
    """
    Reset system to initial state — clears emergency mode, signal plans, etc.
    """
    system_state["traffic_state"] = "NORMAL"
    system_state["emergency_mode"] = False
    system_state["current_signal_plan"] = None
    system_state["current_emergency_route"] = None
    system_state["last_density_data"] = None
    system_state["last_vehicle_counts"] = None

    logger.info("System reset to initial state")
    return {"status": "RESET", "message": "System reset to initial state"}


# ═══════════════════════════════════════════════════════════════════════════════
# 8. TRAFFIC SIMULATION — for nodes without video feeds
# ═══════════════════════════════════════════════════════════════════════════════

from backend.traffic_simulator import (
    start_simulation,
    stop_simulation,
    get_simulation_state,
    set_override_node,
    update_node_with_real_data,
    run_simulation_tick,
    simulation_state as sim_state,
)


@router.get("/simulation/state")
def simulation_state_endpoint():
    """
    Returns the current simulation state with per-node vehicle counts,
    density, congestion levels, and signal plan.
    """
    return get_simulation_state()


@router.get("/simulation/start")
def simulation_start():
    """Start the background traffic simulator (updates every 5 seconds)."""
    result = start_simulation(interval=5.0)
    return result


@router.get("/simulation/stop")
def simulation_stop():
    """Stop the background traffic simulator."""
    result = stop_simulation()
    return result


@router.post("/simulation/override")
def simulation_override(node_id: str = ""):
    """Mark a node as using real video data (skip simulation for it)."""
    set_override_node(node_id if node_id else None)
    return {"override_node": node_id or None}


# ═══════════════════════════════════════════════════════════════════════════════
# 9. NODE-SPECIFIC VIDEO DETECTION — merges into simulation
# ═══════════════════════════════════════════════════════════════════════════════

class NodeDetectRequest(BaseModel):
    """POST /node/detect — detect vehicles for a specific intersection node."""
    node_id: str = Field(..., description="Intersection node ID (e.g. A, B, C...)")
    video_path: str = Field(..., description="Video file path, URL, or camera:0")
    max_frames: int = Field(30)
    start_frame: int = Field(0)


@router.post("/node/detect")
def detect_for_node(request: NodeDetectRequest):
    """
    Run vehicle detection on a video for a SPECIFIC intersection node.
    The result is merged into the simulation state, and signals are
    re-optimized across ALL nodes (real + simulated).
    """
    source = _parse_video_source(request.video_path)

    try:
        from vision.vehicle_detection import detect_vehicles_from_video

        counts = detect_vehicles_from_video(
            source,
            confidence=0.4,
            show=False,
            max_frames=request.max_frames,
            start_frame=request.start_frame,
        )

        normalized = {
            "cars": counts.get("cars", 0),
            "buses": counts.get("buses", 0),
            "trucks": counts.get("trucks", 0),
            "motorcycles": counts.get("motorcycles", 0),
            "total_vehicles": counts.get("total_vehicles", 0),
        }

        # Compute density for this node
        density = calculate_density(normalized, DEFAULT_LANE_CAPACITY)

        # Merge into simulation state
        set_override_node(request.node_id)
        update_node_with_real_data(request.node_id, normalized, density)

        # Re-optimize signals across ALL nodes
        all_nodes = sim_state.get("nodes", {})
        lane_density_data = {}
        for nid, ndata in all_nodes.items():
            lane_density_data[f"lane_{nid}"] = {
                "density_percent": ndata.get("density_percent", 0),
                "congestion_level": ndata.get("congestion_level", "LOW"),
                "speed_kmph": ndata.get("avg_speed_kmph"),
            }
        signal_plan = optimize_signal_timings(lane_density_data)
        sim_state["signal_plan"] = signal_plan

        # Update global system state
        system_state["last_vehicle_counts"] = normalized
        system_state["last_density_data"] = density

        logger.info(f"/node/detect -> node={request.node_id} counts={normalized}")

        return {
            "node_id": request.node_id,
            "vehicle_counts": normalized,
            "density": density,
            "signal_plan": signal_plan,
            "all_nodes": get_simulation_state()["nodes"],
        }

    except Exception as e:
        logger.error(f"/node/detect error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/node/detect/upload")
async def detect_for_node_upload(
    node_id: str = "A",
    file: UploadFile = File(...),
):
    """
    Upload a video for a SPECIFIC node. Detects vehicles, merges into
    simulation, re-optimizes signals across all nodes.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        from vision.vehicle_detection import detect_vehicles_from_video

        counts = detect_vehicles_from_video(
            file_path, confidence=0.4, show=False, max_frames=30,
        )

        normalized = {
            "cars": counts.get("cars", 0),
            "buses": counts.get("buses", 0),
            "trucks": counts.get("trucks", 0),
            "motorcycles": counts.get("motorcycles", 0),
            "total_vehicles": counts.get("total_vehicles", 0),
        }

        density = calculate_density(normalized, DEFAULT_LANE_CAPACITY)

        set_override_node(node_id)
        update_node_with_real_data(node_id, normalized, density)

        # Re-optimize across all nodes
        all_nodes = sim_state.get("nodes", {})
        lane_density_data = {}
        for nid, ndata in all_nodes.items():
            lane_density_data[f"lane_{nid}"] = {
                "density_percent": ndata.get("density_percent", 0),
                "congestion_level": ndata.get("congestion_level", "LOW"),
                "speed_kmph": ndata.get("avg_speed_kmph"),
            }
        signal_plan = optimize_signal_timings(lane_density_data)
        sim_state["signal_plan"] = signal_plan

        system_state["last_vehicle_counts"] = normalized
        system_state["last_density_data"] = density

        return {
            "node_id": node_id,
            "vehicle_counts": normalized,
            "density": density,
            "signal_plan": signal_plan,
            "all_nodes": get_simulation_state()["nodes"],
        }

    except Exception as e:
        logger.error(f"/node/detect/upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/node/emergency/upload")
async def emergency_for_node_upload(
    node_id: str = "A",
    destination: str = "Hospital",
    file: UploadFile = File(...),
):
    """
    Upload a video to check for emergency vehicles at a specific node.
    If detected, creates a green corridor from that node to the destination,
    using real traffic data from all nodes to determine the best route.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        from vision.emergency_vehicle_detection import detect_emergency_from_video

        events = detect_emergency_from_video(
            file_path, confidence=0.45, show=False, max_frames=60,
        )

        if not events:
            return {
                "detected": False,
                "node_id": node_id,
                "vehicle_type": None,
                "confidence": None,
                "message": "No emergency vehicles detected.",
            }

        best = max(events, key=lambda e: e["detection"]["confidence"])
        detection = best["detection"]

        # Build a FRESH graph so we don't permanently mutate the original
        # Then adjust edge weights based on congestion: higher density → higher
        # weight → Dijkstra avoids that path → ambulance goes through LOW traffic
        routing_graph = build_city_graph()
        all_nodes = sim_state.get("nodes", {})

        for nid in routing_graph.nodes:
            node_data = all_nodes.get(nid, {})
            density_pct = node_data.get("density_percent", 0)
            # Multiply edge weights by congestion factor:
            #   LOW (0-30%) → factor 1.0-1.3   (fast, preferred)
            #   MEDIUM (30-70%) → factor 1.3-1.7
            #   HIGH (70-100%) → factor 1.7-2.0
            #   SEVERE (100%+) → factor 2.0+   (slow, avoided)
            congestion_factor = 1.0 + (density_pct / 100.0)
            for neighbor in routing_graph.neighbors(nid):
                edge = routing_graph.edges[nid, neighbor]
                original_travel_time = edge["weight"]
                edge["weight"] = original_travel_time * congestion_factor

        logger.info(
            f"Emergency routing: adjusted weights using traffic density from "
            f"{len(all_nodes)} nodes"
        )

        # Calculate route through LEAST congested path and activate green corridor
        route = calculate_fastest_route(routing_graph, node_id, destination)
        if not route:
            return {
                "detected": True,
                "vehicle_type": detection["vehicle_type"],
                "confidence": detection["confidence"],
                "message": f"Emergency vehicle detected but no route from {node_id} to {destination}",
            }

        result = activate_emergency_mode(route, routing_graph)

        system_state["emergency_mode"] = True
        system_state["traffic_state"] = "EMERGENCY"
        system_state["current_emergency_route"] = result

        return {
            "detected": True,
            "node_id": node_id,
            "vehicle_type": detection["vehicle_type"],
            "confidence": detection["confidence"],
            "total_detections": len(events),
            "route": result["corridor"]["route"],
            "signals": result["corridor"]["corridor_signals"],
            "estimated_travel_time": result["corridor"]["estimated_travel_time"],
            "total_distance": result["corridor"]["total_distance"],
            "visualization": result["visualization"],
            "message": f"🚨 Emergency {detection['vehicle_type']} at {node_id}! Green corridor: {' → '.join(route)}",
        }

    except Exception as e:
        logger.error(f"/node/emergency/upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
