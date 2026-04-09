"""
Verification script: Confirms that different inputs produce different demo outputs.
Tests the pure helper functions without importing Streamlit.
"""
import sys, hashlib, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=" * 70)
print("VERIFICATION: Input-responsive demo data")
print("=" * 70)

# -- Replicate the helper functions from streamlit_app.py (pure Python, no Streamlit) --
def _bbox_seed(bbox, extra=""):
    raw = f"{bbox}{extra}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)

def _estimate_area_hectares(bbox):
    west, south, east, north = bbox
    mid_lat = math.radians((south + north) / 2)
    width_km = abs(east - west) * 111.32 * math.cos(mid_lat)
    height_km = abs(north - south) * 110.574
    return round(width_km * height_km * 100, 2)

import numpy as np

def _get_demo_ndvi_data(params):
    bbox = params["bbox"]
    seed = _bbox_seed(bbox, f"{params.get('start_date','')}{params.get('end_date','')}")
    rng = np.random.RandomState(seed)
    mid_lat = abs((bbox[1] + bbox[3]) / 2)
    base_ndvi = max(0.2, min(0.85, 0.80 - mid_lat * 0.008))
    mean_ndvi = base_ndvi + rng.uniform(-0.08, 0.08)
    return {
        "stats": {
            "mean": round(mean_ndvi, 4),
            "min": round(mean_ndvi - rng.uniform(0.30, 0.50), 4),
            "max": round(min(mean_ndvi + rng.uniform(0.10, 0.22), 0.95), 4),
            "std_dev": round(rng.uniform(0.10, 0.20), 4),
        }
    }

def _get_demo_density_data(params):
    bbox = params["bbox"]
    seed = _bbox_seed(bbox, f"{params.get('start_date','')}{params.get('end_date','')}")
    rng = np.random.RandomState(seed)
    total_ha = _estimate_area_hectares(bbox)
    if total_ha < 100: total_ha = 11000.0
    mid_lat = abs((bbox[1] + bbox[3]) / 2)
    dense_pct = max(10, min(65, 60 - mid_lat * 0.6 + rng.uniform(-5, 5)))
    moderate_pct = max(8, min(30, 22 + rng.uniform(-5, 5)))
    sparse_pct = max(5, min(20, 10 + mid_lat * 0.15 + rng.uniform(-3, 3)))
    grassland_pct = max(2, min(15, 5 + mid_lat * 0.1 + rng.uniform(-2, 2)))
    non_veg_pct = max(1, 100 - dense_pct - moderate_pct - sparse_pct - grassland_pct)
    pcts = [dense_pct, moderate_pct, sparse_pct, grassland_pct, non_veg_pct]
    pct_sum = sum(pcts)
    pcts = [round(p / pct_sum * 100, 1) for p in pcts]
    return {"dense_pct": pcts[0], "total_ha": round(total_ha, 2), "all_pcts": pcts}

def _get_demo_change_data(params):
    bbox = params["bbox"]
    seed = _bbox_seed(bbox, f"{params.get('period1_start','')}{params.get('period2_end','')}")
    rng = np.random.RandomState(seed)
    total_ha = _estimate_area_hectares(bbox)
    if total_ha < 100: total_ha = 11000.0
    threshold = params.get("change_threshold", 0.2)
    mid_lat = abs((bbox[1] + bbox[3]) / 2)
    mid_lon = abs((bbox[0] + bbox[2]) / 2)
    loss_pct = max(1, min(25, 8 + mid_lat * 0.12 + mid_lon * 0.02 - threshold * 15 + rng.uniform(-4, 4)))
    gain_pct = max(0.5, min(15, 3 + mid_lon * 0.01 + rng.uniform(-1.5, 2.5)))
    return {"loss_pct": round(loss_pct, 1), "gain_pct": round(gain_pct, 1), "total_ha": round(total_ha, 2)}

# -----------------------------------------------------------------------
# Test data
# -----------------------------------------------------------------------
regions = {
    "Amazon": {"bbox": [-60.0, -3.0, -59.0, -2.0], "start_date": "2024-01-01", "end_date": "2024-06-30"},
    "Congo":  {"bbox": [20.0, -2.0, 21.0, -1.0],   "start_date": "2024-01-01", "end_date": "2024-06-30"},
    "Borneo": {"bbox": [109.5, 0.5, 110.5, 1.5],    "start_date": "2024-01-01", "end_date": "2024-06-30"},
    "W.Ghats":{"bbox": [75.5, 11.0, 76.5, 12.0],    "start_date": "2024-01-01", "end_date": "2024-06-30"},
}
date_variants = {
    "Amazon_2024H1": {"bbox": [-60.0, -3.0, -59.0, -2.0], "start_date": "2024-01-01", "end_date": "2024-06-30"},
    "Amazon_2023H2": {"bbox": [-60.0, -3.0, -59.0, -2.0], "start_date": "2023-07-01", "end_date": "2023-12-31"},
}

