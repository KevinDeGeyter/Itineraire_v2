import csv
import folium
from neo4j import GraphDatabase

# Connexion à la base de données Neo4j
uri = "bolt://188.166.105.53:7687"
username = "neo4j"
password = "od1235Azerty%"
driver = GraphDatabase.driver(uri, auth=(username, password))

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
            max_clusters=max_clusters,
            max_pois_per_cluster=max_pois_per_cluster
        )
        for record in result:
            cluster_name = record["cluster_name"]
            poi_data = record["poi_data"][:max_pois_per_cluster]  # Limiter les POI par cluster
            clusters_data[cluster_name] = poi_data
    return clusters_data

# Récupérer les données des POIs pour les clusters avec au moins 6 POI et au maximum 10 clusters
clusters_data = get_clusters_poi_data(min_poi_count=6, max_clusters=10, max_pois_per_cluster=10)

# Créer la carte Google Maps
map = folium.Map(location=[0, 0], zoom_start=2)

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
