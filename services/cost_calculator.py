import pandas as pd
import numpy as np
import os

# ✅ Load dataset
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  # go up from /services
DATA_PATH = os.path.join(ROOT_DIR, "datacost.xlsx")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

quotes_df = pd.read_excel(DATA_PATH)

# ✅ Create helper columns
quotes_df["FOB_Name"] = quotes_df["ORIGIN"].astype(str).str.strip()
quotes_df["Dest_Name"] = quotes_df["DESTINATION"].astype(str).str.strip()

def get_quote_from_dataset(fob, destination, distance_km):
    fob = fob.strip()
    destination = destination.strip()

    # ✅ 1. Exact Match → return full breakdown
    match = quotes_df[
        (quotes_df["FOB_Name"].str.lower() == fob.lower()) &
        (quotes_df["Dest_Name"].str.lower() == destination.lower())
    ]
    if not match.empty:
        row = match.iloc[0]
        costs = {
            "linehaul": float(row["LINEHAUL"]),
            "fuel": float(row["FUEL"]),
            "tank_wash": float(row["TANK WASH"]),
            "other": float(row["OTHER"]),
            "total": round(float(row["LINEHAUL"]) + float(row["FUEL"]) + float(row["TANK WASH"]) + float(row["OTHER"]), 2)
        }
        return costs

    # ✅ 2. Unknown Route → calculate average cost per mile
    if "Origin Latitude" in quotes_df.columns and "Destination Latitude" in quotes_df.columns:
        route_distances = np.sqrt(
            (quotes_df["Destination Latitude"] - quotes_df["Origin Latitude"])**2 +
            (quotes_df["Destination Longitude"] - quotes_df["Origin Longitude"])**2
        ) * 111
    else:
        route_distances = np.full(len(quotes_df), distance_km)  # fallback

    route_distances[route_distances < 1] = 1  # avoid divide by zero
    avg_cost_per_mile = (quotes_df["TOTAL"] / route_distances).mean()

    estimated_total = round(distance_km * avg_cost_per_mile, 2)

    # ✅ Return only estimated total
    return {
        "total": estimated_total
    }
