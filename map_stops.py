import streamlit as st
import pandas as pd
import zipfile

st.title("Route-Specific GTFS Stop Visualizer")
uploaded_file = st.file_uploader("Upload GTFS ZIP", type="zip")
route_name = st.text_input("Enter Route Name (exact match required)")

if uploaded_file:
    with zipfile.ZipFile(uploaded_file) as z:
        # Load required GTFS tables
        with z.open("stop_times.txt") as f:
            stop_times_df = pd.read_csv(f, dtype={'stop_id': str, 'trip_id': str})

        with z.open("stops.txt") as f:
            stops_df = pd.read_csv(f, dtype={'stop_id': str})

        with z.open("trips.txt") as f:
            trips_df = pd.read_csv(f, dtype={'trip_id': str, 'route_id': str})

        with z.open("routes.txt") as f:
            routes_df = pd.read_csv(f, dtype={'route_id': str})


    # Show all routes with trip counts for user reference
    trip_counts = trips_df.groupby('route_id').size().reset_index(name='num_trips')
    routes_with_trips = routes_df.merge(trip_counts, on='route_id', how='left').fillna(0)
    st.subheader("Available routes and number of trips:")
    st.dataframe(routes_with_trips[['route_id', 'route_short_name', 'route_long_name', 'num_trips']])
    

    if route_name:
        # Find matching route
        route_filter = (
            (routes_df['route_short_name'] == route_name) |
            (routes_df['route_long_name'] == route_name)
        )

        if not routes_df[route_filter].empty:
            route_id = routes_df[route_filter].iloc[0]['route_id']

            # Get trips for this route
            route_trips = trips_df[trips_df['route_id'] == route_id]
            st.info(f"Route '{route_name}' has {len(route_trips)} trips.")

            # Get stop times for these trips
            route_stop_times = stop_times_df[
                stop_times_df['trip_id'].isin(route_trips['trip_id'])
            ].drop_duplicates(subset=['stop_id'])
            
            st.subheader("Stop Times for Selected Route")
            st.dataframe(route_stop_times, use_container_width=True)

            # Get unique stops
            stop_times_df['stop_id'] = stop_times_df['stop_id'].astype(str).str.strip()
            stops_df['stop_id'] = stops_df['stop_id'].astype(str).str.strip()
            route_stops = stops_df[
                stops_df['stop_id'].isin(route_stop_times['stop_id'])
            ]
            
            st.subheader("Stops for Selected Route")
            st.dataframe(route_stops, use_container_width=True)

            # Display results
            st.subheader(f"Route {route_name} has {len(route_stops)} unique stops")
            if not route_stops.empty:
                st.map(route_stops, latitude="stop_lat", longitude="stop_lon")
            else:
                st.warning("No stops found for this route. Check if the route name is correct and that trips/stops exist.")

            # Show additional route info
            st.write("**Route Details:**")
            st.dataframe(routes_df[route_filter].T, use_container_width=True)
        else:
            st.error(f"No route found with name: {route_name}")