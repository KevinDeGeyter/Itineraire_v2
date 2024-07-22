import streamlit as st
import pandas as pd
import requests
import folium
from geopy.distance import geodesic
import subprocess
import asyncio

# Fonction pour appeler l'API OpenRouteService
def call_openrouteservice(coordinates, profile):
    url = f'https://api.openrouteservice.org/v2/directions/{profile}/geojson'
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': '5b3ce3597851110001cf6248a77c9061ac354f63b239407848bb9f8f',
        'Content-Type': 'application/json; charset=utf-8'
    }
    body = {
        "coordinates": coordinates
    }
    response = requests.post(url, json=body, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        try:
            error_message = response.json()['error']['message']
        except Exception as e:
            error_message = f"Erreur non spécifiée : {str(e)}"
            
        st.error(f"Erreur lors de l'appel à l'API OpenRouteService : {response.status_code}, {error_message}")
        return None

def load_data():
    df = pd.read_csv('clusters_data.csv')
    return df

# Fonction pour calculer la distance entre deux points (en kilomètres)
def calculate_distance(point1, point2):
    return geodesic(point1, point2).kilometers

# Définition des paramètres par défaut
default_address = "Paris, France"
default_poi_types = ["Monument"]
default_radius = 50

# Fonction pour récupérer la latitude et la longitude à partir de l'adresse via api-adresse.data.gouv.fr
async def geocode(address):
    url = 'https://api-adresse.data.gouv.fr/search/'
    params = {
        'q': address
    }
    
    response = await asyncio.to_thread(requests.get, url, params=params)
    
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
        st.error(f"Erreur lors de la récupération des coordonnées pour '{address}' : {response}")
        return None

# Fonction pour exécuter la requête et récupérer les résultats
def execute_query(latitude, longitude, poi_types, radius):
    poi_types_str = " ".join(poi_types)
    command = f"python3 Creation_Clusters.py --latitude {latitude} --longitude {longitude} --poi_types {poi_types_str} --radius {radius}"

    with st.spinner('Fetching data... Please wait.'):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

    if process.returncode == 0:
        st.success('Done!')
        return True
    else:
        st.success('Error')
        return False, stderr.decode('utf-8')


# Fonction principale de l'application Streamlit
def main():
    st.title("Projet Itineraire Data Engineer")

    st.header("Paramètres de la requête")

    # Entrée de l'adresse
    address = st.text_input("Entrez une adresse :", default_address)

    # Récupérer les coordonnées à partir de l'adresse
    coordinates = asyncio.run(geocode(address))
    if coordinates:
        latitude = coordinates['latitude']
        longitude = coordinates['longitude']
    else:
        latitude = None
        longitude = None

    radius = st.text_input("Choisissez une distance maximale :", default_radius)
    
    # Sélection des types de points d'intérêt (POI)
    extended_poi_types = [
        "Culture", "Religion", "Sport", "Loisir", "Divertissement", "Hebergement", 
        "Restauration", "Boisson", "Banque", "Hebergement", "Autre", "Plage", 
        "Mobilité réduite", "Moyen de locomotion", "Montagne", "Antiquité", 
        "Histoire", "Musée", "Détente", "Bar", "Commerce local", "Point de vue", 
        "Nature", "Camping", "Cours d'eau", "Service", "Monument", "Jeunesse", 
        "Apprentissage", "Marché", "Vélo", "Magasin", "Animaux", "Location", 
        "Parcours", "Santé", "Information", "Militaire", "Parking", 
        "Marche à pied", "POI", "Piscine"
    ]

    poi_types = st.multiselect("Types de points d'intérêt :", extended_poi_types, default=default_poi_types)

    # Bouton pour exécuter la requête
    if st.button("Exécuter la requête"):
        if coordinates:
            result = execute_query(latitude, longitude, poi_types, radius)
            
            if result == True:
                st.success("La requête a été exécutée avec succès !")
                # Affichage du résultat de la carte et du tableau CSV si disponible
                st.markdown("## Résultat de la carte")
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
                st.error(f"Erreur lors de l'exécution de la requête : {result}")
        else:
            st.warning("Adresse non valide. Veuillez entrer une adresse correcte.")

    st.header("Interrogation API")

    # Charger les données depuis le CSV
    df = load_data()

    with open("clusters_map.html", "r", encoding="utf-8") as file:
        html_code = file.read()
        st.components.v1.html(html_code, width=800, height=600)

    # Sélection de la couleur par l'utilisateur
    selected_color = st.selectbox('Choisir une couleur :', df['color'].unique())

    # Filtrer les données en fonction de la couleur sélectionnée
    filtered_data = df[df['color'] == selected_color]

    # Afficher les données filtrées
    st.write(f"Coordonnées pour la couleur '{selected_color}':")
    st.dataframe(filtered_data[['label_fr', 'latitude', 'longitude']])

    # Préparer les coordonnées pour l'appel API (assurez-vous de l'ordre correct : [longitude, latitude])
    coordinates = filtered_data[['longitude', 'latitude']].values.tolist()

    # Sélection du mode de transport
    transport_modes = ['driving-car', 'cycling-regular', 'foot-walking', 'driving-hgv']
    selected_transport_mode = st.selectbox('Choisir le mode de transport :', transport_modes)

    # Afficher la carte avec les marqueurs des coordonnées
    st.subheader('Carte des emplacements')
    map_center = [filtered_data['latitude'].mean(), filtered_data['longitude'].mean()]
    m = folium.Map(location=map_center, tiles='cartodbpositron', zoom_start=13)

    # Ajouter des marqueurs pour chaque point
    for index, row in filtered_data.iterrows():
        popup_text = f"{row['label_fr']} (ligne {index + 1})"
        folium.Marker([row['latitude'], row['longitude']], popup=popup_text).add_to(m)

    # Tracer l'itinéraire avec OpenRouteService
    if st.button('Afficher l\'itinéraire'):
        st.write('Envoi de la requête à OpenRouteService...')
        response = call_openrouteservice(coordinates, selected_transport_mode)

        if response:
            # Vérifier si des routes ont été trouvées dans la réponse
            if 'features' in response and len(response['features']) > 0:
                # Récupérer les coordonnées de l'itinéraire
                route_coordinates = []
                for coord in response['features'][0]['geometry']['coordinates']:
                    route_coordinates.append(list(reversed(coord)))
                
                # Ajouter la ligne de l'itinéraire à la carte
                folium.PolyLine(locations=route_coordinates, color='blue', weight=5).add_to(m)

                # Calculer et afficher les distances entre chaque paire de destinations
                st.subheader('Distances entre les destinations (en kilomètres)')
                distances = []
                for i in range(len(coordinates) - 1):
                    coord1 = tuple(coordinates[i])
                    coord2 = tuple(coordinates[i + 1])
                    distance = calculate_distance(coord1, coord2)
                    distances.append({
                        'De': filtered_data.iloc[i]['label_fr'],
                        'À': filtered_data.iloc[i + 1]['label_fr'],
                        'Distance (km)': distance
                    })
                
                st.dataframe(pd.DataFrame(distances))

                # Convertir la carte Folium en HTML
                m.save('map.html')
                
                # Afficher la carte dans Streamlit à l'aide de l'iframe
                with open('map.html', 'r', encoding='utf-8') as f:
                    html_map = f.read()
                    st.components.v1.html(html_map, width=800, height=600)
            else:
                st.warning("Aucun itinéraire trouvé.")
        else:
            st.error("Erreur lors de la récupération de l'itinéraire.")

if __name__ == "__main__":
    main()
