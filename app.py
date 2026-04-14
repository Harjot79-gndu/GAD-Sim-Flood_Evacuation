import sys
import os
import builtins
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import csv

import streamlit as st
from model import EvacuationModel
from visualization import plot_evacuation_map
from streamlit_folium import st_folium
from datetime import datetime
from logic import get_rl_route



# Save the original print function globally
print_original = builtins.print

# Placeholder for output_file
output_file = None

# Define my_print with timestamp
def my_print(*args, **kwargs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = " ".join(str(arg) for arg in args)
    print_original(f"{timestamp} - {message}", **kwargs)
    if output_file and not output_file.closed:
        print_original(f"{timestamp} - {message}", file=output_file)

    #if output_file:
        #print_original(f"{timestamp} - {message}", file=output_file)

# Override print globally
builtins.print = my_print

# -- Streamlit GUI below --

st.set_page_config(layout="wide")
st.title("🚨 Flood Evacuation Simulation - Amritsar City Area")

# User Inputs
st.markdown("### Configure Simulation Settings")
#num_agents = st.slider("Number of Evacuees", 10, 500, 100)
#num_agents = st.slider("Number of Evacuees", min_value=10, max_value=1000, step=50, value=100)
num_agents = st.slider("Number of Evacuees", min_value=100, max_value=1000, step=100, value=1000)

ut = st.slider("Upper Congestion Threshold (UT)", 0.1, 1.0, 0.8)
lt = st.slider("Lower Congestion Threshold (LT)", 0.0, 0.9, 0.3)

if "model" not in st.session_state:
    st.session_state.model = None
if "map" not in st.session_state:
    st.session_state.map = None
if "simulation_done" not in st.session_state:
    st.session_state.simulation_done = False

# 🚀 Run Simulation Button
if st.button("Run Simulation"):
    try:
        # 🧹 Step 1: Clean old logs before simulation
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        log_files = [
            "evacuee_logs.csv",
            "route_lengths.csv",
            "blocked_edges_timeline.csv",
            "lstm_congestion_predictions.csv",
            "marl_route_log.csv"
        ]
        for filename in log_files:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)

        # 🧼 Step 2: Overwrite simulation output file
        output_file = open("simulation_output.txt", "w", encoding="utf-8")

        print("\n🚨 Starting Simulation...")
        st.session_state.model = EvacuationModel(N=num_agents, UT=ut, LT=lt)

        with st.spinner('Running simulation, please wait...'):
            for i in range(100):
                st.session_state.model.step()

        # ✅ Step 3: Save logs
        st.session_state.model.save_logs_to_csv()

        st.session_state.simulation_done = True
        st.success("✅ Simulation complete! You can now show the map.")
        print("✅ Simulation complete!")

    except Exception as e:
        st.error(f"🚫 Simulation failed: {e}")
        print(f"🚫 Simulation failed: {e}")

    finally:
        if output_file:
            output_file.close()

# 📍 Show Map Button
if st.button("Show Evacuation Map"):
    if st.session_state.model and st.session_state.simulation_done:
        m = plot_evacuation_map(st.session_state.model)
        st.session_state.map = m
    else:
        st.warning("⚠️ Please run the simulation first!")

# Show Map
if st.session_state.map:
    st.markdown("### 📍 Evacuation Map of Amritsar City Area")
    st_folium(
        st.session_state.map,
        height=600,
        key="static_map",
        returned_objects=[],
        use_container_width=True
    )

# Risk Weight Legend
st.markdown("""
<div style="background-color:#f9f9f9; border:2px solid grey; padding:10px; width:300px;">
<b>🛣️ Risk Weight Legend</b><br>
🟩 Very Safe (≤100)<br>
🟨 Low Risk (≤200)<br>
🟧 Medium Risk (≤300)<br>
🟥 High Risk (>300)
</div>
""", unsafe_allow_html=True)

# Priority Legend
st.markdown("""
<div style="background-color:#f9f9f9; border:2px solid grey; padding:10px; width:300px;">
<b>🧍 Evacuee Priority Legend</b><br>
🟣 High Priority<br>
🟠 Medium Priority<br>
🔵 Low Priority
</div>
""", unsafe_allow_html=True)


