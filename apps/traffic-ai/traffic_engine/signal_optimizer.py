"""
signal_optimizer.py
===================
Adaptive traffic signal control engine.

Takes density data from ``density_calculator`` and computes optimal
green-time distribution for each lane of an intersection.

Core logic
----------
  1. **Proportional allocation** — green time ∝ lane density.
  2. **Minimum guarantee** — every lane gets ≥ MIN_GREEN seconds.
  3. **SEVERE priority** — any lane at SEVERE congestion is guaranteed
     ≥ 50 % of the total cycle time.
  4. **Signal rotation plan** — ordered sequence the controller follows.
  5. **Real-time adaptation** — ``update_signal_plan()`` re-optimises
     whenever new density data arrives.

Usage
-----
    from traffic_engine.signal_optimizer import (
        optimize_signal_timings,
        generate_signal_sequence,
        update_signal_plan,
    )

    plan = optimize_signal_timings(density_data)
    sequence = generate_signal_sequence(plan)
    updated = update_signal_plan(plan, new_density_data)

Standalone test:
    python -m traffic_engine.signal_optimizer
    # or
    python traffic_engine/signal_optimizer.py
"""

from typing import Dict, List, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

TOTAL_CYCLE_TIME: int = 120         # seconds per full signal cycle
MIN_GREEN_TIME: int = 10            # absolute minimum green per lane
SEVERE_PRIORITY_SHARE: float = 0.50 # SEVERE lane gets ≥ 50 % of cycle
YELLOW_TIME: int = 3                # amber phase between greens

# Speed-weighted tuning (prototype)
FREE_FLOW_SPEED_KMPH: float = 45.0  # reference free-flow speed
MIN_SPEED_KMPH: float = 5.0         # clamp to avoid divide-by-zero
SPEED_WEIGHT: float = 0.6           # how much slow speed increases priority


