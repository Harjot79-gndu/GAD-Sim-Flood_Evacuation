# GAD-Sim-Flood_Evacuation
GAD-Sim: An Integrated GIS-ABDES Framework for Data-Driven Urban Flood Evacuation Modeling and Decision 
## Overview
GAD-Sim (GIS-ABM-DES Simulator) is an integrated simulation framework for modeling and optimizing urban flood evacuation. The framework combines Geographic Information Systems (GIS), Agent-Based Modeling (ABM), and Discrete Event Simulation (DES) with machine learning techniques, including Long Short-Term Memory (LSTM) networks and Multi-Agent Reinforcement Learning (MARL).

It is designed to support decision-making in time-critical disaster scenarios by incorporating behavioral heterogeneity using the reluctance score, LSTM-based congestion-aware routing, and mobility-aware shelter allocation through dual-criteria suitability score.

---

## Key Features
- GIS-integrated road network modeling (OSM + DEM)
- Congestion-aware dynamic routing
- MARL-based adaptive route selection
- LSTM-based traffic congestion prediction
- Mobility-aware dynamic shelter allocation
- Behavioral modeling using probabilistic reluctance
- Threshold-based traffic throttling mechanism
- Interactive visualization using Streamlit

---

## 🔷 Repository Structure
GAD-Sim/
│
├── src/                 # Core simulation modules
├── models/              # Trained LSTM / MARL models
├── app/                 # Streamlit dashboard
├── code/                # Experimental analysis
├── results/             # Simulation outputs
│
├── config.yaml          # Simulation parameters
├── app.py               # Main execution script
├── requirements.txt     # Dependencies
├── README.md
└── LICENSE
