"""
app.py — Smart City Traffic Dashboard
--------------------------------------
Streamlit dashboard for city administrators.

Panels:
  1. 🚦 Signal Control — live lane statuses
  2. 📊 Traffic Density — per-lane density bars
  3. 🚑 Emergency Mode — trigger green corridors
  4. 🗺️  City State Viewer — full intersection view

Run with:
    streamlit run dashboard/app.py
"""

import streamlit as st
import httpx
import time

# ─── Config ──────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Traffic AI Optimizer",
    page_icon="🚦",
    layout="wide",
)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def api_post(endpoint: str, payload: dict) -> dict:
    try:
        r = httpx.post(f"{API_BASE}{endpoint}", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def api_get(endpoint: str) -> dict:
    try:
        r = httpx.get(f"{API_BASE}{endpoint}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def density_color(label: str) -> str:
    return {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(label, "⚪")

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("🚦 Smart City Traffic AI Dashboard")
st.caption("Real-time signal optimization · Emergency corridor control")

# Health check
health = api_get("/health")
if "error" in health:
    st.error(f"⚠️ Backend not reachable: {health['error']}. Start the server first.")
else:
    st.success("✅ Backend connected")

st.divider()

# ─── Layout ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

# ── Panel 1: Traffic Update ──────────────────────────────────────────────────
with col1:
    st.subheader("📊 Traffic Density Input")
    st.caption("Simulate vehicle counts per lane")

    lane_a = st.slider("Lane A — vehicle count", 0, 20, 12)
    lane_b = st.slider("Lane B — vehicle count", 0, 20, 7)
    lane_c = st.slider("Lane C — vehicle count", 0, 20, 4)

    if st.button("🔄 Optimize Signals", use_container_width=True):
        payload = {"lane_vehicle_counts": {"Lane_A": lane_a, "Lane_B": lane_b, "Lane_C": lane_c}}
        result = api_post("/traffic/update", payload)

        if "error" in result:
            st.error(result["error"])
        else:
            st.success("Signal plan updated!")
            st.subheader("🚦 Signal Plan")
            for lane, seconds in result.get("signal_plan", {}).items():
                density_info = result["density"].get(lane, {})
                label = density_info.get("label", "-")
                icon = density_color(label)
                st.metric(label=f"{icon} {lane}", value=f"GREEN {seconds}s", delta=f"{label}")

# ── Panel 2: Emergency Mode ──────────────────────────────────────────────────
with col2:
    st.subheader("🚑 Emergency Green Corridor")
    st.caption("Trigger a green corridor for an emergency vehicle")

    available_nodes = ["INT_1", "INT_2", "INT_3", "INT_4", "INT_5"]
    source = st.selectbox("🚑 Ambulance Location (source)", available_nodes)
    target = st.selectbox("🏥 Destination (target)", ["HOSPITAL", "INT_4", "INT_3"])

    if st.button("🚨 ACTIVATE EMERGENCY CORRIDOR", use_container_width=True, type="primary"):
        payload = {"source_intersection": source, "target_intersection": target}
        result = api_post("/emergency/trigger", payload)

        if "error" in result:
            st.error(result["error"])
        else:
            st.success(result.get("message", "Corridor activated!"))
            st.subheader("🗺️ Route")
            route = result.get("emergency_route", [])
            st.info(" → ".join(route))

            st.subheader("🚦 Corridor Signal States")
            for intersection, signal in result.get("corridor", {}).items():
                color = "🟢" if signal == "GREEN" else "🔴"
                st.write(f"{color} **{intersection}** → {signal}")

st.divider()

# ── City State Snapshot ──────────────────────────────────────────────────────
st.subheader("🌆 Live City State")
if st.button("🔃 Refresh City State"):
    state = api_get("/city/state")
    if "error" in state:
        st.error(state["error"])
    else:
        city = state.get("city_state", {})
        if not city:
            st.info("No data yet. Run a traffic update above.")
        else:
            for node, data in city.items():
                st.write(f"**{node}**: {data}")
