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

## Case Study: Amritsar, India
The provided code is configured to run on the Amritsar city area.

## Main Entry Point 
app.py
It controls 
UI, simulation triggers, call model and visulization and display results

It can be executed in terminal using :
streamlit run app.py
