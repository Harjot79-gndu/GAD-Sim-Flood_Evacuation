# GAD-Sim-Flood_Evacuation
GAD-Sim: An Integrated GIS-ABDES Framework for Data-Driven Urban Flood Evacuation Modelling and Decision 
Research Compendium for Manuscript Submission to Environmental Modelling and Software.

## Overview
GAD-Sim (GIS-ABM-DES Simulator) is an integrated simulation framework for modelling and optimising urban flood evacuation. The framework combines Geographic Information Systems (GIS), Agent-Based Modelling (ABM), and Discrete Event Simulation (DES) with machine learning techniques, including Long Short-Term Memory (LSTM) networks and Multi-Agent Reinforcement Learning (MARL).

It is designed to support decision-making in time-critical disaster scenarios by incorporating behavioural heterogeneity using the reluctance score, LSTM-based congestion-aware routing, and mobility-aware shelter allocation through a dual-criteria suitability score.

---

## Key Features
- GIS-integrated road network modelling (OSM + DEM)
- Congestion-aware dynamic routing
- MARL-based adaptive route selection
- LSTM-based traffic congestion prediction
- Mobility-aware dynamic shelter allocation
- Behavioural modelling using probabilistic reluctance
- Threshold-based traffic throttling mechanism
- Interactive visualisation using Streamlit

---

## Case Study: Amritsar, India
The provided code is configured to run in the Amritsar city area.

## To quick start: Clone the repository:
git clone https://github.com/Harjot79-gndu/GAD-Sim-Flood_Evacuation.git
cd GAD-Sim

## Install Dependencies 
pip install -r requirements.txt

## Main Entry Point 
app.py
It controls UI, simulation triggers, call model and visualisation and displays results

It can be executed in the terminal using :
streamlit run app.py
