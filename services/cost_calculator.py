import pandas as pd
import numpy as np
import os

# ✅ Load dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), "../datacost.xlsx")
quotes_df = pd.read_excel(DATA_PATH)

# ✅ Use ORIGIN and DESTINATION directly for matching
quotes_df["FOB_Name"] = quotes_df["ORIGIN"].astype(str).str.strip()
quotes_df["Dest_Name"] = quotes_df["DESTINATION"].astype(str).str.strip()

def get_quote_from_dataset(fob, destination, distance_km):
    fob = fob.strip()
    destination = destination.strip()

    # 1️⃣ Exact match
    match = quotes_df[
        (quotes_df["FOB_Name"].str.lower() == fob.lower()) &
        (quotes_df["Dest_Name"].str.lower() == destination.lower())
    ]
    if not match.empty:
        return extract_costs(match.iloc[0])

    # 2️⃣ No exact match → find closest by coordinate distance
    if "Origin Latitude" in quotes_df.columns and "Destination Latitude" in quotes_df.columns:
        quotes_df["dist_diff"] = np.abs(
            np.sqrt(
                (quotes_df["Destination Latitude"] - quotes_df["Origin Latitude"])**2 +
                (quotes_df["Destination Longitude"] - quotes_df["Origin Longitude"])**2
            ) * 111 - distance_km
        )
    else:
        # If coordinates missing, fall back to comparing total cost heuristics
        quotes_df["dist_diff"] = np.abs(distance_km - (quotes_df["TOTAL"] / 2))

    closest = quotes_df.sort_values("dist_diff").iloc[0]
    return extract_costs(closest)

def extract_costs(row):
    return {
        "linehaul": float(row["LINEHAUL"]),
        "fuel": float(row["FUEL"]),
        "tank_wash": float(row["TANK WASH"]),
        "other": float(row["OTHER"]),
        "demurrage": float(row["Demurrage"]),
        "total": float(row["TOTAL"])
    }
