import networkx as nx
from shapely.geometry import Point
import random


def assign_shelter(priority, traffic_status, capacities):
    preferred_order = []

    # Rule-based priority matching
    if traffic_status == 1:  # Congested
        if priority == 1:
            preferred_order = ['temporary', 'bounded', 'secondary']
        elif priority == 2:
            preferred_order = ['bounded', 'secondary', 'temporary']
        else:
            preferred_order = ['secondary', 'temporary']
    else:  # Clear road
        if priority == 1:
            preferred_order = ['expansive', 'temporary']
        elif priority == 2:
            preferred_order = ['expansive', 'bounded', 'temporary']
        else:
            preferred_order = ['bounded', 'secondary', 'temporary']

    # Try to assign from available shelters
    for shelter_type in preferred_order:
        if capacities.get(shelter_type, 0) > 0:
            capacities[shelter_type] -= 1
            return shelter_type

    # 🚨 Force assignment even if all are full (log overload)
    forced_type = preferred_order[0] if preferred_order else "temporary"
    print(f"⚠️ Forced assignment to {forced_type} (over capacity)")
    return forced_type


def check_congestion(traffic_data):
    # Example logic to check congestion
    if traffic_data > 0.8:
        return "High Congestion"
    elif traffic_data > 0.5:
        return "Medium Congestion"
    else:
        return "Low Congestion"


def assign_nearest_shelter(agent, shelters_gdf):
    agent_location = Point(agent.pos[1], agent.pos[0])  # Assuming pos is (lat, lon)
    shelters_gdf['distance'] = shelters_gdf.geometry.distance(agent_location)
    nearest_shelter = shelters_gdf.loc[shelters_gdf['distance'].idxmin()]
    return nearest_shelter


def score_edge_risk(G, u, v):
    n1, n2 = G.nodes[u], G.nodes[v]
    avg_elev = (n1.get("elevation", 300) + n2.get("elevation", 300)) / 2
    flood_risk = n1.get("in_flood_zone", False) or n2.get("in_flood_zone", False)

    base_len = G[u][v][0].get("length", 1)
    penalty = 0
    if avg_elev < 230:
        penalty += 50
    if flood_risk:
        penalty += 100

    return base_len + penalty


def get_dynamic_route(G, source, destination, UT, use_rl=False, agent_state=None):
    """
    Computes route from source to destination avoiding blocked links.
    Uses RL stub if use_rl=True.

    Parameters:
    - G: NetworkX graph
    - source, destination: node IDs
    - UT: upper threshold for congestion
    - use_rl: bool flag to use RL policy
    - agent_state: dict with agent info (required if use_rl is True)

    Returns:
    - List of nodes representing the path
    """
    if use_rl and agent_state:
        environment_state = {"graph": G}  # expand if needed
        return get_rl_route(agent_state, environment_state)

    # Normal rule-based routing
    G_filtered = G.copy()
    congested_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('congestion', 0) > UT]
    G_filtered.remove_edges_from(congested_edges)

    for u, v, data in G_filtered.edges(data=True):
        data["risk_weight"] = score_edge_risk(G_filtered, u, v)

    try:
        return nx.shortest_path(G_filtered, source=source, target=destination, weight="risk_weight")
    except nx.NetworkXNoPath:
        return []


def predict_congestion_lstm(edge_history):
    """
    Stub function to simulate LSTM-based traffic prediction.

    Parameters:
    - edge_history: dict with edge keys (u, v) and past congestion values

    Returns:
    - predicted_congestion: dict with edge keys and predicted values [0, 1]
    """
    predicted_congestion = {}
    for edge in edge_history.keys():
        predicted_congestion[edge] = random.uniform(0.1, 0.95)  # simulate a prediction
    return predicted_congestion


def assign_shelter_dynamic(agent, shelters, G, capacities):
    """
    Assigns the most suitable shelter to an agent based on mobility, accessibility, and capacity.

    Parameters:
    - agent: Agent object with 'current_node' and 'vehicle'
    - shelters: List of ShelterAgent objects
    - G: NetworkX graph
    - capacities: Dict of shelter_type -> remaining count

    Returns:
    - Chosen shelter object or None
    """
    scored_shelters = []

    for shelter in shelters:
        shelter_node = shelter.shelter_node
        shelter_type = shelter.shelter_type
        shelter_access_type = getattr(shelter, 'access_type', agent.vehicle)  # fallback to vehicle type

        # Skip full shelters
        if capacities.get(shelter_type, 0) <= 0:
            continue

        try:
            distance = nx.shortest_path_length(G, agent.current_node, shelter_node, weight='length')
        except nx.NetworkXNoPath:
            continue

        cost = distance
        if agent.vehicle != shelter_access_type:
            cost += 100  # penalty for unsuitable shelter access

        scored_shelters.append((shelter, cost))

    if not scored_shelters:
        return None

    chosen_shelter = min(scored_shelters, key=lambda x: x[1])[0]
    capacities[chosen_shelter.shelter_type] -= 1
    return chosen_shelter


def get_rl_route(agent_state, environment_state):
    """
    Placeholder for Reinforcement Learning (MARL) route logic.

    Simulates imperfect RL by modifying shortest path occasionally.

    Parameters:
    - agent_state: dict with 'current_node' and 'destination'
    - environment_state: dict with 'graph'

    Returns:
    - List of node IDs representing chosen path
    """
    current_node = agent_state["current_node"]
    destination = agent_state["destination"]
    G = environment_state["graph"]

    try:
        # ✅ Start with shortest path
        path = nx.shortest_path(G, source=current_node, target=destination, weight="risk_weight")

        # ✅ Simulate RL exploration (random deviation)
        if len(path) > 3 and random.random() < 0.3:
            path = path[:-1]  # randomly truncate last node

        return path

    except nx.NetworkXNoPath:
        return [current_node]  # fallback: stay in place