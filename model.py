from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import numpy as np
import random
from logic import assign_shelter
from logic import assign_shelter_dynamic
from logic import get_dynamic_route
from network import load_network
import geopandas as gpd
import pandas as pd
import os
import json
import osmnx as ox
from logic import predict_congestion_lstm
import csv

# Constants for evacuee priority
HIGH, MEDIUM, LOW = 1, 2, 3
VEHICLES = ['helicopter', 'ambulance', 'truck', 'car']

# ✨ Function to generate random shelters
def generate_random_shelters(network, output_path):
    all_nodes = list(network.nodes(data=True))
    shelter_categories = {
        "expansive": random.randint(1, 2),
        "bounded": random.randint(2, 3),
        "secondary": random.randint(3, 5),
        "temporary": random.randint(5, 6)
    }

    features = []
    used_nodes = set()

    for shelter_type, count in shelter_categories.items():
        for _ in range(count):
            while True:
                node = random.choice(all_nodes)
                node_id = node[0]
                if node_id not in used_nodes:
                    used_nodes.add(node_id)
                    break

            lon = node[1]['x']
            lat = node[1]['y']

            capacity = {
                "expansive": random.randint(400, 800),
                "bounded": random.randint(150, 300),
                "secondary": random.randint(50, 150),
                "temporary": random.randint(30, 100)
            }[shelter_type]

            shelter_feature = {
                "type": "Feature",
                "properties": {
                    "name": f"{shelter_type.capitalize()} Shelter {len(features)+1}",
                    "capacity": capacity,
                    "shelter_type": shelter_type
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                }
            }
            features.append(shelter_feature)

    shelters_geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_path, 'w') as f:
        json.dump(shelters_geojson, f, indent=2)

    print(f"✅ Random shelters generated and saved to {output_path}")

class EvacueeAgent(Agent):
    def __init__(self, unique_id, model, priority, current_node=None):
        super().__init__(unique_id, model)
        self.departure_time = None
        self.priority = priority
        self.current_node = current_node
        self.shelter = None
        self.vehicle = None
        self.reluctance = np.random.beta(2, 5)
        self.readiness = 0

    def calculate_departure_time(self, current_time):
        if self.priority == HIGH:
            delay = np.random.exponential(scale=1)
        else:
            delay = np.random.rayleigh(scale=2)

        self.departure_time = current_time + delay

        G = self.model.network
        all_nodes = list(G.nodes(data=True))
        if not all_nodes:
            raise ValueError("The network has no nodes to assign to evacuees.")

        random_node = random.choice(all_nodes)
        x, y = random_node[1]['x'], random_node[1]['y']
        nearest_node = ox.distance.nearest_nodes(G, x, y)
        self.location = (G.nodes[nearest_node]['y'], G.nodes[nearest_node]['x'])
        print(f"Evacuee {self.unique_id} assigned to location: {self.location}")

    def step(self):
        current_time = self.model.schedule.time
        if self.departure_time is None:
            self.calculate_departure_time(current_time)

        if current_time >= self.departure_time:
            self.model.update_congestion()
            self.shelter = assign_shelter(self.priority, self.model.traffic_status, self.model.shelter_capacities)
            if self.priority == HIGH:
                self.vehicle = "helicopter"
            elif self.priority == MEDIUM:
                self.vehicle = "ambulance"
            else:
                self.vehicle = random.choice(["truck", "car"])
            self.readiness = 1

            print(f"Evacuee {self.unique_id} assigned to shelter: {self.shelter}, vehicle: {self.vehicle}")
            print(f"Remaining capacities: {self.model.shelter_capacities}")

            # ✨ Log evacuee details into CSV
            self.model.evacuee_logs.append({
                "Evacuee ID": self.unique_id,
                "Priority": self.priority,
                "Assigned Shelter": self.shelter,
                "Vehicle": self.vehicle,
                "Departure Time": round(self.departure_time, 2),
                "Readiness": int(self.readiness)
            })

        if not self.readiness:
            if np.random.rand() > self.reluctance:
                self.readiness = True
                chosen = assign_shelter_dynamic(self, self.model.shelters, self.model.network, self.model.capacities)
                if chosen:
                    self.shelter_node = chosen.shelter_node
                    use_rl = True

                    agent_state = {
                        "current_node": self.current_node,
                        "destination": self.shelter_node,
                        "priority": self.priority,
                        "vehicle": self.vehicle,
                        "id": self.unique_id
                    }

                    self.route = get_dynamic_route(
                        self.model.network,
                        self.current_node,
                        self.shelter_node,
                        self.model.UT,
                        use_rl=use_rl,
                        agent_state=agent_state
                    )

                    # 🧠 Log MARL decision
                    if use_rl and hasattr(self, "route") and self.route:
                        if not hasattr(self.model, "marl_log_path"):
                            self.model.marl_log_path = os.path.join(os.path.dirname(__file__), 'data', 'marl_route_log.csv')

                        if self.model.schedule.time == 0:
                            with open(self.model.marl_log_path, 'w', newline='') as f:
                                writer = csv.writer(f)
                                writer.writerow(["Timestep", "AgentID", "StartNode", "EndNode", "RouteLength", "RouteNodes", "RouteScore"])

                        G = self.model.network
                        risk_score = 0
                        for i in range(len(self.route) - 1):
                            u, v = self.route[i], self.route[i + 1]
                            edge_data = G.get_edge_data(u, v, default={})
                            risk_score += edge_data.get("risk_weight", 0)

                        with open(self.model.marl_log_path, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                self.model.schedule.time,
                                self.unique_id,
                                self.current_node,
                                self.shelter_node,
                                len(self.route),
                                "->".join(map(str, self.route)),
                                round(risk_score, 2)
                            ])

                    if self.route:
                        self.model.route_lengths.append((self.unique_id, len(self.route)))


