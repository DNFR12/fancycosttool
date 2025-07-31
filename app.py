from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import os
from services.cost_calculator import get_quote_from_dataset

app = Flask(__name__)

# ✅ Load FOBs dynamically
DATA_PATH = os.path.join(os.path.dirname(__file__), "datacosts.xlsx")
df = pd.read_excel(DATA_PATH)

FOBS = {}
for _, row in df.iterrows():
    fob_name = str(row["ORIGIN"]).strip()
    if fob_name not in FOBS:
        FOBS[fob_name] = {
            "lat": float(row["Origin Latitude"]),
            "lon": float(row["Origin Longitude"])
        }

OSRM_URL = "http://router.project-osrm.org/route/v1/driving/"

@app.route("/")
def index():
    # ✅ Pass list of known destinations to frontend
    destinations = sorted(df["DESTINATION"].astype(str).unique())
    return render_template("index.html", fobs=list(FOBS.keys()), destinations=destinations)

@app.route("/route", methods=["POST"])
def get_route():
    data = request.json
    fob_name = data.get("fob")
    dest_name = data.get("destination_name", "")
    dest_lat = data.get("dest_lat")
    dest_lon = data.get("dest_lon")

    if fob_name not in FOBS:
        return jsonify({"error": "FOB not found"}), 400

    origin = FOBS[fob_name]

    # ✅ If using known destination (lat=0), skip OSRM and set dummy distance
    if dest_lat == 0 and dest_lon == 0:
        distance_km = 0  # will not affect cost logic, cost comes directly from dataset
        geometry = {"type": "LineString", "coordinates": [[origin["lon"], origin["lat"]]]}
    else:
        # ✅ Use OSRM to calculate driving route
        coords = f"{origin['lon']},{origin['lat']};{dest_lon},{dest_lat}"
        url = f"{OSRM_URL}{coords}?overview=full&geometries=geojson"
        r = requests.get(url)
        if r.status_code != 200:
            return jsonify({"error": "OSRM request failed"}), 500
        route = r.json()["routes"][0]
        distance_km = route["distance"] / 1000
        geometry = route["geometry"]

    # ✅ Get costs (exact breakdown or estimate)
    costs = get_quote_from_dataset(fob_name, dest_name, distance_km)

    return jsonify({
        "distance_km": distance_km,
        "geometry": geometry,
        "costs": costs
    })

if __name__ == "__main__":
    app.run(debug=True)
