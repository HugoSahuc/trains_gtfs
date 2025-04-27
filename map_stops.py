import streamlit as st
import pandas as pd
import zipfile
from map import plot_route_map

st.title("Visualiseur de lignes GTFS")
uploaded_file = st.file_uploader("Télécharger un fichier GTFS (ZIP)", type="zip")
route_name = st.text_input("Entrez le nom exact de la ligne")

if uploaded_file:
    with zipfile.ZipFile(uploaded_file) as z:
        # Charger les fichiers GTFS
        with z.open("stop_times.txt") as f:
            stop_times_df = pd.read_csv(f, dtype={'stop_id': str, 'trip_id': str})

        with z.open("stops.txt") as f:
            stops_df = pd.read_csv(f, dtype={'stop_id': str})

        with z.open("trips.txt") as f:
            trips_df = pd.read_csv(f, dtype={'trip_id': str, 'route_id': str})

        with z.open("routes.txt") as f:
            routes_df = pd.read_csv(f, dtype={'route_id': str})

    trip_counts = trips_df.groupby('route_id').size().reset_index(name='num_trips')
    routes_with_trips = routes_df.merge(trip_counts, on='route_id', how='left').fillna(0)
    st.subheader("Lignes disponibles et nombre de trajets :")
    st.dataframe(routes_with_trips[['route_id', 'route_short_name', 'route_long_name', 'num_trips']])

    if route_name:
        route_filter = (
            (routes_df['route_short_name'] == route_name) |
            (routes_df['route_long_name'] == route_name)
        )

        if not routes_df[route_filter].empty:
            # Afficher des informations supplémentaires sur la ligne
            st.write("**Détails de la ligne :**")
            st.dataframe(routes_df[route_filter].T, use_container_width=True)
            route_id = routes_df[route_filter].iloc[0]['route_id']

            # Obtenir les trajets pour cette ligne
            route_trips = trips_df[trips_df['route_id'] == route_id]
            st.info(f"La ligne '{route_name}' possède {len(route_trips)} trajets.")

            # Obtenir les horaires d'arrêt pour ces trajets
            route_stop_times = stop_times_df[
                stop_times_df['trip_id'].isin(route_trips['trip_id'])
            ].drop_duplicates(subset=['stop_id'])
            
            st.subheader("Horaires de passage pour la ligne sélectionnée")
            st.dataframe(route_stop_times, use_container_width=True)

            # Obtenir les arrêts uniques
            stop_times_df['stop_id'] = stop_times_df['stop_id'].astype(str).str.strip()
            stops_df['stop_id'] = stops_df['stop_id'].astype(str).str.strip()
            route_stops = stops_df[
                stops_df['stop_id'].isin(route_stop_times['stop_id'])
            ]
            
            st.subheader("Arrêts pour la ligne sélectionnée")
            st.dataframe(route_stops, use_container_width=True)

            # Afficher les résultats
            st.subheader(f"La ligne {route_name} possède {len(route_stops)} arrêts uniques")
            if not route_stops.empty:
                plot_route_map(route_stop_times, stops_df)
                #st.map(route_stops, latitude="stop_lat", longitude="stop_lon")
            else:
                st.warning("Aucun arrêt trouvé pour cette ligne. Vérifiez que le nom de la ligne est correct et que des trajets/arrêts existent.")

        else:
            st.error(f"Aucune ligne trouvée avec le nom : {route_name}")
