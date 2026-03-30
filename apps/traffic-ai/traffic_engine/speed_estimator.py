"""
speed_estimator.py
==================
Lightweight speed estimation utilities for the Traffic AI prototype.

We don't do full multi-object tracking here (too heavy for a hackathon demo).
Instead, we estimate average lane speed from density using a simple
Greenshields-style curve:

    v = v_free * (1 - k / k_jam)

Where:
  v_free = free-flow speed (km/h)
  k      = density_percent (0–100+)
  k_jam  = "jam density" proxy (default 140%)

This yields a plausible speed signal that can be used to:
  • display "Avg Speed" on the dashboard
  • weight signal timing decisions (slow lanes get more green)

For simulation we add a bit of noise to feel more "live".
For real video overrides we keep noise at 0 for stability.
"""

from __future__ import annotations

import random
from typing import Optional


def estimate_speed_kmph(
    density_percent: float,
    *,
    free_flow_speed: float = 45.0,
    jam_density_percent: float = 140.0,
    min_speed: float = 5.0,
    noise_kmph: float = 2.0,
) -> float:
    """
    Estimate average lane speed (km/h) from density.

    Parameters
    ----------
    density_percent : float
        Lane density (0–100+).
    free_flow_speed : float
        Speed at near-zero density.
    jam_density_percent : float
        Density at which speed approaches 0.
    min_speed : float
        Lower clamp for stability.
    noise_kmph : float
        Random +/- noise added (use 0 for stable/real detections).
    """
    if density_percent is None:
        density_percent = 0.0

    ratio = max(0.0, min(density_percent / jam_density_percent, 1.0))
    base_speed = free_flow_speed * (1.0 - ratio)

    if noise_kmph:
        base_speed += random.uniform(-noise_kmph, noise_kmph)

    speed = max(min_speed, min(free_flow_speed, base_speed))
    return round(speed, 1)


def classify_speed(
    speed_kmph: Optional[float],
    *,
    slow_threshold: float = 15.0,
    moderate_threshold: float = 30.0,
) -> str:
    """
    Convert speed into a qualitative label.
    """
    if speed_kmph is None:
        return "UNKNOWN"
    if speed_kmph <= slow_threshold:
        return "SLOW"
    if speed_kmph <= moderate_threshold:
        return "MODERATE"
    return "FAST"

