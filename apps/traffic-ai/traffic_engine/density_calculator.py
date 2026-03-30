"""
density_calculator.py
=====================
Converts raw vehicle detection counts into traffic density metrics
used by the Signal Optimization Engine.

Key concepts
------------
  • **Weighted vehicle load** — different vehicle types consume different
    amounts of road capacity (a bus ≈ 2.5 cars, a motorcycle ≈ 0.5 cars).
  • **Density percent** — weighted load / lane capacity × 100.
  • **Congestion level** — LOW / MEDIUM / HIGH / SEVERE based on density.
  • **Multi-lane / intersection** — aggregate densities across all lanes.

Usage
-----
    from traffic_engine.density_calculator import (
        calculate_density,
        calculate_intersection_density,
    )

    counts = {"cars": 10, "buses": 2, "trucks": 3, "motorcycles": 5, "total_vehicles": 20}
    result = calculate_density(counts, lane_capacity=30)

Run standalone:
    python -m traffic_engine.density_calculator
    # or
    python traffic_engine/density_calculator.py
"""

from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Weighted impact factors — how much road capacity each type consumes
# relative to a standard passenger car (PCU — Passenger Car Unit).
VEHICLE_WEIGHT_FACTORS: Dict[str, float] = {
    "cars":        1.0,    # baseline
    "motorcycles": 0.5,    # smaller footprint, lane-splitting
    "buses":       2.5,    # large, slow acceleration, frequent stops
    "trucks":      2.0,    # large, heavy, slower speed
}

# Default lane capacity in PCU (Passenger Car Units)
DEFAULT_LANE_CAPACITY: int = 20

# Congestion thresholds (density percent → label)
CONGESTION_THRESHOLDS = [
    (30,  "LOW"),       # 0–30 %
    (70,  "MEDIUM"),    # 30–70 %
    (100, "HIGH"),      # 70–100 %
]
# Anything above 100 % → SEVERE


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _classify_congestion(density_percent: float) -> str:
    """
    Map a density percentage to a congestion level string.

        0–30 %   → LOW
        30–70 %  → MEDIUM
        70–100 % → HIGH
        >100 %   → SEVERE
    """
    for threshold, label in CONGESTION_THRESHOLDS:
        if density_percent <= threshold:
            return label
    return "SEVERE"


