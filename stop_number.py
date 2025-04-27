import streamlit as st
import pandas as pd
import zipfile

st.title("GTFS: Find Routes Serving a Stop")

uploaded_file = st.file_uploader("Upload GTFS ZIP", type="zip")
stop_name = st.text_input("Enter Stop Name (case-insensitive, partial match allowed)")

if uploaded_file:
    with zipfile.ZipFile(uploaded_file) as z:
        with z.open("stops.txt") as f:
            stops_df = pd.read_csv(f, dtype={'stop_id': str, 'stop_name': str})
        with z.open("stop_times.txt") as f:
            stop_times_df = pd.read_csv(f, dtype={'trip_id': str, 'stop_id': str})
        with z.open("trips.txt") as f:
            trips_df = pd.read_csv(f, dtype={'trip_id': str, 'route_id': str})
        with z.open("routes.txt") as f:
            routes_df = pd.read_csv(f, dtype={'route_id': str})

    # Normalize
    stops_df['stop_name'] = stops_df['stop_name'].str.strip().str.lower()
    stop_times_df['stop_id'] = stop_times_df['stop_id'].str.strip()
    stops_df['stop_id'] = stops_df['stop_id'].str.strip()
    
    st.subheader("Available stops:")
    st.dataframe(stops_df, use_container_width=True)

    if stop_name:
        matching_stops = stops_df[stops_df['stop_name'].str.contains(stop_name.strip().lower())]
    
        if matching_stops.empty:
            st.error("No stops found matching that name.")
        else:
            st.write("Matching stops found:", matching_stops[['stop_id', 'stop_name']])
    
            # Find all stop_ids
            stop_ids = matching_stops['stop_id'].unique()
            # Find all trip_ids that visit these stops
            trips_for_stops = stop_times_df[stop_times_df['stop_id'].isin(stop_ids)]['trip_id'].unique()
            # Find all routes for these trips
            trips_matched = trips_df[trips_df['trip_id'].isin(trips_for_stops)]
            # Count trips per route
            route_trip_counts = trips_matched.groupby('route_id').size().reset_index(name='num_trips')
            # Merge with route info
            routes_info = routes_df.merge(route_trip_counts, on='route_id', how='inner')
    
            if routes_info.empty:
                st.warning("No routes found serving this stop.")
            else:
                st.subheader("Routes serving this stop and number of trips:")
                st.dataframe(routes_info[['route_id', 'route_short_name', 'route_long_name', 'num_trips']])
