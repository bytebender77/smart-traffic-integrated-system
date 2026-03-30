"""
vehicle_detection.py
====================
Production-grade vehicle detection module for the Smart City Traffic AI system.

Uses YOLOv8 (Ultralytics) + OpenCV to detect and count vehicles from:
  • video files
  • webcam feeds
  • RTSP / traffic camera streams

Detected vehicle classes:
  car · bus · truck · motorcycle

Outputs:
  - Annotated video frames with bounding boxes, labels, and confidence
  - Per-frame structured vehicle counts
  - Real-time on-screen overlay (HUD) with running totals

Usage:
  # As a library
  from vision.vehicle_detection import detect_vehicles_from_video
  counts = detect_vehicles_from_video("data/sample_videos/traffic.mp4")

  # Standalone
  python vision/vehicle_detection.py
"""

import sys
import time
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# COCO class IDs that map to our target vehicle types
# Full COCO list: https://docs.ultralytics.com/datasets/detect/coco/
VEHICLE_CLASS_MAP: Dict[int, str] = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Distinct colours for each vehicle type (BGR for OpenCV)
VEHICLE_COLORS: Dict[str, Tuple[int, int, int]] = {
    "car":        (0, 200, 0),      # green
    "bus":        (0, 165, 255),     # orange
    "truck":      (255, 50, 50),     # blue
    "motorcycle": (200, 0, 200),     # magenta
}

# HUD styling
HUD_BG_ALPHA = 0.65
HUD_FONT = cv2.FONT_HERSHEY_SIMPLEX
HUD_FONT_SCALE = 0.65
HUD_THICKNESS = 2
HUD_LINE_HEIGHT = 30
HUD_MARGIN = 15


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: get_vehicle_counts
# ═══════════════════════════════════════════════════════════════════════════════

def get_vehicle_counts(results) -> Dict[str, int]:
    """
    Parse raw YOLOv8 results and return a structured vehicle count dictionary.

    Parameters
    ----------
    results : ultralytics.engine.results.Results
        A single YOLOv8 result object (one frame).

    Returns
    -------
    dict
        {
            "cars": int,
            "buses": int,
            "trucks": int,
            "motorcycles": int,
            "total_vehicles": int
        }
    """
    counts = {"cars": 0, "buses": 0, "trucks": 0, "motorcycles": 0}

    for box in results.boxes:
        cls_id = int(box.cls[0])
        if cls_id in VEHICLE_CLASS_MAP:
            vehicle_type = VEHICLE_CLASS_MAP[cls_id]
            # Map singular → plural key
            key = {
                "car": "cars",
                "bus": "buses",
                "truck": "trucks",
                "motorcycle": "motorcycles",
            }[vehicle_type]
            counts[key] += 1

    counts["total_vehicles"] = sum(counts.values())
    return counts


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: draw_vehicle_boxes
# ═══════════════════════════════════════════════════════════════════════════════