def _compute_weighted_load(vehicle_counts: Dict[str, int]) -> float:
    """
    Compute a weighted vehicle load using PCU factors.

    Formula:
        weighted_load = Σ (count_i × weight_i)

    Example:
        10 cars × 1.0  = 10.0
         5 motos × 0.5 =  2.5
         2 buses × 2.5 =  5.0
         3 trucks × 2.0 = 6.0
                         ─────
                          23.5 PCU
    """
    load = 0.0
    for vehicle_type, weight in VEHICLE_WEIGHT_FACTORS.items():
        count = vehicle_counts.get(vehicle_type, 0)
        load += count * weight
    return round(load, 2)


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: calculate_density  (single lane)
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_density(
    vehicle_counts: Dict[str, int],
    lane_capacity: int = DEFAULT_LANE_CAPACITY,
) -> Dict[str, Any]:
    """
    Compute traffic density for a **single lane**.

    Parameters
    ----------
    vehicle_counts : dict
        Detection output:
        {"cars": int, "buses": int, "trucks": int, "motorcycles": int, "total_vehicles": int}
    lane_capacity : int
        Maximum PCU the lane can handle before full congestion (100 %).

    Returns
    -------
    dict
        {
            "total_vehicles":   int,   # raw vehicle count
            "weighted_load":    float, # PCU-weighted total
            "lane_capacity":    int,
            "density_percent":  float, # 0–100+ (can exceed 100)
            "congestion_level": str,   # LOW | MEDIUM | HIGH | SEVERE
            "vehicle_breakdown": {     # individual weighted contributions
                "cars":        {"count": int, "weight": float, "load": float},
                "buses":       ...,
                "trucks":      ...,
                "motorcycles": ...
            }
        }
    """
    # Guard against zero capacity
    if lane_capacity <= 0:
        logger.warning("lane_capacity is 0 — defaulting to 1 to avoid division by zero.")
        lane_capacity = 1

    total_vehicles = vehicle_counts.get("total_vehicles", 0)

    # ── Weighted load ────────────────────────────────────────────────────────
    weighted_load = _compute_weighted_load(vehicle_counts)

    # ── Density % ────────────────────────────────────────────────────────────
    # density_percent = (weighted_load / lane_capacity) × 100
    density_percent = round((weighted_load / lane_capacity) * 100, 2)

    # ── Congestion classification ────────────────────────────────────────────
    congestion_level = _classify_congestion(density_percent)

    # ── Per-type breakdown ───────────────────────────────────────────────────
    breakdown = {}
    for vtype, weight in VEHICLE_WEIGHT_FACTORS.items():
        count = vehicle_counts.get(vtype, 0)
        breakdown[vtype] = {
            "count": count,
            "weight": weight,
            "load": round(count * weight, 2),
        }

    result = {
        "total_vehicles":    total_vehicles,
        "weighted_load":     weighted_load,
        "lane_capacity":     lane_capacity,
        "density_percent":   density_percent,
        "congestion_level":  congestion_level,
        "vehicle_breakdown": breakdown,
    }

    logger.info(
        f"Density → {density_percent:.1f}% ({congestion_level}) "
        f"| weighted_load={weighted_load} PCU / capacity={lane_capacity}"
    )

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: calculate_intersection_density  (multi-lane)
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_intersection_density(
    lane_data: Dict[str, Dict[str, int]],
    lane_capacity: int = DEFAULT_LANE_CAPACITY,
) -> Dict[str, Any]:
    """
    Compute traffic density across all lanes of an intersection.

    Parameters
    ----------
    lane_data : dict
        Mapping of lane_id → vehicle_counts dict.
        Example:
        {
            "lane_A": {"cars": 10, "buses": 2, "trucks": 1, "motorcycles": 3, "total_vehicles": 16},
            "lane_B": {"cars": 5,  "buses": 0, "trucks": 0, "motorcycles": 8, "total_vehicles": 13},
            "lane_C": {"cars": 3,  "buses": 1, "trucks": 2, "motorcycles": 0, "total_vehicles": 6},
        }
    lane_capacity : int
        Maximum PCU per lane (same for all lanes; override per-lane if needed later).

    Returns
    -------
    dict
        {
            "intersection_density": float,   # average density across all lanes
            "congestion_level":     str,      # based on average density
            "total_weighted_load":  float,    # sum of all lane loads
            "total_capacity":       int,      # lane_capacity × number_of_lanes
            "num_lanes":            int,
            "lanes": {
                "lane_A": { ...single-lane result from calculate_density... },
                "lane_B": { ... },
                ...
            },
            "most_congested_lane":  str,      # lane_id with highest density
            "least_congested_lane": str,      # lane_id with lowest density
        }
    """
    if not lane_data:
        return {
            "intersection_density": 0.0,
            "congestion_level": "LOW",
            "total_weighted_load": 0.0,
            "total_capacity": 0,
            "num_lanes": 0,
            "lanes": {},
            "most_congested_lane": None,
            "least_congested_lane": None,
        }

    # ── Calculate each lane ──────────────────────────────────────────────────
    lane_results: Dict[str, Dict] = {}
    for lane_id, counts in lane_data.items():
        lane_results[lane_id] = calculate_density(counts, lane_capacity)

    num_lanes = len(lane_results)
    total_capacity = lane_capacity * num_lanes

    # ── Aggregates ───────────────────────────────────────────────────────────
    total_weighted_load = round(
        sum(lr["weighted_load"] for lr in lane_results.values()), 2
    )
    avg_density = round(
        sum(lr["density_percent"] for lr in lane_results.values()) / num_lanes, 2
    )
    intersection_congestion = _classify_congestion(avg_density)

    # ── Best / worst lanes ───────────────────────────────────────────────────
    most_congested = max(lane_results, key=lambda k: lane_results[k]["density_percent"])
    least_congested = min(lane_results, key=lambda k: lane_results[k]["density_percent"])

    result = {
        "intersection_density":  avg_density,
        "congestion_level":      intersection_congestion,
        "total_weighted_load":   total_weighted_load,
        "total_capacity":        total_capacity,
        "num_lanes":             num_lanes,
        "lanes":                 lane_results,
        "most_congested_lane":   most_congested,
        "least_congested_lane":  least_congested,
    }

    logger.info(
        f"Intersection → avg density {avg_density:.1f}% ({intersection_congestion}) "
        f"| worst={most_congested} best={least_congested} | {num_lanes} lanes"
    )

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST MODE — python traffic_engine/density_calculator.py
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    print("=" * 64)
    print("  🚦 Traffic Engine — Density Calculator (test mode)")
    print("=" * 64)

    # ── Mock data ────────────────────────────────────────────────────────────
    mock_lanes = {
        "lane_A": {
            "cars": 12, "buses": 2, "trucks": 3, "motorcycles": 5,
            "total_vehicles": 22,
        },
        "lane_B": {
            "cars": 4, "buses": 0, "trucks": 1, "motorcycles": 8,
            "total_vehicles": 13,
        },
        "lane_C": {
            "cars": 2, "buses": 1, "trucks": 0, "motorcycles": 1,
            "total_vehicles": 4,
        },
    }

    # ── Single-lane test ─────────────────────────────────────────────────────
    print("\n─── Single Lane Test (lane_A) ───")
    single = calculate_density(mock_lanes["lane_A"], lane_capacity=20)
    print(json.dumps(single, indent=2))

    # ── Multi-lane intersection test ─────────────────────────────────────────
    print("\n─── Intersection Test (3 lanes) ───")
    intersection = calculate_intersection_density(mock_lanes, lane_capacity=20)

    # Pretty-print without the nested lane details for readability
    summary = {k: v for k, v in intersection.items() if k != "lanes"}
    print(json.dumps(summary, indent=2))

    print("\nPer-lane breakdown:")
    for lane_id, lane_result in intersection["lanes"].items():
        level = lane_result["congestion_level"]
        icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "SEVERE": "🚨"}.get(level, "⚪")
        print(
            f"  {icon} {lane_id}: "
            f"{lane_result['density_percent']:>6.1f}% ({level})  "
            f"weighted_load={lane_result['weighted_load']} PCU"
        )

    print("\n" + "=" * 64)
    print(f"  🏆 Most Congested  → {intersection['most_congested_lane']}")
    print(f"  😌 Least Congested → {intersection['least_congested_lane']}")
    print("=" * 64)
