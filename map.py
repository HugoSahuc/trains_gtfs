import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np

def plot_route_map(route_stop_times, stops_df):
    # Merge stop times and stops to get ordered stop coordinates
    print("OK")
    ordered_stops = route_stop_times.merge(
        stops_df, on="stop_id"
    ).sort_values("stop_sequence")

    # Prepare data for Pydeck
    stop_points = ordered_stops[["stop_lat", "stop_lon"]].rename(
        columns={"stop_lat": "lat", "stop_lon": "lon"}
    )

    # Create the line as a list of [lon, lat] pairs
    route_line = [[row["stop_lon"], row["stop_lat"]] for idx, row in ordered_stops.iterrows()]

    # Define Pydeck layers
    stop_layer = pdk.Layer(
        "ScatterplotLayer",
        data=stop_points,
        get_position='[lon, lat]',
        get_color='[255,0,0]',  # Green
        get_radius=50,
        pickable=True,
    )

    line_layer = pdk.Layer(
        "LineLayer",
        data=[{"path": route_line}],
        get_path="path",
        get_color='[0,0,255]',  # Red
        width_scale=5,
        width_min_pixels=5,
    )

    # Set the initial view
    view_state = pdk.ViewState(
        latitude=stop_points["lat"].mean(),
        longitude=stop_points["lon"].mean(),
        zoom=12,
        pitch=0,
    )

    # Render the map
    st.pydeck_chart(pdk.Deck(
        layers=[line_layer, stop_layer],
        initial_view_state=view_state,
        tooltip={"text": "Stop: {lat}, {lon}"}
    ))
