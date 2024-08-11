import argparse
import csv
import subprocess
from geopy.distance import geodesic
from neo4j import GraphDatabase
from sklearn.cluster import KMeans
import folium
import psycopg2

# Définition des arguments en ligne de commande
parser = argparse.ArgumentParser(description='Script pour créer des clusters de Points d_intérêt en fonction de la localisation et du type d_activité.')
parser.add_argument('--latitude', type=float, required=True, help='Latitude du point de référence')
parser.add_argument('--longitude', type=float, required=True, help='Longitude du point de référence')
parser.add_argument('--poi_types', nargs='+', required=True, help='Types d_activité')
parser.add_argument('--radius', type=float, required=True, help='Rayon en kilomètres pour filtrer les points d_intérêt')
args = parser.parse_args()

# Fonction pour filtrer les points d'intérêt dans un rayon donné autour d'une position
def filter_pois(position, pois, radius_km):
    list_pois = []
    for poi in pois:
        poi_latitude, poi_longitude = float(poi[1]), float(poi[2])
        if -90 <= poi_latitude <= 90 and -180 <= poi_longitude <= 180:
            poi_position = (poi_latitude, poi_longitude)
            if geodesic(position, poi_position).kilometers <= radius_km:
                list_pois.append(poi)
        else:
            print("Coordonnées incorrectes")
    return list_pois

# Connexion à la base de données PostgreSQL
conn = psycopg2.connect(
    host="188.166.105.53",
    port="65001",
    database="postgres",
    user="postgres",
    password="LearnPostgreSQL"
)
cursor = conn.cursor()

# Requête SQL pour récupérer les points d'intérêt correspondant aux types spécifiés
poi_types_condition = " OR ".join([f"tp.type = '{poi_type}'" for poi_type in args.poi_types])
sql_query = (
    "SELECT dt.label_fr, dt.latitude, dt.longitude, tp.type "
    "FROM datatourisme dt "
    "JOIN liaison_datatourisme_types_de_poi ldtp ON dt.id = ldtp.id_datatourisme "
    "JOIN types_de_poi tp ON ldtp.id_type_de_poi = tp.id "
    f"WHERE {poi_types_condition} "
    "GROUP BY dt.label_fr, dt.latitude, dt.longitude, tp.type"
)

# Exécution de la requête SQL
cursor.execute(sql_query)
rows = cursor.fetchall()
conn.commit()

# Position de référence pour le filtrage des POIs
reference_position = (args.latitude, args.longitude)

# Filtrer les points d'intérêt dans le rayon spécifié autour de la position de référence
list_pois = filter_pois(reference_position, rows, args.radius)

# Utilisation de KMeans pour regrouper les POIs en clusters
X = [(row[1], row[2]) for row in list_pois]
kmeans = KMeans(n_clusters=10, n_init=10)
kmeans.fit(X)
clusters = kmeans.labels_

# Connexion à la base de données Neo4j
uri = "bolt://188.166.105.53:7687"
username = "neo4j"
password = "od1235Azerty%"
driver = GraphDatabase.driver(uri, auth=(username, password))

# Fonction pour créer les clusters et les POIs dans Neo4j
def create_graph(tx):
    # Supprimer tous les nœuds et relations existants dans la base Neo4j
    tx.run("MATCH (n) DETACH DELETE n")

    # Création des clusters
    for i in range(max(clusters) + 1):
        cluster_name = f"Cluster_{i}"
        tx.run("CREATE (:Cluster {name: $name})", name=cluster_name)

    # Création des POIs et des relations avec les clusters
    for i, row in enumerate(list_pois):
        label_fr, latitude, longitude, poi_type = row
        cluster_name = f"Cluster_{clusters[i]}"
        tx.run(
            "CREATE (:POI {label_fr: $label_fr, latitude: $latitude, longitude: $longitude, poi_type: $poi_type})",
            label_fr=label_fr, latitude=latitude, longitude=longitude, poi_type=poi_type
        )
        tx.run(
            "MATCH (poi:POI {label_fr: $label_fr}), (cluster:Cluster {name: $cluster_name}) "
            "CREATE (poi)-[:BELONGS_TO]->(cluster)",
            label_fr=label_fr, cluster_name=cluster_name
        )

# Création de la session Neo4j et exécution de la transaction
with driver.session() as session:
    session.write_transaction(create_graph)

# Fermeture du curseur et de la connexion à la base de données PostgreSQL
cursor.close()
conn.close()

# Fonction pour récupérer les coordonnées GPS et les labels des POIs de chaque cluster depuis Neo4j
def get_clusters_poi_data(min_poi_count=6, max_clusters=10, max_pois_per_cluster=10):
    clusters_data = {}
    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Cluster)<-[:BELONGS_TO]-(p:POI)
            WITH c, p
            ORDER BY c.name, p.label_fr
            WHERE size([(c)-[:BELONGS_TO]-(p2) | p2]) >= $min_poi_count
            RETURN c.name AS cluster_name, collect([p.latitude, p.longitude, p.label_fr]) AS poi_data
            LIMIT $max_clusters
            """,
            min_poi_count=min_poi_count,
            max_clusters=max_clusters
        )
        for record in result:
            cluster_name = record["cluster_name"]
            poi_data = record["poi_data"][:max_pois_per_cluster]  # Limiter les POI par cluster
            clusters_data[cluster_name] = poi_data
    return clusters_data

# Récupérer les données des POIs pour les clusters avec au moins 6 POI et au maximum 10 clusters
clusters_data = get_clusters_poi_data(min_poi_count=6, max_clusters=10, max_pois_per_cluster=10)

# Créer la carte
map = folium.Map(location=[args.latitude, args.longitude], zoom_start=12)

# Définir les couleurs pour les marqueurs de chaque cluster
colors = ['red', 'blue', 'green', 'purple', 'orange', 'lightgreen', 'pink', 'white', 'gray', 'black']

# Créer une liste pour stocker les données à écrire dans le CSV
csv_data = []

# Ajouter un marqueur pour chaque POI de chaque cluster avec une couleur différente
for i, (cluster_name, poi_data) in enumerate(clusters_data.items()):
    color = colors[i % len(colors)]  # Utilisation d'une couleur cyclique pour chaque cluster
    for poi_coordinate in poi_data:
        latitude, longitude, label_fr = poi_coordinate
        # Ajouter un marqueur avec une info-bulle (tooltip) pour afficher le label_fr du POI
        folium.Marker(
            location=[latitude, longitude],
            icon=folium.Icon(color=color),
            tooltip=label_fr
        ).add_to(map)

        # Ajouter les données au CSV
        csv_data.append({
            'color': color,
            'label_fr': label_fr,
            'latitude': latitude,
            'longitude': longitude
        })

# Sauvegarder la carte dans un fichier HTML
map_filename = 'clusters_map.html'
map.save(map_filename)
print(f"La carte '{map_filename}' a été créée avec succès.")

# Écrire les données dans un fichier CSV
csv_filename = 'clusters_data.csv'
csv_fields = ['color', 'label_fr', 'latitude', 'longitude']

with open(csv_filename, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
    writer.writeheader()
    for data in csv_data:
        writer.writerow(data)

print(f"Le fichier CSV '{csv_filename}' a été créé avec succès.")
