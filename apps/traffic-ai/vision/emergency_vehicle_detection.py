"""
emergency_vehicle_detection.py
==============================
Detects emergency vehicles (ambulance, fire truck, police car) in traffic
camera feeds and triggers alerts for the green corridor system.

Detection strategy
------------------
YOLOv8 is trained on COCO, which does **not** have dedicated "ambulance" or
"fire truck" classes.  We use a two-tier approach:

  **Tier 1 — Direct class match**
      If a fine-tuned model with explicit emergency classes is loaded, use
      direct class names.

  **Tier 2 — Proxy heuristic (COCO fallback)**
      Map COCO classes to emergency vehicle *candidates*:
        • ``truck``  (class 7)  → possible fire truck
        • ``car``    (class 2)  → possible police car
      Then flag any detection whose confidence exceeds a high threshold as a
      *potential* emergency vehicle.  In a real deployment this would be
      augmented with colour / siren / marking analysis.

Usage
-----
    from vision.emergency_vehicle_detection import (
        detect_emergency_vehicle,
        detect_emergency_from_video,
    )

    result = detect_emergency_vehicle(frame)
    results = detect_emergency_from_video("data/sample_videos/emergency.mp4")

Standalone:
    python -m vision.emergency_vehicle_detection
    python vision/emergency_vehicle_detection.py
"""

import sys
import time
from typing import Dict, List, Any, Optional, Callable

import cv2
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# --- Direct emergency class names (for fine-tuned models) ---
EMERGENCY_CLASS_NAMES = {
    "ambulance":    "ambulance",
    "fire truck":   "fire_truck",
    "fire_truck":   "fire_truck",
    "firetruck":    "fire_truck",
    "police":       "police",
    "police car":   "police",
    "police_car":   "police",
}

# --- COCO proxy mapping (fallback for pretrained yolov8n) ---
# COCO class_id → candidate emergency type
# Since YOLOv8n-COCO has no "ambulance" class, we map large vehicles
# that resemble emergency vehicles to emergency candidates.
COCO_PROXY_MAP = {
    7: "ambulance",     # COCO "truck"  → potential ambulance / fire truck
    5: "ambulance",     # COCO "bus"    → potential ambulance (boxy shape)
    2: "police",        # COCO "car"    → potential police car
}

# Minimum confidence to flag a COCO proxy as an emergency candidate
# Lower threshold since we're using COCO proxies (no real ambulance class)
PROXY_CONFIDENCE_THRESHOLD = 0.45

# --- Visual styling ---
ALERT_COLOR   = (0, 0, 255)    # RED in BGR
BOX_THICKNESS = 3
FONT          = cv2.FONT_HERSHEY_SIMPLEX
BANNER_HEIGHT = 50


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: detect_emergency_vehicle  (single frame)
# ═══════════════════════════════════════════════════════════════════════════════

