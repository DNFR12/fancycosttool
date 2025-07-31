from flask import Flask, render_template, request, jsonify
import requests
from services.cost_calculator import calculate_costs

app = Flask(__name__)

# Example FOB data
FOBS = {
    "Houston, TX": {"lat": 29.7604, "lon": -95.3698},
    "Corpus Christi, TX": {"lat": 27.8006, "lon": -97.3964},
    "Lake Charles, LA": {"lat": 30.2266, "lon": -93.2174}
}

OSRM_URL = "http://router.project-osrm.org/route/v1/driving/"

@app.route("/")
def index():
    return render_template("index.html", fobs=list(FOBS.keys()))

@app.route("/route", methods=["POST"])
def get_route():
    data = request.json
    fob_name = data.get("fob")
    dest_lat = data.get("dest_lat")
    dest_lon = data.get("dest_lon")

    if fob_name not in FOBS:
        return jsonify({"error": "Invalid FOB"}), 400

    origin = FOBS[fob_name]
    coords = f"{origin['lon']},{origin['lat']};{dest_lon},{dest_lat}"
    url = f"{OSRM_URL}{coords}?overview=full&geometries=geojson"

    r = requests.get(url)
    if r.status_code != 200:
        return jsonify({"error": "OSRM request failed"}), 500

    route = r.json()["routes"][0]
    distance_km = route["distance"] / 1000

    # Calculate costs using your business logic
    costs = calculate_costs(distance_km)

    return jsonify({
        "distance_km": distance_km,
        "geometry": route["geometry"],
        "costs": costs
    })

if __name__ == "__main__":
    app.run(debug=True)
