from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
from services.cost_calculator import get_quote_from_dataset
import os

app = Flask(__name__)

# ✅ Load FOBs dynamically from the dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), "datacost.xlsx")
df = pd.read_excel(DATA_PATH)

# Create a FOB dictionary { "FOB Name": {"lat": .., "lon": ..} }
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
    # ✅ Pass dynamically loaded FOB names to frontend
    return render_template("index.html", fobs=list(FOBS.keys()))

@app.route("/route", methods=["POST"])
def get_route():
    data = request.json
    fob_name = data.get("fob")
    dest_name = data.get("destination_name", "")
    dest_lat = data.get("dest_lat")
    dest_lon = data.get("dest_lon")

    # ✅ Check if FOB exists in dataset
    if fob_name not in FOBS:
        return jsonify({"error": "FOB not found in dataset"}), 400

    origin = FOBS[fob_name]
    coords = f"{origin['lon']},{origin['lat']};{dest_lon},{dest_lat}"
    url = f"{OSRM_URL}{coords}?overview=full&geometries=geojson"

    r = requests.get(url)
    if r.status_code != 200:
        return jsonify({"error": "OSRM request failed"}), 500

    route = r.json()["routes"][0]
    distance_km = route["distance"] / 1000

    # ✅ Retrieve cost from dataset (exact or closest match)
    costs = get_quote_from_dataset(fob_name, dest_name, distance_km)

    return jsonify({
        "distance_km": distance_km,
        "geometry": route["geometry"],
        "costs": costs
    })

if __name__ == "__main__":
    app.run(debug=True)
