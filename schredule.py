import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import zipfile

st.title("GTFS : Trouver les lignes desservant un stop et les prochains passages")

uploaded_file = st.file_uploader("Télécharger le fichier GTFS ZIP", type="zip")
stop_name = st.text_input("Nom du stop (insensible à la casse, recherche partielle autorisée)")

def get_active_service_ids(calendar_df, calendar_dates_df, today):
    today_str = today.strftime("%Y%m%d")
    weekday = today.strftime("%A").lower()  # ex : 'monday'

    # 1. Depuis calendar.txt
    cal_active = calendar_df[
        (calendar_df['start_date'] <= today_str) &
        (calendar_df['end_date'] >= today_str) &
        (calendar_df[weekday] == 1)
    ]['service_id'].tolist()

    # 2. Depuis calendar_dates.txt
    added = calendar_dates_df[
        (calendar_dates_df['date'] == today_str) &
        (calendar_dates_df['exception_type'] == 1)
    ]['service_id'].tolist()
    removed = calendar_dates_df[
        (calendar_dates_df['date'] == today_str) &
        (calendar_dates_df['exception_type'] == 2)
    ]['service_id'].tolist()

    # Ensemble final : (services actifs + ajoutés) - supprimés
    service_ids = set(cal_active) | set(added)
    service_ids -= set(removed)
    return service_ids

if uploaded_file:
    with zipfile.ZipFile(uploaded_file) as z:
        stops_df = pd.read_csv(z.open("stops.txt"), dtype=str)
        stop_times_df = pd.read_csv(z.open("stop_times.txt"), dtype=str)
        trips_df = pd.read_csv(z.open("trips.txt"), dtype=str)
        routes_df = pd.read_csv(z.open("routes.txt"), dtype=str)
        calendar_df = pd.read_csv(z.open("calendar.txt"), dtype={'monday': int, 'tuesday': int, 'wednesday': int, 'thursday': int, 'friday': int, 'saturday': int, 'sunday': int, 'start_date': str, 'end_date': str, 'service_id': str})
        calendar_dates_df = pd.read_csv(z.open("calendar_dates.txt"), dtype={'service_id': str, 'date': str, 'exception_type': int})

    st.subheader("Stops disponibles :")
    unique_stops_df = stops_df.drop_duplicates(subset=['stop_name'])
    st.dataframe(unique_stops_df, use_container_width=True)

    if stop_name:
        now = datetime.now()
        active_service_ids = get_active_service_ids(calendar_df, calendar_dates_df, now)
        if not active_service_ids:
            st.warning("Aucun service actif trouvé pour aujourd'hui.")
            st.stop()

        # 2. Filtrer les trajets par services actifs
        active_trips_df = trips_df[trips_df['service_id'].isin(active_service_ids)]

        # 3. Correspondance des arrêts
        matched_stops = stops_df[stops_df['stop_name'].str.contains(stop_name, case=False, na=False)]
        if matched_stops.empty:
            st.warning("Aucun stop trouvé correspondant à ce nom.")
            st.stop()

        st.subheader("Stops correspondants")
        st.dataframe(matched_stops[['stop_id', 'stop_name']])

        # 4. Trouver les trajets actifs desservant ces arrêts
        trips_at_stop = stop_times_df[stop_times_df['stop_id'].isin(matched_stops['stop_id'])]
        trips_at_stop = trips_at_stop[trips_at_stop['trip_id'].isin(active_trips_df['trip_id'])]

        # 5. Fusionner pour obtenir les infos sur les lignes
        trips_with_routes = trips_at_stop.merge(active_trips_df[['trip_id', 'route_id']], on='trip_id')
        trips_with_routes = trips_with_routes.merge(routes_df, on='route_id')

        # 6. Pour chaque ligne, obtenir les 2 prochains passages
        now_time = now.replace(second=0, microsecond=0)
        results = []

        for route_id, group in trips_with_routes.groupby('route_id'):
            route_info = group.iloc[0]
            times = group['departure_time'].dropna().unique()
            departures = []
            for t in times:
                h, m, s = map(int, t.split(":"))
                # Les horaires GTFS peuvent dépasser 24:00:00
                dep_time = now_time.replace(hour=0, minute=0, second=0) + timedelta(hours=h, minutes=m, seconds=s)
                if dep_time >= now_time:
                    departures.append(dep_time)
            departures.sort()
            next_two = departures[:2]
            for dep in next_two:
                mins_away = int((dep - now_time).total_seconds() // 60)
                results.append({
                    "Ligne": route_info.get('route_short_name', route_id),
                    "Nom de la ligne": route_info.get('route_long_name', ''),
                    "Prochain passage": dep.strftime("%H:%M"),
                    "Dans (minutes)": mins_away
                })

        if results:
            st.subheader("Lignes et 2 prochains passages à ce stop (aujourd'hui uniquement)")
            st.dataframe(pd.DataFrame(results))
        else:
            st.info("Aucun passage à venir trouvé pour cet arrêt aujourd'hui.")arrêt