def _compute_speed_weight(speed_kmph: Optional[float]) -> Dict[str, float | None]:
    """
    Convert speed into a weight factor.

    Slow lanes get higher weight (more green).
    """
    if speed_kmph is None:
        return {
            "speed_kmph": None,
            "speed_weight": 1.0,
            "slowdown_index": 0.0,
        }

    try:
        speed_val = float(speed_kmph)
    except (TypeError, ValueError):
        return {
            "speed_kmph": None,
            "speed_weight": 1.0,
            "slowdown_index": 0.0,
        }

    speed_val = max(speed_val, MIN_SPEED_KMPH)
    speed_norm = min(max(speed_val / FREE_FLOW_SPEED_KMPH, 0.0), 1.5)
    slowdown = max(0.0, 1.0 - speed_norm)
    speed_weight = 1.0 + SPEED_WEIGHT * slowdown

    return {
        "speed_kmph": round(speed_val, 1),
        "speed_weight": round(speed_weight, 3),
        "slowdown_index": round(slowdown, 3),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: optimize_signal_timings
# ═══════════════════════════════════════════════════════════════════════════════

def optimize_signal_timings(
    lane_density_data: Dict[str, Dict[str, Any]],
    cycle_time: int = TOTAL_CYCLE_TIME,
    min_green: int = MIN_GREEN_TIME,
) -> Dict[str, Any]:
    """
    Compute an optimal signal plan for one intersection.

    Parameters
    ----------
    lane_density_data : dict
        Per-lane density info from ``density_calculator``.
        Example::

            {
                "lane_A": {"density_percent": 85.0, "congestion_level": "HIGH", "speed_kmph": 18.5},
                "lane_B": {"density_percent": 45.0, "congestion_level": "MEDIUM"},
                "lane_C": {"density_percent": 20.0, "congestion_level": "LOW"},
                "lane_D": {"density_percent": 120.0, "congestion_level": "SEVERE"},
            }

    cycle_time : int
        Total cycle length in seconds (default 120).
    min_green : int
        Minimum green time any lane can receive (default 10).

    Returns
    -------
    dict
        {
            "cycle_time": int,
            "signals": {
                "lane_X": {
                    "green_time": int,
                    "density_percent": float,
                    "congestion_level": str,
                    "priority": bool        # True if SEVERE-boosted
                    "speed_kmph": float | None
                    "speed_weight": float   # 1.0+ when speed is slow
                    "effective_density": float  # density × speed_weight
                },
                ...
            },
            "has_severe_lanes": bool,
            "total_green_allocated": int,
        }
    """
    if not lane_density_data:
        return {
            "cycle_time": cycle_time,
            "signals": {},
            "has_severe_lanes": False,
            "total_green_allocated": 0,
        }

    num_lanes = len(lane_density_data)

    # ── Step 1: Identify SEVERE lanes ────────────────────────────────────────
    severe_lanes = [
        lid for lid, d in lane_density_data.items()
        if d.get("congestion_level", "").upper() == "SEVERE"
    ]
    has_severe = len(severe_lanes) > 0

    # ── Step 2: Compute raw density values ───────────────────────────────────
    densities: Dict[str, float] = {}
    speed_meta: Dict[str, Dict[str, Any]] = {}
    for lid, d in lane_density_data.items():
        raw_density = max(d.get("density_percent", 0.0), 0.01)  # avoid 0
        speed_info = _compute_speed_weight(
            d.get("speed_kmph") or d.get("avg_speed_kmph")
        )
        effective_density = raw_density * speed_info["speed_weight"]

        densities[lid] = max(effective_density, 0.01)
        speed_meta[lid] = {
            **speed_info,
            "effective_density": round(effective_density, 2),
        }

    total_density = sum(densities.values())

    # ── Step 3: Proportional green time allocation ───────────────────────────
    #
    #   green_time_lane = (density_lane / total_density) × cycle_time
    #
    # If a lane is SEVERE, we guarantee it ≥ SEVERE_PRIORITY_SHARE of the
    # cycle, then distribute the remainder proportionally among the rest.

    signals: Dict[str, Dict[str, Any]] = {}

    if has_severe:
        # --- SEVERE priority path ---
        #
        # Reserve SEVERE_PRIORITY_SHARE for the worst SEVERE lane.
        # If multiple SEVERE lanes exist, split the reserved share
        # among them proportionally by their densities.

        severe_reserved = int(cycle_time * SEVERE_PRIORITY_SHARE)
        remaining_time = cycle_time - severe_reserved

        # Densities of SEVERE lanes only
        severe_density_total = sum(densities[lid] for lid in severe_lanes)
        non_severe_lanes = [lid for lid in densities if lid not in severe_lanes]
        non_severe_density_total = sum(densities[lid] for lid in non_severe_lanes)

        # Allocate within the SEVERE pool
        for lid in severe_lanes:
            share = densities[lid] / severe_density_total if severe_density_total else 1.0
            green = max(min_green, int(share * severe_reserved))
            meta = speed_meta.get(lid, {})
            signals[lid] = {
                "green_time": green,
                "density_percent": lane_density_data[lid].get("density_percent", 0),
                "congestion_level": lane_density_data[lid].get("congestion_level", ""),
                "priority": True,
                "speed_kmph": meta.get("speed_kmph"),
                "speed_weight": meta.get("speed_weight", 1.0),
                "effective_density": meta.get("effective_density"),
                "slowdown_index": meta.get("slowdown_index", 0.0),
            }

        # Allocate within the remaining pool
        if non_severe_lanes:
            for lid in non_severe_lanes:
                share = densities[lid] / non_severe_density_total if non_severe_density_total else 1.0
                green = max(min_green, int(share * remaining_time))
                meta = speed_meta.get(lid, {})
                signals[lid] = {
                    "green_time": green,
                    "density_percent": lane_density_data[lid].get("density_percent", 0),
                    "congestion_level": lane_density_data[lid].get("congestion_level", ""),
                    "priority": False,
                    "speed_kmph": meta.get("speed_kmph"),
                    "speed_weight": meta.get("speed_weight", 1.0),
                    "effective_density": meta.get("effective_density"),
                    "slowdown_index": meta.get("slowdown_index", 0.0),
                }
    else:
        # --- Normal proportional path ---
        for lid in densities:
            proportion = densities[lid] / total_density
            green = max(min_green, int(proportion * cycle_time))
            meta = speed_meta.get(lid, {})
            signals[lid] = {
                "green_time": green,
                "density_percent": lane_density_data[lid].get("density_percent", 0),
                "congestion_level": lane_density_data[lid].get("congestion_level", ""),
                "priority": False,
                "speed_kmph": meta.get("speed_kmph"),
                "speed_weight": meta.get("speed_weight", 1.0),
                "effective_density": meta.get("effective_density"),
                "slowdown_index": meta.get("slowdown_index", 0.0),
            }

    # ── Step 4: Normalise so total green == cycle_time ───────────────────────
    allocated = sum(s["green_time"] for s in signals.values())
    if allocated != cycle_time and signals:
        diff = cycle_time - allocated
        # Add/subtract surplus from the lane with the most green time
        target_lane = max(signals, key=lambda k: signals[k]["green_time"])
        signals[target_lane]["green_time"] = max(
            min_green, signals[target_lane]["green_time"] + diff
        )

    total_allocated = sum(s["green_time"] for s in signals.values())

    # ── Log ──────────────────────────────────────────────────────────────────
    for lid, s in signals.items():
        prio = " ⚠️ PRIORITY" if s["priority"] else ""
        speed_note = ""
        if s.get("speed_kmph") is not None:
            speed_note = f", speed {s['speed_kmph']} km/h, w={s.get('speed_weight', 1.0):.2f}x"
        logger.info(
            f"Signal → {lid}: GREEN {s['green_time']}s "
            f"(density {s['density_percent']:.1f}%, {s['congestion_level']}{speed_note}){prio}"
        )

    return {
        "cycle_time": cycle_time,
        "signals": signals,
        "has_severe_lanes": has_severe,
        "total_green_allocated": total_allocated,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: generate_signal_sequence
# ═══════════════════════════════════════════════════════════════════════════════

def generate_signal_sequence(
    signal_plan: Dict[str, Any],
    yellow_time: int = YELLOW_TIME,
) -> List[Dict[str, Any]]:
    """
    Convert a signal plan into an ordered rotation sequence the controller
    follows within one cycle.

    Lanes are sorted **descending by green time** so the most congested lane
    goes first (reduces queue buildup).

    Parameters
    ----------
    signal_plan : dict
        Output of ``optimize_signal_timings()``.
    yellow_time : int
        Amber transition phase in seconds inserted between greens.

    Returns
    -------
    list[dict]
        Ordered sequence of phases::

            [
                {"phase": 1, "lane": "lane_D", "state": "GREEN",  "duration": 60},
                {"phase": 2, "lane": "ALL",    "state": "YELLOW", "duration": 3},
                {"phase": 3, "lane": "lane_A", "state": "GREEN",  "duration": 30},
                ...
            ]
    """
    signals = signal_plan.get("signals", {})
    if not signals:
        return []

    # Sort lanes descending by green_time (priority lanes first)
    sorted_lanes = sorted(
        signals.items(),
        key=lambda x: (-int(x[1].get("priority", False)), -x[1]["green_time"]),
    )

    sequence: List[Dict[str, Any]] = []
    phase = 1

    for i, (lane_id, lane_info) in enumerate(sorted_lanes):
        # GREEN phase
        sequence.append({
            "phase": phase,
            "lane": lane_id,
            "state": "GREEN",
            "duration": lane_info["green_time"],
        })
        phase += 1

        # YELLOW transition (skip after the last lane)
        if i < len(sorted_lanes) - 1:
            sequence.append({
                "phase": phase,
                "lane": "ALL",
                "state": "YELLOW",
                "duration": yellow_time,
            })
            phase += 1

    logger.info(f"Signal sequence generated — {len(sequence)} phases")
    return sequence


# ═══════════════════════════════════════════════════════════════════════════════
# CORE: update_signal_plan  (real-time adaptation)
# ═══════════════════════════════════════════════════════════════════════════════

def update_signal_plan(
    current_plan: Dict[str, Any],
    new_density_data: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Recompute signal timings when new density data arrives.

    This is the real-time adaptation hook: every time the
    ``density_calculator`` produces fresh data, call this function
    to get an updated plan.

    Parameters
    ----------
    current_plan : dict
        The existing signal plan (used to preserve ``cycle_time``).
    new_density_data : dict
        Fresh per-lane density data from ``density_calculator``.

    Returns
    -------
    dict
        A brand-new signal plan (same schema as ``optimize_signal_timings``).
    """
    cycle_time = current_plan.get("cycle_time", TOTAL_CYCLE_TIME)
    logger.info("🔄 Real-time re-optimisation triggered")

    new_plan = optimize_signal_timings(new_density_data, cycle_time=cycle_time)

    # ── Log changes ──────────────────────────────────────────────────────────
    old_signals = current_plan.get("signals", {})
    for lid, new_sig in new_plan.get("signals", {}).items():
        old_green = old_signals.get(lid, {}).get("green_time", "N/A")
        new_green = new_sig["green_time"]
        delta = ""
        if isinstance(old_green, int):
            d = new_green - old_green
            delta = f" (Δ {'+' if d >= 0 else ''}{d}s)"
        logger.info(f"  {lid}: {old_green}s → {new_green}s{delta}")

    return new_plan


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: pretty-print a plan to the console
# ═══════════════════════════════════════════════════════════════════════════════

def _print_plan(plan: Dict[str, Any], title: str = "Signal Plan") -> None:
    """Pretty-print a signal plan to stdout."""
    print(f"\n{'─' * 50}")
    print(f"  {title}  (cycle = {plan['cycle_time']}s)")
    print(f"{'─' * 50}")

    for lid, info in plan.get("signals", {}).items():
        level = info.get("congestion_level", "")
        icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "SEVERE": "🚨"}.get(level, "⚪")
        prio = " ⚠️  PRIORITY" if info.get("priority") else ""
        print(
            f"  {icon} {lid:<10} → GREEN {info['green_time']:>3}s   "
            f"({info['density_percent']:>6.1f}% {level}){prio}"
        )

    print(f"{'─' * 50}")
    print(f"  Total green allocated: {plan.get('total_green_allocated', '?')}s")


def _print_sequence(seq: List[Dict[str, Any]]) -> None:
    """Pretty-print a signal rotation sequence."""
    print(f"\n{'─' * 50}")
    print("  Signal Rotation Sequence")
    print(f"{'─' * 50}")
    for entry in seq:
        icon = "🟢" if entry["state"] == "GREEN" else "🟡"
        print(
            f"  Phase {entry['phase']:>2} │ {icon} {entry['lane']:<10} "
            f"{entry['state']:<7} {entry['duration']:>3}s"
        )
    print(f"{'─' * 50}")


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST MODE — python traffic_engine/signal_optimizer.py
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  🚦 Traffic Engine — Signal Optimizer (test mode)")
    print("=" * 60)

    # ── Scenario 1: Normal traffic ───────────────────────────────────────────
    normal_data = {
        "lane_A": {"density_percent": 75.0, "congestion_level": "HIGH"},
        "lane_B": {"density_percent": 45.0, "congestion_level": "MEDIUM"},
        "lane_C": {"density_percent": 20.0, "congestion_level": "LOW"},
        "lane_D": {"density_percent": 30.0, "congestion_level": "MEDIUM"},
    }

    print("\n\n🔹 SCENARIO 1 — Normal Traffic (no SEVERE)")
    plan1 = optimize_signal_timings(normal_data)
    _print_plan(plan1, "Normal Traffic Plan")

    seq1 = generate_signal_sequence(plan1)
    _print_sequence(seq1)

    # ── Scenario 2: SEVERE congestion on lane_A ─────────────────────────────
    severe_data = {
        "lane_A": {"density_percent": 130.0, "congestion_level": "SEVERE"},
        "lane_B": {"density_percent": 50.0,  "congestion_level": "MEDIUM"},
        "lane_C": {"density_percent": 25.0,  "congestion_level": "LOW"},
        "lane_D": {"density_percent": 10.0,  "congestion_level": "LOW"},
    }

    print("\n\n🔹 SCENARIO 2 — SEVERE Congestion (lane_A = 130%)")
    plan2 = optimize_signal_timings(severe_data)
    _print_plan(plan2, "SEVERE Priority Plan")

    seq2 = generate_signal_sequence(plan2)
    _print_sequence(seq2)

    # ── Scenario 3: Real-time update ─────────────────────────────────────────
    updated_data = {
        "lane_A": {"density_percent": 60.0,  "congestion_level": "MEDIUM"},
        "lane_B": {"density_percent": 80.0,  "congestion_level": "HIGH"},
        "lane_C": {"density_percent": 25.0,  "congestion_level": "LOW"},
        "lane_D": {"density_percent": 15.0,  "congestion_level": "LOW"},
    }

    print("\n\n🔹 SCENARIO 3 — Real-Time Adaptation (density shift)")
    plan3 = update_signal_plan(plan2, updated_data)
    _print_plan(plan3, "Updated Plan (after re-optimisation)")

    seq3 = generate_signal_sequence(plan3)
    _print_sequence(seq3)

    print("\n" + "=" * 60)
    print("  ✅ All scenarios completed successfully")
    print("=" * 60)
