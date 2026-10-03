"""Explicit authorized development set; held-out and wet races are denied."""
DEVELOPMENT_RACES = {
    "bahrain_2021": {"year": 2021, "race": "Bahrain", "scheduled_laps": 56},
    "spain_2022": {"year": 2022, "race": "Spain", "scheduled_laps": 66},
    "france_2022": {"year": 2022, "race": "France", "scheduled_laps": 53},
}


def race_key(data):
    for key, race in DEVELOPMENT_RACES.items():
        if (data.get("year"), data.get("race")) == (race["year"], race["race"]):
            return key
    raise ValueError("Approved development races only: Bahrain 2021, Spain 2022, France 2022")