# --- NDVI ---
print("\n--- NDVI Analysis (different regions, same dates) ---")
ndvi_means = {}
for name, params in regions.items():
    data = _get_demo_ndvi_data(params)
    mean = data["stats"]["mean"]
    ndvi_means[name] = mean
    print(f"  {name:10s}  mean={mean:.4f}  min={data['stats']['min']:.4f}  max={data['stats']['max']:.4f}  std={data['stats']['std_dev']:.4f}")
all_different = len(set(ndvi_means.values())) == len(ndvi_means)
print(f"  -> All regions produce DIFFERENT means: {'PASS' if all_different else 'FAIL'}")

print("\n--- NDVI Analysis (same region, different dates) ---")
ndvi_date_means = {}
for name, params in date_variants.items():
    data = _get_demo_ndvi_data(params)
    mean = data["stats"]["mean"]
    ndvi_date_means[name] = mean
    print(f"  {name:20s}  mean={mean:.4f}")
dates_different = len(set(ndvi_date_means.values())) == len(ndvi_date_means)
print(f"  -> Different dates produce DIFFERENT means: {'PASS' if dates_different else 'FAIL'}")

# --- Density ---
print("\n--- Forest Density (different regions) ---")
density_results = {}
for name, params in regions.items():
    data = _get_demo_density_data(params)
    density_results[name] = data["dense_pct"]
    print(f"  {name:10s}  dense={data['dense_pct']:.1f}%  total_area={data['total_ha']:.0f} ha")
density_all_diff = len(set(density_results.values())) == len(density_results)
print(f"  -> All regions produce DIFFERENT dense %: {'PASS' if density_all_diff else 'FAIL'}")

# --- Change Detection ---
print("\n--- Change Detection (different regions) ---")
change_base = {"period1_start": "2023-01-01", "period1_end": "2023-06-30",
               "period2_start": "2024-01-01", "period2_end": "2024-06-30", "change_threshold": 0.2}
change_results = {}
for name, reg in regions.items():
    params = {**reg, **change_base}
    data = _get_demo_change_data(params)
    change_results[name] = data["loss_pct"]
    print(f"  {name:10s}  loss={data['loss_pct']:.1f}%  gain={data['gain_pct']:.1f}%  area={data['total_ha']:.0f} ha")
change_all_diff = len(set(change_results.values())) == len(change_results)
print(f"  -> All regions produce DIFFERENT loss %: {'PASS' if change_all_diff else 'FAIL'}")

# --- Determinism ---
print("\n--- Determinism Check (same input twice) ---")
d1 = _get_demo_ndvi_data(regions["Amazon"])
d2 = _get_demo_ndvi_data(regions["Amazon"])
deterministic = d1["stats"] == d2["stats"]
print(f"  Run 1: mean={d1['stats']['mean']:.4f}")
print(f"  Run 2: mean={d2['stats']['mean']:.4f}")
print(f"  -> Same input = identical output: {'PASS' if deterministic else 'FAIL'}")

# --- Backend seed function ---
print("\n--- Backend _bbox_seed consistency ---")
from backend.gee.imagery import _bbox_seed as backend_seed, _estimate_area_hectares as backend_area
fs = _bbox_seed([-60.0, -3.0, -59.0, -2.0], "2024-01-012024-06-30")
bs = backend_seed([-60.0, -3.0, -59.0, -2.0], "2024-01-012024-06-30")
print(f"  Frontend seed: {fs}")
print(f"  Backend  seed: {bs}")
print(f"  -> Seeds match: {'PASS' if fs == bs else 'FAIL'}")
a1 = _estimate_area_hectares([-60.0, -3.0, -59.0, -2.0])
a2 = backend_area([-60.0, -3.0, -59.0, -2.0])
print(f"  Frontend area: {a1} ha")
print(f"  Backend  area: {a2} ha")
print(f"  -> Areas match: {'PASS' if a1 == a2 else 'FAIL'}")

# --- Summary ---
print("\n" + "=" * 70)
tests = [all_different, dates_different, density_all_diff, change_all_diff, deterministic, fs == bs, a1 == a2]
passed = sum(tests)
total = len(tests)
print(f"RESULT: {passed}/{total} tests passed — {'ALL PASSED' if all(tests) else 'SOME FAILED'}")
print("=" * 70)
