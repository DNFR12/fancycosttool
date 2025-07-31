import pandas as pd
import numpy as np
import os

# ✅ Load dataset
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  
DATA_PATH = os.path.join(ROOT_DIR, "datacost.xlsx")

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

quotes_df = pd.read_excel(DATA_PATH)

# ✅ Helper columns
quotes_df["FOB_Name"] = quotes_df["ORIGIN"].astype(str).str.strip()
quotes_df["Dest_Name"] = quotes_df["DESTINATION"].astype(str).str.strip()

def get_quote_from_dataset(fob, destination, distance_km):
    fob = fob.strip()
    destination = destination.strip()

    # ✅ 1. Exact Match → Average all quotes for this pair
    matches = quotes_df[
        (quotes_df["FOB_Name"].str.lower() == fob.lower()) &
        (quotes_df["Dest_Name"].str.lower() == destination.lower())
    ]

    if not matches.empty:
        count_quotes = len(matches)

        linehauls = matches["LINEHAUL"].astype(float)
        fuel_percents = matches["FUEL"].astype(float)
        other_costs = matches["OTHER"].astype(float)
        tank_washes = matches["TANK WASH"].astype(float)

        fuel_costs = linehauls * fuel_percents
        totals = linehauls + fuel_costs + other_costs  # ✅ exclude tank wash

        avg_linehaul = round(linehauls.mean(), 2)
        avg_fuel = round(fuel_costs.mean(), 2)
        avg_other = round(other_costs.mean(), 2)
        avg_tank_wash = round(tank_washes.mean(), 2)
        avg_total = round(totals.mean(), 2)

        return {
            "linehaul": avg_linehaul,
            "fuel": avg_fuel,
            "tank_wash": avg_tank_wash,
            "other": avg_other,
            "total": avg_total,
            "note": f"Average of {count_quotes} quotes"
        }

    # ✅ 2. Unknown Route → Average CPM across all quotes
    if "Origin Latitude" in quotes_df.columns and "Destination Latitude" in quotes_df.columns:
        route_distances = np.sqrt(
            (quotes_df["Destination Latitude"] - quotes_df["Origin Latitude"])**2 +
            (quotes_df["Destination Longitude"] - quotes_df["Origin Longitude"])**2
        ) * 111
    else:
        route_distances = np.full(len(quotes_df), distance_km)

    route_distances[route_distances < 1] = 1

    adj_totals = []
    for _, r in quotes_df.iterrows():
        l = float(r["LINEHAUL"])
        f_pct = float(r["FUEL"])
        o = float(r["OTHER"])
        adj_totals.append(l + (l * f_pct) + o)

    avg_cost_per_mile = np.mean(np.array(adj_totals) / route_distances)
    estimated_total = round(distance_km * avg_cost_per_mile, 2)

    return {
        "total": estimated_total
    }
