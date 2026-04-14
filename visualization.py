import folium
from streamlit_folium import folium_static
from model import EvacueeAgent
import csv
import os
import pandas as pd
import json


def plot_network_links(model, m):
    folium.map.CustomPane("roads").add_to(m)

    for u, v, data in model.network.edges(data=True):
        start_node = model.network.nodes[u]
        end_node = model.network.nodes[v]

        latlon_start = (start_node['y'], start_node['x'])
        latlon_end = (end_node['y'], end_node['x'])

        # Default to safe risk if not present
        risk_weight = data.get("risk_weight", 0)
        color = "green"
        if risk_weight > 300:
            color = "red"
        elif risk_weight > 200:
            color = "orange"
        elif risk_weight > 100:
            color = "yellow"

        folium.PolyLine(
            [latlon_start, latlon_end],
            color=color,
            weight=3,
            opacity=0.6,
            pane="roads",
            tooltip=f"Risk: {risk_weight:.1f}"
        ).add_to(m)

    # Export edge risk values
    edge_risks = []
    for u, v, data in model.network.edges(data=True):
        if "risk_weight" in data:
            edge_risks.append({
                "Edge_U": u,
                "Edge_V": v,
                "RiskWeight": data["risk_weight"]
            })
    if edge_risks:
        os.makedirs("data", exist_ok=True)
        pd.DataFrame(edge_risks).to_csv("data/edge_risk_weights.csv", index=False)


def plot_flood_zones(m):
    flood_path = "data/flood_zones.geojson"
    if os.path.exists(flood_path):
        with open(flood_path) as f:
            flood_data = json.load(f)

        folium.GeoJson(
            flood_data,
            name="Flood Zones",
            style_function=lambda x: {
                'fillColor': 'blue',
                'color': 'blue',
                'weight': 1,
                'fillOpacity': 0.4
            },
            tooltip="Flood Zone"
        ).add_to(m)


def plot_evacuation_map(model):
    center_lat, center_lon = model.map_center
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    # 📌 Add Risk Weight Legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 30px; left: 30px; width: 170px; height: 140px; 
                border:2px solid grey; z-index:9999; font-size:14px; 
                background-color:white; padding: 10px;">
    <b>Risk Weight Legend</b><br>
    <span style="background-color:green; width:10px; height:10px; display:inline-block;"></span> Very Safe (≤100)<br>
    <span style="background-color:yellow; width:10px; height:10px; display:inline-block;"></span> Low Risk (≤200)<br>
    <span style="background-color:orange; width:10px; height:10px; display:inline-block;"></span> Medium Risk (≤300)<br>
    <span style="background-color:red; width:10px; height:10px; display:inline-block;"></span> High Risk (>300)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # 📌 Add Evacuee Priority Legend
    priority_legend = """
    <div style="position: fixed; 
                bottom: 30px; right: 30px; width: 190px; height: 110px; 
                border:2px solid grey; z-index:9999; font-size:14px; 
                background-color:white; padding: 10px;">
    <b>Evacuee Priority Legend</b><br>
    <span style="background-color:purple; width:10px; height:10px; display:inline-block;"></span> High Priority<br>
    <span style="background-color:orange; width:10px; height:10px; display:inline-block;"></span> Medium Priority<br>
    <span style="background-color:blue; width:10px; height:10px; display:inline-block;"></span> Low Priority
    </div>
    """
    m.get_root().html.add_child(folium.Element(priority_legend))

    # 1. Roads
    plot_network_links(model, m)

    # 2. Flood Zones
    plot_flood_zones(m)

    # 3. Evacuees
    folium.map.CustomPane("evacuees").add_to(m)
    marker_color_map = {1: "red", 2: "orange", 3: "blue"}
    route_color_map = {1: "purple", 2: "orange", 3: "blue"}

    for agent in model.schedule.agents:
        if isinstance(agent, EvacueeAgent):
            if hasattr(agent, "location") and isinstance(agent.location, tuple):
                lat, lon = agent.location
                priority = getattr(agent, "priority", 3)
                marker_color = marker_color_map.get(priority, "blue")
                route_color = route_color_map.get(priority, "blue")

                folium.CircleMarker(
                    location=(lat, lon),
                    radius=4,
                    color=marker_color,
                    fill=True,
                    fill_color=marker_color,
                    fill_opacity=0.9,
                    weight=1,
                    pane="evacuees",
                    popup=f"Evacuee {agent.unique_id}<br>Priority: {priority}<br>Vehicle: {agent.vehicle}<br>Shelter: {agent.shelter}"
                ).add_to(m)

                if hasattr(agent, "route") and agent.route:
                    route_coords = [
                        (model.network.nodes[n]['y'], model.network.nodes[n]['x'])
                        for n in agent.route if n in model.network.nodes
                    ]
                    folium.PolyLine(
                        route_coords,
                        color=route_color,
                        weight=2,
                        opacity=0.6,
                        pane="evacuees"
                    ).add_to(m)

    # 4. Shelters
    folium.map.CustomPane("shelters").add_to(m)

    icon_map = {
        "expansive": ("green", "home"),
        "bounded": ("blue", "warehouse"),
        "secondary": ("purple", "school"),
        "temporary": ("gray", "bed")
    }

    for i, shelter in enumerate(model.shelters):
        if hasattr(shelter, "location") and isinstance(shelter.location, tuple):
            lat, lon = shelter.location
            shelter_type = getattr(shelter, "shelter_type", "unknown")
            capacity = getattr(shelter, "capacity", "?")
            shelter_id = getattr(shelter, "unique_id", f"shelter_{i}")

            color, icon = icon_map.get(shelter_type, ("black", "question"))

            folium.Marker(
                location=(lat, lon),
                popup=f"Shelter {shelter_id}<br>Type: {shelter_type}<br>Capacity: {capacity}",
                icon=folium.Icon(color=color, icon=icon, prefix='fa'),
                pane="shelters"
            ).add_to(m)

    return m
