import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
from neo4j import GraphDatabase
import pandas as pd

# Connexion à la base de données Neo4j
uri = "bolt://188.166.105.53:7687"
username = "neo4j"
password = "od1235Azerty%"

driver = GraphDatabase.driver(uri, auth=(username, password))

def get_pois_and_clusters():
    query = """
    MATCH (poi:POI)-[:BELONGS_TO]->(cluster:Cluster)
    RETURN poi.label_fr AS label, poi.latitude AS latitude, poi.longitude AS longitude, poi.poi_type AS type, cluster.name AS cluster_name
    """
    with driver.session() as session:
        result = session.run(query)
        data = pd.DataFrame([record.data() for record in result])
    return data

# Récupérer les données
# data = get_pois_and_clusters()

# Nettoyer les données
# data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
# data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
# data = data.dropna(subset=['latitude', 'longitude'])

# Créer l'application Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='graph'),
])

@app.callback(
    Output('graph', 'figure'),
    [Input('graph', 'id')]
)
def update_graph(_):
    # Récupérer les données
    data = get_pois_and_clusters()

    # Nettoyer les données
    data['latitude'] = pd.to_numeric(data['latitude'], errors='coerce')
    data['longitude'] = pd.to_numeric(data['longitude'], errors='coerce')
    data = data.dropna(subset=['latitude', 'longitude'])

    fig = px.scatter_mapbox(
        data,
        lat='latitude',
        lon='longitude',
        color='cluster_name',
        hover_name='label',
        hover_data={'type': True, 'cluster_name': False},
        zoom=10,
        height=600
    )
    fig.update_layout(mapbox_style="open-street-map")
    return fig

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050,debug=True)
