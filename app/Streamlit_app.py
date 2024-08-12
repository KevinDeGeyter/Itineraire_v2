import streamlit as st
import pandas as pd
import requests
import subprocess
import folium
import os
import streamlit.components.v1 as components
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
# from ortools.constraint_solver import pywrapcp
import time

# Fonction pour charger les données
def load_data():
    try:
        df = pd.read_csv('clusters_data.csv')
        return df
    except FileNotFoundError:
        st.error("Le fichier 'clusters_data.csv' est introuvable.")
        return pd.DataFrame()  # DF Vide en cas d'erreur


def execute_query(latitude, longitude, poi_types, radius):
    poi_types_str = " ".join(poi_types)
    command = f"python3 Creation_Clusters.py --latitude {latitude} --longitude {longitude} --poi_types {poi_types_str} --radius {radius}"

    with st.spinner('Création des clusters...'):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

    if process.returncode == 0:
        st.success('Done!')
        return True
    else:
        st.error(f"Erreur lors de l'exécution de la requête : {stderr.decode('utf-8')}")
        return False


# Fonction pour exécuter la requête de géocodage
def geocode_sync(address):
    url = 'https://api-adresse.data.gouv.fr/search/'
    params = {
        'q': address
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if len(data['features']) > 0:
                return {
                    'latitude': float(data['features'][0]['geometry']['coordinates'][1]),
                    'longitude': float(data['features'][0]['geometry']['coordinates'][0])
                }
            else:
                return None
        else:
            st.error(f"Erreur lors de la récupération des coordonnées pour '{address}' : {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Erreur lors de la requête de géocodage : {str(e)}")
        return None


# Fonction pour résoudre le problème du voyageur de commerce
def solve_tsp(distance_matrix):
    # Instantiate the data problem.
    data = {}
    data['distance_matrix'] = distance_matrix
    data['num_vehicles'] = 1
    data['depot'] = 0

    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(data['distance_matrix'][from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))
        return route
    else:
        st.error("Aucune solution trouvée.")
        return None


def generate_map(route, coordinates):
    # Crée une carte centrée sur le premier point
    m = folium.Map(location=[coordinates[0][0], coordinates[0][1]], zoom_start=13)

    # Ajouter des marqueurs pour chaque point
    for i, (lat, lon) in enumerate(coordinates):
        folium.Marker([lat, lon], popup=f"Étape {i + 1}").add_to(m)

    # Ajouter des lignes pour l'itinéraire
    for i in range(len(route) - 1):
        start = coordinates[route[i]]
        end = coordinates[route[1 + i]]
        folium.PolyLine([(start[0], start[1]), (end[0], end[1])], color="blue", weight=2.5, opacity=1).add_to(m)

    return m


# Fonction pour tracer l'itinéraire avec OpenRouteService
def get_ors_route(coordinates, mode):
    API_KEY = os.getenv('OPENROUTE_API_KEY')
    ORS_URL = 'https://api.openrouteservice.org/v2/directions'

    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8'
    }

    # Map mode to OpenRouteService endpoint
    ors_mode_map = {
        'à pied': 'foot-walking',
        'voiture': 'driving-car',
        'vélo': 'cycling-regular'
    }
    ors_mode = ors_mode_map.get(mode, 'driving-car')

    url = f'{ORS_URL}/{ors_mode}/gpx'
    payload = {
        'coordinates': coordinates
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            gpx_data = response.text
            return gpx_data
        else:
            st.error(f"Erreur lors de la récupération de l'itinéraire : {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Erreur lors de la requête OpenRouteService : {str(e)}")
        return None


def get_route_from_openrouteservice(coordinates, mode):
    API_KEY = os.getenv('OPENROUTE_API_KEY')
    ORS_URL = 'https://api.openrouteservice.org/v2/directions'

    modes = {
        "driving-car": "driving-car",
        "cycling-regular": "cycling-regular",
        "foot-walking": "foot-walking"
    }

    if mode not in modes:
        st.error("Mode de transport non valide.")
        return None

    url = f'{ORS_URL}/{modes[mode]}/geojson'
    headers = {
        'Authorization': API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }
    body = {
        'coordinates': coordinates
    }

    try:
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            st.error(f"Erreur lors de la récupération de l'itinéraire : {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Erreur lors de la requête de l'itinéraire : {str(e)}")
        return None


def main():
    st.title("Projet Itinéraire Data Engineer")

    st.header("Paramètres de la requête")
    address = st.text_input("Entrez une adresse :", "Paris, France")

    coordinates = geocode_sync(address)
    if coordinates:
        latitude = coordinates['latitude']
        longitude = coordinates['longitude']
    else:
        latitude = None
        longitude = None

    radius = st.text_input("Choisissez une distance maximale :", "50")
    poi_types = st.multiselect("Types de points d'intérêt :", [
        "Culture", "Religion", "Sport", "Loisir", "Divertissement", "Hebergement",
        "Restauration", "Boisson", "Banque", "Hebergement", "Autre", "Plage",
        "Mobilité réduite", "Moyen de locomotion", "Montagne", "Antiquité",
        "Histoire", "Musée", "Détente", "Bar", "Commerce local", "Point de vue",
        "Nature", "Camping", "Cours d'eau", "Service", "Monument", "Jeunesse",
        "Apprentissage", "Marché", "Vélo", "Magasin", "Animaux", "Location",
        "Parcours", "Santé", "Information", "Militaire", "Parking",
        "Marche à pied", "POI", "Piscine"],
                               default=["Monument"])

    # Afficher une carte initiale si des coordonnées sont disponibles
    if coordinates:
        st.markdown("## Carte initiale")
        m = folium.Map(location=[latitude, longitude], zoom_start=13)
        folium.Marker([latitude, longitude], popup="Adresse").add_to(m)
        st.components.v1.html(m._repr_html_(), width=800, height=600)

    if st.button("Créer clusters de points d'interet"):
        if coordinates:
            result = execute_query(latitude, longitude, poi_types, radius)
            if result:
                st.success("La requête a été exécutée avec succès !")
                st.markdown("## Résultat de la carte des clusters")
                with open("clusters_map.html", "r", encoding="utf-8") as file:
                    html_code = file.read()
                    st.components.v1.html(html_code, width=800, height=600)

                st.markdown("## Données des établissements")
                try:
                    df = pd.read_csv("clusters_data.csv")
                    st.dataframe(df)
                except ValueError as e:
                    st.error(str(e))
                except FileNotFoundError:
                    st.error("Le fichier csv est introuvable.")
            else:
                st.error("Erreur lors de l'exécution de la requête.")
        else:
            st.warning("Adresse non valide. Veuillez entrer une adresse correcte.")

    st.header("Calculer l'itinéraire le plus court")

    df = load_data()
    if df.empty:
        return

    selected_color = st.selectbox('Choisir une couleur :', df['color'].unique(), key='selectbox_1')
    filtered_data = df[df['color'] == selected_color]

    st.write(f"Coordonnées pour la couleur '{selected_color}':")
    st.dataframe(filtered_data[['label_fr', 'latitude', 'longitude']])

    coordinates = filtered_data[['latitude', 'longitude']].values.tolist()

    # Afficher une carte avec les coordonnées sélectionnées
    if len(coordinates) > 1:
        st.markdown("## Carte des points sélectionnés")
        m = folium.Map(location=[coordinates[0][0], coordinates[0][1]], zoom_start=13)
        for i, (lat, lon) in enumerate(coordinates):
            folium.Marker([lat, lon], popup=f"Étape {i + 1}").add_to(m)
        st.components.v1.html(m._repr_html_(), width=800, height=600)

    if st.button("Calculer l'itinéraire le plus court"):
        if len(coordinates) > 1:
            # Calculer la matrice des distances (ici, juste une distance euclidienne simplifiée)
            num_points = len(coordinates)
            distance_matrix = [[0] * num_points for _ in range(num_points)]
            for i in range(num_points):
                for j in range(num_points):
                    if i != j:
                        coord1 = coordinates[i]
                        coord2 = coordinates[j]
                        distance_matrix[i][j] = ((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2) ** 0.5

            # Résoudre le problème TSP
            route = solve_tsp(distance_matrix)

            if route:
                st.success("L'itinéraire le plus court a été trouvé !")
                # Générer et afficher la carte de l'itinéraire le plus court
                m = generate_map(route, coordinates)
                st.components.v1.html(m._repr_html_(), width=800, height=600)
            else:
                st.error("Impossible de trouver l'itinéraire le plus court.")
        else:
            st.warning("Il doit y avoir au moins deux points pour calculer l'itinéraire le plus court.")

    st.header("Tracer l'itinéraire avec OpenRouteService")

    coordinates = filtered_data[['longitude', 'latitude']].values.tolist()  # Changer l'ordre pour OpenRouteService

    transport_mode = st.selectbox("Choisissez un mode de transport :",
                                  ["driving-car", "cycling-regular", "foot-walking"])

    if st.button("Tracer le chemin sur la route"):
        if len(coordinates) > 1:
            # Tracer l'itinéraire via OpenRouteService
            openrouteservice_data = get_route_from_openrouteservice(coordinates, transport_mode)
            if openrouteservice_data:
                st.success("L'itinéraire a été tracé avec OpenRouteService !")
                # Générer et afficher la carte avec OpenRouteService
                m = folium.Map(location=[coordinates[0][1], coordinates[0][0]], zoom_start=13)

                # Ajouter des marqueurs pour chaque point
                for i, (lon, lat) in enumerate(coordinates):
                    folium.Marker([lat, lon], popup=f"Étape {i + 1}").add_to(m)

                # Ajouter l'itinéraire
                if 'features' in openrouteservice_data and len(openrouteservice_data['features']) > 0:
                    route_coords = openrouteservice_data['features'][0]['geometry']['coordinates']
                    folium.PolyLine([(coord[1], coord[0]) for coord in route_coords], color="blue", weight=2.5,
                                    opacity=1).add_to(m)

                st.components.v1.html(m._repr_html_(), width=800, height=600)
            else:
                st.error("Impossible de tracer l'itinéraire avec OpenRouteService.")
        else:
            st.warning("Il doit y avoir au moins deux points pour tracer un itinéraire.")


if __name__ == "__main__":
    main()