class ShelterAgent(Agent):
    def __init__(self, unique_id, model, location, shelter_node, capacity, shelter_type):
        super().__init__(unique_id, model)
        self.location = location
        self.shelter_node = shelter_node
        self.capacity = capacity
        self.shelter_type = shelter_type

class EvacuationModel(Model):
    def __init__(self, N, UT, LT, max_steps=100):
        self.num_agents = N
        self.schedule = RandomActivation(self)
        self.traffic_status = 0
        self.UT = UT
        self.LT = LT
        self.shelter_capacities = {
            'expansive': 1000,
            'bounded': 1000,
            'secondary': 1000,
            'temporary': 1000
        }
        self.capacities = self.shelter_capacities.copy()
        self.step_count = 0
        self.max_steps = max_steps
        self.shelters = []
        self.evacuee_logs = []
        self.route_lengths = []
        self.blocked_edges_log = []
        self.marl_route_log = []
        self.lstm_congestion_predictions = []


        print(f"🛖 Initial shelter capacities: {self.shelter_capacities}")

        # Load network
        self.network = load_network()

        if self.network is None or len(self.network.nodes) == 0:
            raise ValueError("❌ Network has no nodes after loading.")

        print(f"✅ Network loaded: {len(self.network.nodes)} nodes, {len(self.network.edges)} edges")

        # Calculate map center
        nodes = list(self.network.nodes(data=True))
        center_lat = sum(node[1]["y"] for node in nodes) / len(nodes)
        center_lon = sum(node[1]["x"] for node in nodes) / len(nodes)
        self.map_center = (center_lat, center_lon)

        print(f"📍 Map center set at: {self.map_center}")

        self.grid = MultiGrid(width=100, height=100, torus=False)

        # Evacuees
        for i in range(N):
            random_node = random.choice(list(self.network.nodes))
            evacuee = EvacueeAgent(unique_id=i, model=self, priority=random.randint(1, 3), current_node=random_node)
            self.schedule.add(evacuee)

        # Auto-generate shelters
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        shelters_file_path = os.path.join(data_dir, 'shelters.geojson')
        os.makedirs(data_dir, exist_ok=True)

        generate_random_shelters(self.network, shelters_file_path)

        # Load shelters
        self.shelters_gdf = gpd.read_file(shelters_file_path)
        print("Shelter GeoDataFrame columns:", self.shelters_gdf.columns)
        print(self.shelters_gdf[['name', 'capacity', 'shelter_type']])

        all_network_nodes = list(self.network.nodes)

        for idx, row in self.shelters_gdf.iterrows():
            shelter_type = row['shelter_type'] if 'shelter_type' in row and pd.notnull(row['shelter_type']) else 'temporary'
            capacity = row['capacity'] if 'capacity' in row and pd.notnull(row['capacity']) else 100

            shelter_node = random.choice(all_network_nodes)

            shelter_location = (
                self.network.nodes[shelter_node]['y'],
                self.network.nodes[shelter_node]['x']
            )

            if shelter_type in self.shelter_capacities:
                self.shelter_capacities[shelter_type] += capacity
                print(f"✅ Loaded shelter: {row['name']}, type={shelter_type}, capacity={capacity}")
            else:
                print(f"⚠️ Unknown shelter type: {shelter_type}")

            shelter_agent = ShelterAgent(
                unique_id=f"shelter_{idx}",
                model=self,
                location=shelter_location,
                shelter_node=shelter_node,
                capacity=capacity,
                shelter_type=shelter_type
            )
            self.schedule.add(shelter_agent)
            self.grid.place_agent(shelter_agent, (int(shelter_location[1]) % 100, int(shelter_location[0]) % 100))
            self.shelters.append(shelter_agent)

    
    def update_congestion(self):
        # ✅ Build dummy history: assume we have congestion history per edge
        # For now, we simulate history as random values (in real use, you'd collect past logs)
        edge_history = {(u, v): [random.uniform(0, 1) for _ in range(5)]
                    for u, v, _ in self.network.edges(data=True)}

        # ✅ Get predicted congestion from LSTM placeholder
        predicted = predict_congestion_lstm(edge_history)

        # ✅ Assign predicted values to each edge
        for (u, v), pred_value in predicted.items():
            if self.network.has_edge(u, v):
                self.network[u][v][0]["congestion"] = pred_value  # assumes single edge per u-v pair

        
        # ✅ Refresh log on first step
        self.lstm_log_path = os.path.join(os.path.dirname(__file__), 'data', 'lstm_congestion_predictions.csv')
        if self.step_count == 0:
            with open(self.lstm_log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestep", "Edge_U", "Edge_V", "Predicted_Congestion"])

        with open(self.lstm_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            for (u, v), val in predicted.items():
                writer.writerow([self.schedule.time, u, v, round(val, 4)])

        

        # ✅ Update global traffic status (used by shelter logic)
        avg_congestion = sum(predicted.values()) / len(predicted)
        if avg_congestion > self.UT:
            self.traffic_status = 1  # congested
        elif avg_congestion < self.LT:
            self.traffic_status = 0  # clear

    def apply_throttling(self):
        for u, v, d in self.network.edges(data=True):
            cl = d.get("congestion", random.random())
            if cl >= self.UT:
                d["blocked"] = True
            elif cl <= self.LT:
                d["blocked"] = False

    def save_logs_to_csv(self):
        if not self.evacuee_logs:
            print("⚠️ No evacuee logs to save.")
            return

        # ✅ Convert evacuee log to DataFrame
        logs_df = pd.DataFrame(self.evacuee_logs)

        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)

        # ✅ Save main evacuee logs
        logs_df.to_csv(os.path.join(data_dir, "evacuee_logs.csv"), index=False)

        # ✅ Save route length logs
        pd.DataFrame(self.route_lengths, columns=['EvacueeID', 'RouteLength']).to_csv(
        os.path.join(data_dir, "route_lengths.csv"), index=False
        )

        # ✅ Save blocked edge timeline logs
        pd.DataFrame({
        "Step": list(range(len(self.blocked_edges_log))),
        "BlockedEdges": self.blocked_edges_log
        }).to_csv(os.path.join(data_dir, "blocked_edges_timeline.csv"), index=False)

        # ✅ Save MARL route log (if available)
        if self.marl_route_log:
            pd.DataFrame(self.marl_route_log).to_csv(
                os.path.join(data_dir, "marl_route_log.csv"), index=False
            )

        # ✅ Save LSTM congestion predictions (if available)
        if self.lstm_congestion_predictions:
            pd.DataFrame(self.lstm_congestion_predictions).to_csv(
                os.path.join(data_dir, "lstm_congestion_predictions.csv"), index=False
            )

        print("✅ All simulation logs saved.")


    def step(self):
        if self.step_count >= self.max_steps:
            print("Simulation has reached maximum steps. Stopping.")
            return

        print(f"Step {self.step_count}: Current shelter capacities: {self.shelter_capacities}")
        self.apply_throttling()
        self.schedule.step()
        self.schedule.time += 1 
        self.step_count += 1

        # ✨ Track congestion
        blocked_count = sum(1 for _, _, d in self.network.edges(data=True) if d.get("blocked"))
        self.blocked_edges_log.append(blocked_count)

        # ✨ Save evacuee logs when simulation ends
        if self.step_count >= self.max_steps:
            self.save_logs_to_csv()
