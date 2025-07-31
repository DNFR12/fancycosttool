from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import os
from services.cost_calculator import get_quote_from_dataset

app = Flask(__name__)

# ✅ Load dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), "datacost.xlsx")
df = pd.read_excel(DATA_PATH)

# ✅ Build FOB dictionary with coordinates
FOBS = {}
for _, row in df.iterrows():
    fob_name = str(row["ORIGIN"]).strip()
    if fob_name not in FOBS:
        FOBS[fob_name] = {
            "lat": float(row["Origin Latitude"]),
            "lon": float(row["Origin Longitude"])
        }

# ✅ Build FOB → Destinations mapping with coordinates
fob_dest_map = {}
for _, row in df.iterrows():
    fob_name = str(row["ORIGIN"]).strip()
    dest_name = str(row["DESTINATION"]).strip()
    dest_lat = float(row["Destination Latitude"])
    dest_lon = float(row["Destination Longitude"])

    if fob_name not in fob_dest_map:
        fob_dest_map[fob_name] = []
    if not any(d["name"] == dest_name for d in fob_dest_map[fob_name]):
        fob_dest_map[fob_name].append({"name": dest_name, "lat": dest_lat, "lon": dest_lon})

OSRM_URL = "http://router.project-osrm.org/route/v1/driving/"

@app.route("/")
def index():
    return render_template("index.html", fobs=list(FOBS.keys()), fob_dest_map=fob_dest_map)

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

    # ✅ Always use OSRM if valid coordinates exist
    coords = f"{origin['lon']},{origin['lat']};{dest_lon},{dest_lat}"
    url = f"{OSRM_URL}{coords}?overview=full&geometries=geojson"
    r = requests.get(url)
    if r.status_code != 200:
        return jsonify({"error": "OSRM request failed"}), 500

    route = r.json()["routes"][0]
    distance_km = route["distance"] / 1000

    # ✅ Get cost (quoted vs estimate logic handled in cost_calculator)
    costs = get_quote_from_dataset(fob_name, dest_name, distance_km)

    return jsonify({
        "distance_km": distance_km,
        "geometry": route["geometry"],
        "costs": costs
    })

if __name__ == "__main__":
    app.run(debug=True)
