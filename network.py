import os
import osmnx as ox
import rasterio
import geopandas as gpd
from shapely.geometry import Point
import networkx as nx

# 📍 Add elevation from DEM
def add_elevation_to_nodes(G, dem_path):
    with rasterio.open(dem_path) as src:
        for node_id, data in G.nodes(data=True):
            lon, lat = data['x'], data['y']
            for val in src.sample([(lon, lat)]):
                data['elevation'] = float(val)
    return G

# 💧 Tag nodes with flood zone information
def tag_nodes_with_hazards(G, flood_path):
    flood_gdf = gpd.read_file(flood_path)
    for node_id, data in G.nodes(data=True):
        point = Point(data['x'], data['y'])
        data['in_flood_zone'] = flood_gdf.contains(point).any()
    return G

# 🚦 Assign risk weight to edges
def assign_edge_risk(G):
    for u, v, data in G.edges(data=True):
        congestion = data.get("congestion", 0.5)
        length = data.get("length", 1)
        risk_weight = (congestion * 100) + (length / 10)
        data["risk_weight"] = risk_weight
    return G

# 🌐 Basic OSMnx network loader
def load_network_basic():
    print("🌍 Loading basic Amritsar network...")
    G = ox.graph_from_place("Amritsar, Punjab, India", network_type="drive")
    center_point = (31.6340, 74.8723)
    dist = 500
    G_sub = ox.graph_from_point(center_point, dist=dist, network_type='drive', simplify=True)
    print(f"✅ Loaded basic cropped network: {len(G_sub.nodes)} nodes, {len(G_sub.edges)} edges")
    return G_sub

# 🔁 Full loader with DEM + flood zone fusion
def load_network_with_fusion():
    try:
        print("🌍 Loading Amritsar city network with geospatial fusion...")

        G = ox.graph_from_place("Amritsar, Punjab, India", network_type="drive")
        if G is None or len(G.nodes) == 0:
            raise ValueError("❌ No roads found in Amritsar area.")

        center_point = (31.6340, 74.8723)
        dist = 500
        G_small = ox.graph_from_point(center_point, dist=dist, network_type="drive", simplify=True)
        if G_small is None or len(G_small.nodes) == 0:
            raise ValueError("❌ No nodes found after cropping.")

        print(f"✅ Cropped Rani Ka Bagh network: {len(G_small.nodes)} nodes, {len(G_small.edges)} edges")

        dem_path = "data/elevation.tif"
        flood_path = "data/flood_zones.geojson"

        if os.path.exists(dem_path):
            G_small = add_elevation_to_nodes(G_small, dem_path)
        else:
            print("⚠️ DEM file not found — skipping elevation.")

        if os.path.exists(flood_path):
            G_small = tag_nodes_with_hazards(G_small, flood_path)
        else:
            print("⚠️ Flood zone file not found — skipping hazard tagging.")

        G_small = assign_edge_risk(G_small)

        return G_small

    except Exception as e:
        print(f"❌ Failed to load network: {e}")
        return None

# 🎯 Main unified function used by other modules
load_network = load_network_with_fusion