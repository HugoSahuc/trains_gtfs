import streamlit as st
import pandas as pd
import zipfile
from datetime import timedelta

def parse_gtfs_time(t):
    """Parse HH:MM:SS GTFS time, allowing for hours > 24."""
    h, m, s = map(int, t.split(":"))
    return timedelta(hours=h, minutes=m, seconds=s)

st.title("GTFS Trip Duration & Stop Interval Calculator")

uploaded_file = st.file_uploader("Upload GTFS ZIP", type="zip")
trip_id = st.text_input("Enter trip_id")

if uploaded_file and trip_id:
    with zipfile.ZipFile(uploaded_file) as z:
        with z.open("stop_times.txt") as f:
            stop_times = pd.read_csv(f, dtype={'trip_id': str})

    # Filter for the given trip_id and sort by stop_sequence
    trip_times = stop_times[stop_times['trip_id'] == trip_id].sort_values("stop_sequence")

    if trip_times.empty:
        st.error("No stop_times found for this trip_id.")
    else:
        # Parse all arrival times as timedeltas
        trip_times['arrival_td'] = trip_times['arrival_time'].apply(parse_gtfs_time)
        trip_times['departure_td'] = trip_times['departure_time'].apply(parse_gtfs_time)

        # Trip duration
        first_departure = trip_times['departure_td'].iloc[0]
        last_arrival = trip_times['arrival_td'].iloc[-1]
        duration = (last_arrival - first_departure).total_seconds() / 60  # in minutes

        # Time between stops (arrival to arrival)
        intervals = trip_times['arrival_td'].diff().dropna().dt.total_seconds() / 60  # in minutes

        if not intervals.empty:
            avg_interval = intervals.mean()
            max_interval = intervals.max()
            min_interval = intervals.min()
        else:
            avg_interval = max_interval = min_interval = 0

        st.write(f"**Trip `{trip_id}` stats:**")
        st.write(f"- Total duration: **{duration:.1f} minutes**")
        st.write(f"- Average time between stops: **{avg_interval:.1f} minutes**")
        st.write(f"- Max time between stops: **{max_interval:.1f} minutes**")
        st.write(f"- Min time between stops: **{min_interval:.1f} minutes**")

        st.subheader("Stop times for this trip")
        st.dataframe(trip_times, use_container_width=True)