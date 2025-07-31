import pandas as pd
import numpy as np
import os

# ✅ Load dataset
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  
DATA_PATH = os.path.join(ROOT_DIR, "datacost.xlsx")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

quotes_df = pd.read_excel(DATA_PATH)

# ✅ Helper columns for matching
quotes_df["FOB_Name"] = quotes_df["ORIGIN"].astype(str).str.strip()
quotes_df["Dest_Name"] = quotes_df["DESTINATION"].astype(str).str.strip()

def get_quote_from_dataset(fob, destination, distance_km):
    fob = fob.strip()
    destination = destination.strip()

    # ✅ 1. Exact Match → Calculate using Linehaul & Fuel% formula
    match = quotes_df[
        (quotes_df["FOB_Name"].str.lower() == fob.lower()) &
        (quotes_df["Dest_Name"].str.lower() == destination.lower())
    ]
    if not match.empty:
        row = match.iloc[0]
        linehaul = float(row["LINEHAUL"])
        fuel_percent = float(row["FUEL"])   # Treat as decimal (e.g., 0.25 for 25%)
        fuel_cost = linehaul * fuel_percent
        other_cost = float(row["OTHER"])
        tank_wash = float(row["TANK WASH"])

        total = round(linehaul + fuel_cost + other_cost, 2)  # ✅ Tank Wash excluded

        return {
            "linehaul": round(linehaul, 2),
            "fuel": round(fuel_cost, 2),
            "tank_wash": round(tank_wash, 2),
            "other": round(other_cost, 2),
            "total": total
        }

    # ✅ 2. Unknown Route → Use Average Cost Per Mile (still ignores Tank Wash)
    if "Origin Latitude" in quotes_df.columns and "Destination Latitude" in quotes_df.columns:
        route_distances = np.sqrt(
            (quotes_df["Destination Latitude"] - quotes_df["Origin Latitude"])**2 +
            (quotes_df["Destination Longitude"] - quotes_df["Origin Longitude"])**2
        ) * 111
    else:
        route_distances = np.full(len(quotes_df), distance_km)

    route_distances[route_distances < 1] = 1

    # ✅ Average CPM based on adjusted formula (excluding tank wash)
    adj_totals = []
    for _, r in quotes_df.iterrows():
        l = float(r["LINEHAUL"])
        f_pct = float(r["FUEL"])
        o = float(r["OTHER"])
        adj_totals.append(l + (l * f_pct) + o)
    avg_cost_per_mile = np.mean(adj_totals / route_distances)

    estimated_total = round(distance_km * avg_cost_per_mile, 2)

    return {
        "total": estimated_total
    }