def draw_vehicle_boxes(
    frame: np.ndarray,
    results,
    confidence_threshold: float = 0.4,
) -> np.ndarray:
    """
    Draw bounding boxes, labels, and confidence scores on a frame.

    Parameters
    ----------
    frame : np.ndarray
        BGR image (OpenCV format).
    results : ultralytics.engine.results.Results
        YOLOv8 result for this frame.
    confidence_threshold : float
        Minimum confidence to draw a box.

    Returns
    -------
    np.ndarray
        The annotated frame (same array, mutated in place for speed).
    """
    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])

        # Skip non-vehicle classes and low-confidence detections
        if cls_id not in VEHICLE_CLASS_MAP or conf < confidence_threshold:
            continue

        vehicle_type = VEHICLE_CLASS_MAP[cls_id]
        color = VEHICLE_COLORS.get(vehicle_type, (255, 255, 255))

        # Bounding box coordinates
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # Draw the rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Label string: "car 0.92"
        label = f"{vehicle_type} {conf:.2f}"

        # Background rectangle for label readability
        (tw, th), _ = cv2.getTextSize(label, HUD_FONT, 0.5, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
        cv2.putText(frame, label, (x1 + 3, y1 - 5), HUD_FONT, 0.5, (255, 255, 255), 1)

    return frame


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: draw_hud_overlay
# ═══════════════════════════════════════════════════════════════════════════════

def _draw_hud_overlay(
    frame: np.ndarray,
    counts: Dict[str, int],
    fps: float = 0.0,
) -> np.ndarray:
    """
    Draw a translucent HUD overlay showing vehicle counts and FPS.

    Example:
        ┌─────────────────┐
        │ 🚦 VEHICLE COUNT │
        │  Cars:        12 │
        │  Buses:        3 │
        │  Trucks:       4 │
        │  Motorcycles:  7 │
        │  ──────────────  │
        │  Total:       26 │
        │  FPS:       29.8 │
        └─────────────────┘
    """
    lines = [
        "VEHICLE COUNT",
        f"  Cars:        {counts.get('cars', 0)}",
        f"  Buses:       {counts.get('buses', 0)}",
        f"  Trucks:      {counts.get('trucks', 0)}",
        f"  Motorcycles: {counts.get('motorcycles', 0)}",
        "  ──────────────",
        f"  Total:       {counts.get('total_vehicles', 0)}",
        f"  FPS:         {fps:.1f}",
    ]

    # Calculate overlay dimensions
    box_w = 240
    box_h = HUD_MARGIN * 2 + HUD_LINE_HEIGHT * len(lines)
    x_start, y_start = 10, 10

    # Semi-transparent dark background
    overlay = frame.copy()
    cv2.rectangle(overlay, (x_start, y_start), (x_start + box_w, y_start + box_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, HUD_BG_ALPHA, frame, 1 - HUD_BG_ALPHA, 0, frame)

    # Draw border
    cv2.rectangle(frame, (x_start, y_start), (x_start + box_w, y_start + box_h), (0, 200, 200), 1)

    # Draw text
    for i, line in enumerate(lines):
        y = y_start + HUD_MARGIN + (i + 1) * HUD_LINE_HEIGHT
        color = (0, 255, 255) if i == 0 else (220, 220, 220)
        scale = 0.7 if i == 0 else HUD_FONT_SCALE
        cv2.putText(frame, line, (x_start + 10, y), HUD_FONT, scale, color, HUD_THICKNESS if i == 0 else 1)

    return frame


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: _process_source  (shared logic for video / camera / stream)
# ═══════════════════════════════════════════════════════════════════════════════

def _process_source(
    source,
    confidence: float = 0.4,
    show: bool = True,
    max_frames: int = 0,
    frame_skip: int = 1,
    start_frame: int = 0,
) -> Dict[str, int]:
    """
    Internal workhorse. Opens a video source, runs YOLOv8 per frame, draws
    annotations, and returns the aggregated counts from the *last processed frame*.

    Parameters
    ----------
    source : str | int
        Path to video file, RTSP URL, or integer camera ID.
    confidence : float
        YOLO confidence threshold.
    show : bool
        Whether to display the annotated video window.
    max_frames : int
        Stop after this many frames (0 = unlimited / until video ends).
    frame_skip : int
        Process every Nth frame to boost FPS (1 = every frame).
    start_frame : int
        Start reading at this frame index (file sources only).

    Returns
    -------
    dict
        Final aggregated vehicle counts.
    """

    # ── Load YOLOv8 model ────────────────────────────────────────────────────
    from ultralytics import YOLO  # lazy import — heavy dependency
    logger.info("Loading YOLOv8 model …")
    model = YOLO("yolov8n.pt")  # auto-downloads ~6 MB nano model on first run
    logger.info("Model loaded ✅")

    # ── Open video source ────────────────────────────────────────────────────
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error(f"Cannot open video source: {source}")
        return {"cars": 0, "buses": 0, "trucks": 0, "motorcycles": 0, "total_vehicles": 0}

    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames_in_video = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if start_frame and total_frames_in_video > 0:
        safe_start = start_frame % total_frames_in_video
        cap.set(cv2.CAP_PROP_POS_FRAMES, safe_start)
        logger.info(f"Starting at frame {safe_start} (requested {start_frame})")
    logger.info(
        f"Source opened — resolution: {int(cap.get(3))}x{int(cap.get(4))}, "
        f"FPS: {src_fps:.1f}, frames: {total_frames_in_video}"
    )

    # ── Processing loop ──────────────────────────────────────────────────────
    latest_counts: Dict[str, int] = {}
    frame_idx = 0
    prev_time = time.time()
    fps = 0.0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Frame skipping for real-time performance
        if frame_idx % frame_skip != 0:
            continue

        # ── Run YOLOv8 inference ─────────────────────────────────────────────
        results = model(frame, conf=confidence, verbose=False)[0]

        # ── Count vehicles ───────────────────────────────────────────────────
        latest_counts = get_vehicle_counts(results)

        # ── Annotate frame ───────────────────────────────────────────────────
        draw_vehicle_boxes(frame, results, confidence_threshold=confidence)

        # ── FPS calculation ──────────────────────────────────────────────────
        curr_time = time.time()
        fps = 1.0 / max(curr_time - prev_time, 1e-6)
        prev_time = curr_time

        # ── HUD overlay ─────────────────────────────────────────────────────
        _draw_hud_overlay(frame, latest_counts, fps)

        # ── Display window ───────────────────────────────────────────────────
        if show:
            cv2.imshow("Traffic AI — Vehicle Detection", frame)
            # Press 'q' to quit early
            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("User pressed 'q' — stopping.")
                break

        # ── Print to console ─────────────────────────────────────────────────
        sys.stdout.write(
            f"\rFrame {frame_idx:>5} | "
            f"Cars: {latest_counts['cars']:>3}  "
            f"Buses: {latest_counts['buses']:>2}  "
            f"Trucks: {latest_counts['trucks']:>2}  "
            f"Motorcycles: {latest_counts['motorcycles']:>2}  "
            f"Total: {latest_counts['total_vehicles']:>3}  "
            f"FPS: {fps:>5.1f}"
        )
        sys.stdout.flush()

        # ── Frame limit ─────────────────────────────────────────────────────
        if max_frames > 0 and frame_idx >= max_frames:
            logger.info(f"Reached max_frames={max_frames}, stopping.")
            break

    # ── Cleanup ──────────────────────────────────────────────────────────────
    cap.release()
    if show:
        cv2.destroyAllWindows()

    print()  # newline after \r progress
    logger.info(f"Processing complete — {frame_idx} frames read.")
    logger.info(f"Final counts: {latest_counts}")

    return latest_counts


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def detect_vehicles_from_video(
    video_path: str,
    confidence: float = 0.4,
    show: bool = True,
    max_frames: int = 0,
    frame_skip: int = 1,
    start_frame: int = 0,
) -> Dict[str, int]:
    """
    Detect vehicles from a video file.

    Parameters
    ----------
    video_path : str
        Path to the video file (MP4, AVI, MOV, etc.).
    confidence : float
        Minimum confidence for a detection to count (0–1).
    show : bool
        Display the annotated video in a window.
    max_frames : int
        Process at most N frames (0 = all frames).
    frame_skip : int
        Process only every Nth frame for speed.

    Returns
    -------
    dict
        {
            "cars": int,
            "buses": int,
            "trucks": int,
            "motorcycles": int,
            "total_vehicles": int
        }

    Example
    -------
    >>> counts = detect_vehicles_from_video("data/sample_videos/traffic.mp4")
    >>> print(counts)
    {'cars': 12, 'buses': 3, 'trucks': 4, 'motorcycles': 7, 'total_vehicles': 26}
    """
    logger.info(f"🎬 Starting video detection: {video_path}")
    return _process_source(
        source=video_path,
        confidence=confidence,
        show=show,
        max_frames=max_frames,
        frame_skip=frame_skip,
        start_frame=start_frame,
    )


def stream_vehicle_detection(
    source,
    confidence: float = 0.4,
    max_frames: int = 0,
    frame_skip: int = 1,
):
    """
    Stream annotated frames as multipart JPEG for live dashboard previews.

    `source` can be a file path, RTSP/HTTP URL, or camera index.
    Yields bytes suitable for "multipart/x-mixed-replace; boundary=frame".
    """
    import cv2
    import time
    from ultralytics import YOLO  # lazy import

    logger.info(f"📡 Streaming vehicle detection: {source}")
    model = YOLO("yolov8n.pt")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error(f"Cannot open video source: {source}")
        return

    frame_idx = 0
    prev_time = time.time()
    fps = 0.0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if frame_idx % frame_skip != 0:
                continue

            results = model(frame, conf=confidence, verbose=False)[0]
            latest_counts = get_vehicle_counts(results)
            draw_vehicle_boxes(frame, results, confidence_threshold=confidence)

            curr_time = time.time()
            fps = 1.0 / max(curr_time - prev_time, 1e-6)
            prev_time = curr_time

            _draw_hud_overlay(frame, latest_counts, fps)

            ok, buffer = cv2.imencode(".jpg", frame)
            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )

            if max_frames > 0 and frame_idx >= max_frames:
                break
    finally:
        cap.release()

    return


def detect_vehicles_from_camera(
    camera_id: int = 0,
    confidence: float = 0.4,
    show: bool = True,
    max_frames: int = 0,
    frame_skip: int = 1,
    start_frame: int = 0,
) -> Dict[str, int]:
    """
    Detect vehicles from a live webcam or USB camera.

    Parameters
    ----------
    camera_id : int
        OpenCV camera index (0 = default webcam, 1, 2, … for others).
    confidence : float
        Minimum detection confidence.
    show : bool
        Display the live annotated feed.
    max_frames : int
        Stop after N frames (0 = run until user quits with 'q').
    frame_skip : int
        Process every Nth frame.

    Returns
    -------
    dict
        Vehicle counts (same structure as detect_vehicles_from_video).
    """
    logger.info(f"📷 Starting camera detection: camera_id={camera_id}")
    return _process_source(
        source=camera_id,
        confidence=confidence,
        show=show,
        max_frames=max_frames,
        frame_skip=frame_skip,
        start_frame=start_frame,
    )


def detect_vehicles_from_stream(
    stream_url: str,
    confidence: float = 0.4,
    show: bool = True,
    max_frames: int = 0,
    frame_skip: int = 2,
    start_frame: int = 0,
) -> Dict[str, int]:
    """
    Detect vehicles from an RTSP / HTTP traffic camera stream.

    Parameters
    ----------
    stream_url : str
        RTSP or HTTP URL (e.g. "rtsp://192.168.1.100:554/stream").
    confidence : float
        Minimum detection confidence.
    show : bool
        Display the live annotated stream.
    max_frames : int
        Stop after N frames (0 = run indefinitely until 'q').
    frame_skip : int
        Process every Nth frame (default=2 for network streams).

    Returns
    -------
    dict
        Vehicle counts.
    """
    logger.info(f"📡 Starting stream detection: {stream_url}")
    return _process_source(
        source=stream_url,
        confidence=confidence,
        show=show,
        max_frames=max_frames,
        frame_skip=frame_skip,
        start_frame=start_frame,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE MODE — run with: python vision/vehicle_detection.py
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import os
    import glob

    print("=" * 60)
    print("  🚦 Traffic AI — Vehicle Detection Module")
    print("=" * 60)

    # Look for a sample video in data/sample_videos/
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_videos")
    videos = glob.glob(os.path.join(sample_dir, "*.mp4")) + \
             glob.glob(os.path.join(sample_dir, "*.avi")) + \
             glob.glob(os.path.join(sample_dir, "*.mov"))

    if videos:
        video_path = videos[0]
        print(f"\n▶ Found sample video: {video_path}")
        counts = detect_vehicles_from_video(video_path, confidence=0.4, show=True)
    else:
        print(f"\n⚠ No video files found in {os.path.abspath(sample_dir)}")
        print("  Falling back to webcam (camera_id=0).")
        print("  Press 'q' in the video window to stop.\n")
        counts = detect_vehicles_from_camera(camera_id=0, confidence=0.4, show=True)

    # ── Print final summary ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  📊 FINAL VEHICLE COUNTS")
    print("=" * 60)
    print(f"  Cars:        {counts.get('cars', 0)}")
    print(f"  Buses:       {counts.get('buses', 0)}")
    print(f"  Trucks:      {counts.get('trucks', 0)}")
    print(f"  Motorcycles: {counts.get('motorcycles', 0)}")
    print(f"  ─────────────────")
    print(f"  Total:       {counts.get('total_vehicles', 0)}")
    print("=" * 60)
