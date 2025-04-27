import streamlit as st
import pandas as pd
import zipfile
from datetime import timedelta

def parse_gtfs_time(t):
    """Analyse le temps GTFS au format HH:MM:SS en autorisant les heures > 24"""
    h, m, s = map(int, t.split(":"))
    return timedelta(hours=h, minutes=m, seconds=s)

st.title("Calculateur de Durée de Trajet et d'Intervalle entre Arrêts GTFS")

uploaded_file = st.file_uploader("Téléverser un fichier GTFS ZIP", type="zip")
trip_id = st.text_input("Entrez l'ID du trajet")

if uploaded_file:
    with zipfile.ZipFile(uploaded_file) as z:
        with z.open("stop_times.txt") as f:
            stop_times = pd.read_csv(f, dtype={'trip_id': str})
        with z.open("trips.txt") as f:
            trips = pd.read_csv(f, dtype={'trip_id': str})

    st.subheader("Table des trajets (trips.txt) :")
    st.dataframe(trips, use_container_width=True)

    if trip_id:
    # Filtrage par trip_id et tri par stop_sequence
        trip_times = stop_times[stop_times['trip_id'] == trip_id].sort_values("stop_sequence")

        if trip_times.empty:
            st.error("Aucun horaire d'arrêt trouvé pour cet ID de trajet.")
        else:
            # Conversion des heures en timedelta
            trip_times['arrival_td'] = trip_times['arrival_time'].apply(parse_gtfs_time)
            trip_times['departure_td'] = trip_times['departure_time'].apply(parse_gtfs_time)

            # Calcul de la durée totale
            premier_depart = trip_times['departure_td'].iloc[0]
            derniere_arrivee = trip_times['arrival_td'].iloc[-1]
            duree = (derniere_arrivee - premier_depart).total_seconds() / 60  # en minutes

            # Calcul des intervalles entre arrêts
            intervalles = trip_times['arrival_td'].diff().dropna().dt.total_seconds() / 60

            if not intervalles.empty:
                moyenne = intervalles.mean()
                maximum = intervalles.max()
                minimum = intervalles.min()
            else:
                moyenne = maximum = minimum = 0

            st.write(f"**Statistiques du trajet `{trip_id}` :**")
            st.write(f"- Durée totale : **{duree:.1f} minutes**")
            st.write(f"- Temps moyen entre deux arrêts : **{moyenne:.1f} minutes**")
            st.write(f"- Temps maximum entre deux arrêts : **{maximum:.1f} minutes**")
            st.write(f"- Temps minimum entre deux arrêts : **{minimum:.1f} minutes**")

            st.subheader("Horaires des arrêts pour ce trajet")
            st.dataframe(trip_times, use_container_width=True)