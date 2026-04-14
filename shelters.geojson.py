import os
import json

# Always go to project_root/data, no matter where the script is run from
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(data_dir, exist_ok=True)

# Define 4 types of shelters
shelters_data = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "Expansive Shelter",
                "capacity": 5,
                "shelter_type": "expansive"
            },
            "geometry": {"type": "Point", "coordinates": [74.8720, 31.6345]}
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Bounded Shelter",
                "capacity": 10,
                "shelter_type": "bounded"
            },
            "geometry": {"type": "Point", "coordinates": [74.8735, 31.6350]}
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Secondary Shelter",
                "capacity": 20,
                "shelter_type": "secondary"
            },
            "geometry": {"type": "Point", "coordinates": [74.8710, 31.6330]}
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Temporary Shelter",
                "capacity": 999,
                "shelter_type": "temporary"
            },
            "geometry": {"type": "Point", "coordinates": [74.8700, 31.6340]}
        }
    ]
}

# Save the file to project_root/data/shelters.geojson
shelters_file_path = os.path.join(data_dir, 'shelters.geojson')
with open(shelters_file_path, 'w') as f:
    json.dump(shelters_data, f, indent=2)

print("✅ shelters.geojson successfully saved at:", os.path.abspath(shelters_file_path))