def detect_emergency_vehicle(
    frame: np.ndarray,
    model=None,
    confidence: float = 0.45,
) -> Dict[str, Any]:
    """
    Detect emergency vehicles in a single BGR frame.

    Parameters
    ----------
    frame : np.ndarray
        BGR image from OpenCV.
    model : ultralytics.YOLO, optional
        Pre-loaded YOLO model.  If ``None``, a new ``yolov8n.pt`` will
        be loaded (slow on first call).
    confidence : float
        Minimum detection confidence.

    Returns
    -------
    dict
        {
            "detected":       bool,
            "vehicle_type":   str | None,    # "ambulance" / "fire_truck" / "police"
            "confidence":     float | None,
            "bounding_box":   [x1, y1, x2, y2] | None,
            "all_detections": [              # every emergency hit in this frame
                {"vehicle_type": str, "confidence": float, "bounding_box": [...]},
                ...
            ]
        }
    """
    # ── Lazy-load model ─────────────────────────────────────────────────────
    if model is None:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")

    results = model(frame, conf=confidence, verbose=False)[0]
    class_names = results.names  # {id: "name", ...}

    all_detections: List[Dict[str, Any]] = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        cls_name = class_names.get(cls_id, "").lower()
        conf = float(box.conf[0])
        bbox = list(map(int, box.xyxy[0].tolist()))

        # ── Tier 1: direct match ────────────────────────────────────────────
        if cls_name in EMERGENCY_CLASS_NAMES:
            vtype = EMERGENCY_CLASS_NAMES[cls_name]
            all_detections.append({
                "vehicle_type": vtype,
                "confidence": round(conf, 3),
                "bounding_box": bbox,
            })
            continue

        # ── Tier 2: COCO proxy heuristic ────────────────────────────────────
        if cls_id in COCO_PROXY_MAP and conf >= PROXY_CONFIDENCE_THRESHOLD:
            vtype = COCO_PROXY_MAP[cls_id]
            all_detections.append({
                "vehicle_type": vtype,
                "confidence": round(conf, 3),
                "bounding_box": bbox,
            })

    # Build response — pick the highest-confidence detection as primary
    if all_detections:
        best = max(all_detections, key=lambda d: d["confidence"])
        return {
            "detected": True,
            "vehicle_type": best["vehicle_type"],
            "confidence": best["confidence"],
            "bounding_box": best["bounding_box"],
            "all_detections": all_detections,
        }

    return {
        "detected": False,
        "vehicle_type": None,
        "confidence": None,
        "bounding_box": None,
        "all_detections": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: draw alert overlay
# ═══════════════════════════════════════════════════════════════════════════════

def _draw_emergency_overlay(
    frame: np.ndarray,
    detections: List[Dict[str, Any]],
) -> np.ndarray:
    """
    Draw RED bounding boxes and a flashing alert banner on the frame.
    """
    h, w = frame.shape[:2]

    for det in detections:
        x1, y1, x2, y2 = det["bounding_box"]
        vtype = det["vehicle_type"]
        conf  = det["confidence"]

        # RED bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), ALERT_COLOR, BOX_THICKNESS)

        # Label above box
        label = f"{vtype.upper()} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, FONT, 0.7, 2)
        cv2.rectangle(frame, (x1, y1 - th - 12), (x1 + tw + 8, y1), ALERT_COLOR, -1)
        cv2.putText(frame, label, (x1 + 4, y1 - 6), FONT, 0.7, (255, 255, 255), 2)

    # ── Top banner: EMERGENCY VEHICLE DETECTED ──────────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, BANNER_HEIGHT), ALERT_COLOR, -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    banner_text = "!! EMERGENCY VEHICLE DETECTED !!"
    (tw, th), _ = cv2.getTextSize(banner_text, FONT, 0.9, 2)
    tx = (w - tw) // 2
    ty = (BANNER_HEIGHT + th) // 2
    cv2.putText(frame, banner_text, (tx, ty), FONT, 0.9, (255, 255, 255), 2)

    return frame


# ═══════════════════════════════════════════════════════════════════════════════
# ALERT: console alert & callback
# ═══════════════════════════════════════════════════════════════════════════════

def _fire_alert(
    detection: Dict[str, Any],
    frame_idx: int,
    callback: Optional[Callable[[Dict], None]] = None,
) -> None:
    """
    Print a console alert and optionally call a callback to integrate
    with the traffic signal optimizer / emergency route engine.
    """
    vtype = detection.get("vehicle_type", "unknown")
    conf  = detection.get("confidence", 0)
    icons = {
        "ambulance":  "🚑",
        "fire_truck": "🚒",
        "police":     "🚓",
    }
    icon = icons.get(vtype, "🚨")

    print(
        f"\n{icon}  ALERT — Emergency Vehicle Detected!"
        f"\n   Type:       {vtype}"
        f"\n   Confidence: {conf:.1%}"
        f"\n   Frame:      {frame_idx}"
        f"\n   → Activating Green Corridor …\n"
    )
    logger.warning(
        f"{icon} Emergency {vtype} detected (conf={conf:.2f}) at frame {frame_idx}"
    )

    if callback:
        callback(detection)


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: detect_emergency_from_video
# ═══════════════════════════════════════════════════════════════════════════════

def detect_emergency_from_video(
    video_path: str,
    confidence: float = 0.45,
    show: bool = True,
    max_frames: int = 0,
    frame_skip: int = 1,
    start_frame: int = 0,
    on_emergency: Optional[Callable[[Dict], None]] = None,
) -> List[Dict[str, Any]]:
    """
    Process a video file and detect emergency vehicles frame-by-frame.

    Parameters
    ----------
    video_path : str
        Path to the video file.
    confidence : float
        Minimum detection confidence.
    show : bool
        Display the annotated video in a window.
    max_frames : int
        Limit frames to process (0 = entire video).
    frame_skip : int
        Process every Nth frame for speed.
    start_frame : int
        Start reading at this frame index (file sources only).
    on_emergency : callable, optional
        Callback fired on first detection per "event" (after a cooldown).

    Returns
    -------
    list[dict]
        List of all emergency detections across the video, each entry:
        ``{"frame": int, "detection": dict}``
    """
    from ultralytics import YOLO

    logger.info(f"🎬 Loading emergency detection for: {video_path}")
    model = YOLO("yolov8n.pt")
    logger.info("Model loaded ✅")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info(f"Video: {int(cap.get(3))}×{int(cap.get(4))}, {fps:.0f} FPS, {total_frames} frames")

    if start_frame and total_frames > 0:
        safe_start = start_frame % total_frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, safe_start)
        logger.info(f"Starting at frame {safe_start} (requested {start_frame})")

    all_events: List[Dict[str, Any]] = []
    frame_idx = 0
    alert_cooldown = 0          # frames to wait before re-alerting
    COOLDOWN_FRAMES = int(fps * 3)  # suppress duplicate alerts for 3 seconds
    prev_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Frame skipping
        if frame_idx % frame_skip != 0:
            continue

        # ── Detect ───────────────────────────────────────────────────────────
        result = detect_emergency_vehicle(frame, model=model, confidence=confidence)

        # ── FPS ──────────────────────────────────────────────────────────────
        curr_time = time.time()
        current_fps = 1.0 / max(curr_time - prev_time, 1e-6)
        prev_time = curr_time

        if result["detected"]:
            # Draw alert overlay
            _draw_emergency_overlay(frame, result["all_detections"])

            # Record event
            all_events.append({"frame": frame_idx, "detection": result})

            # Fire alert (with cooldown to avoid spam)
            if alert_cooldown <= 0:
                _fire_alert(result, frame_idx, callback=on_emergency)
                alert_cooldown = COOLDOWN_FRAMES
        else:
            # No detection — show a calm status bar at bottom
            h, w = frame.shape[:2]
            cv2.putText(
                frame, "Scanning for emergency vehicles ...",
                (10, h - 15), FONT, 0.5, (180, 180, 180), 1,
            )

        alert_cooldown -= 1

        # ── FPS overlay (bottom-right) ───────────────────────────────────────
        h, w = frame.shape[:2]
        cv2.putText(
            frame, f"FPS: {current_fps:.1f}  Frame: {frame_idx}",
            (w - 250, h - 15), FONT, 0.5, (0, 255, 255), 1,
        )

        # ── Progress ─────────────────────────────────────────────────────────
        sys.stdout.write(
            f"\rFrame {frame_idx:>5}/{total_frames}  "
            f"Emergencies: {len(all_events):>3}  "
            f"FPS: {current_fps:>5.1f}"
        )
        sys.stdout.flush()

        # ── Display ──────────────────────────────────────────────────────────
        if show:
            cv2.imshow("Emergency Vehicle Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("User pressed 'q' — stopping.")
                break

        if max_frames > 0 and frame_idx >= max_frames:
            break

    cap.release()
    if show:
        cv2.destroyAllWindows()

    print()
    logger.info(f"Done — {frame_idx} frames processed, {len(all_events)} emergency detections.")
    return all_events


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: detect from camera (live feed)
# ═══════════════════════════════════════════════════════════════════════════════

def detect_emergency_from_camera(
    camera_id: int = 0,
    confidence: float = 0.45,
    show: bool = True,
    max_frames: int = 0,
    on_emergency: Optional[Callable[[Dict], None]] = None,
) -> List[Dict[str, Any]]:
    """
    Run emergency detection on a live webcam / USB camera feed.

    Parameters
    ----------
    camera_id : int
        OpenCV camera index.
    confidence : float
        Minimum detection confidence.
    show : bool
        Display the live feed.
    max_frames : int
        Stop after N frames (0 = indefinite, quit with 'q').
    on_emergency : callable, optional
        Callback on detection.

    Returns
    -------
    list[dict]
        All emergency detection events.
    """
    from ultralytics import YOLO

    logger.info(f"📷 Starting live emergency detection on camera {camera_id}")
    model = YOLO("yolov8n.pt")

    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        logger.error(f"Cannot open camera {camera_id}")
        return []

    all_events: List[Dict[str, Any]] = []
    frame_idx = 0
    alert_cooldown = 0
    COOLDOWN_FRAMES = 90  # ~3 sec at 30 fps
    prev_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        result = detect_emergency_vehicle(frame, model=model, confidence=confidence)

        curr_time = time.time()
        current_fps = 1.0 / max(curr_time - prev_time, 1e-6)
        prev_time = curr_time

        if result["detected"]:
            _draw_emergency_overlay(frame, result["all_detections"])
            all_events.append({"frame": frame_idx, "detection": result})
            if alert_cooldown <= 0:
                _fire_alert(result, frame_idx, callback=on_emergency)
                alert_cooldown = COOLDOWN_FRAMES
        else:
            h, w = frame.shape[:2]
            cv2.putText(
                frame, "Scanning for emergency vehicles ...",
                (10, h - 15), FONT, 0.5, (180, 180, 180), 1,
            )

        alert_cooldown -= 1

        h, w = frame.shape[:2]
        cv2.putText(
            frame, f"FPS: {current_fps:.1f}  Frame: {frame_idx}",
            (w - 250, h - 15), FONT, 0.5, (0, 255, 255), 1,
        )

        if show:
            cv2.imshow("Emergency Vehicle Detection — LIVE", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        if max_frames > 0 and frame_idx >= max_frames:
            break

    cap.release()
    if show:
        cv2.destroyAllWindows()

    logger.info(f"Live session ended — {len(all_events)} detections in {frame_idx} frames.")
    return all_events


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST — python vision/emergency_vehicle_detection.py
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os
    import glob

    print("=" * 62)
    print("  🚨 Emergency Vehicle Detection Module (test mode)")
    print("=" * 62)

    # ── Integration callback demo ────────────────────────────────────────────
    def on_emergency_demo(detection: Dict):
        """
        This callback would normally call:
          emergency_route.generate_corridor(source, target)
          signal_optimizer.update_signal_plan(...)
        """
        print("  [CALLBACK] Would trigger green corridor for:", detection.get("vehicle_type"))

    # ── Look for sample video ────────────────────────────────────────────────
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_videos")
    videos = (
        glob.glob(os.path.join(sample_dir, "*emergency*"))
        + glob.glob(os.path.join(sample_dir, "*ambulance*"))
        + glob.glob(os.path.join(sample_dir, "*.mp4"))
        + glob.glob(os.path.join(sample_dir, "*.avi"))
    )
    # dedupe keeping order
    seen = set()
    unique_videos = []
    for v in videos:
        av = os.path.abspath(v)
        if av not in seen:
            seen.add(av)
            unique_videos.append(av)

    if unique_videos:
        video_path = unique_videos[0]
        print(f"\n▶ Using video: {video_path}\n")
        events = detect_emergency_from_video(
            video_path,
            confidence=0.45,
            show=True,
            on_emergency=on_emergency_demo,
        )
    else:
        print(f"\n⚠ No videos in {os.path.abspath(sample_dir)}")
        print("  Falling back to webcam.  Press 'q' to stop.\n")
        events = detect_emergency_from_camera(
            camera_id=0,
            confidence=0.45,
            show=True,
            on_emergency=on_emergency_demo,
        )

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  📊 DETECTION SUMMARY")
    print("=" * 62)
    print(f"  Total emergency events: {len(events)}")

    if events:
        types_found = set()
        for e in events:
            d = e["detection"]
            types_found.add(d.get("vehicle_type", "unknown"))
        print(f"  Types detected:         {', '.join(sorted(types_found))}")

        # Show first 5 events
        print("\n  First detections:")
        for e in events[:5]:
            d = e["detection"]
            print(
                f"    Frame {e['frame']:>5} │ "
                f"{d['vehicle_type']:<12} conf={d['confidence']:.2f}  "
                f"bbox={d['bounding_box']}"
            )

    print("=" * 62)
