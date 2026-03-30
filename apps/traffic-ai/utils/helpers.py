"""
helpers.py
----------
Shared utility functions used across the project.
"""

from typing import Dict


def compute_density(vehicle_count: int, lane_capacity: int) -> float:
    """
    Compute traffic density as a ratio of vehicles to lane capacity.
    Returns a float between 0.0 and 1.0.
    """
    if lane_capacity == 0:
        return 0.0
    return min(vehicle_count / lane_capacity, 1.0)


def density_label(density: float) -> str:
    """
    Convert a numeric density value to a human-readable category.
    """
    if density < 0.30:
        return "LOW"
    elif density < 0.70:
        return "MEDIUM"
    else:
        return "HIGH"


def format_signal_plan(signal_plan: Dict[str, int]) -> str:
    """
    Pretty-print a signal timing plan dictionary.
    Example input: {"Lane_A": 45, "Lane_B": 25}
    """
    lines = [f"  {lane} → GREEN {duration}s" for lane, duration in signal_plan.items()]
    return "\n".join(lines)
