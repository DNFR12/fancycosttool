def calculate_costs(distance_km):
    # Example cost logic
    linehaul = distance_km * 2.0            # $2 per km
    fuel = linehaul * 0.15                  # 15% surcharge
    tank_wash = 150 if distance_km > 200 else 0
    other = 50
    demurrage = 100 if distance_km > 500 else 0
    total = linehaul + fuel + tank_wash + other + demurrage

    return {
        "linehaul": round(linehaul, 2),
        "fuel": round(fuel, 2),
        "tank_wash": tank_wash,
        "other": other,
        "demurrage": demurrage,
        "total": round(total, 2)
    }
