import os
from fastapi import APIRouter, Request, Body, status, HTTPException
import asyncio
import requests
import logging
import json
# from geopy.distance import geodesic

# logger = logging.getLogger('uvicorn.error')
# logger.setLevel(logging.DEBUG)

routerDataNeo4j = APIRouter()

# Configurer le format de journalisation
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Créer un logger
logger = logging.getLogger(__name__)


@routerDataNeo4j.get("/", response_description="Data Neo4j")
async def hello():
    return {"data": "Hello Data Neo4j"}


@routerDataNeo4j.get("/cluster_poi/{min_poi_count}/{max_clusters}/{max_pois_per_cluster}", response_description="Data Neo4j")
async def get_clusters_poi_data(
        min_poi_count: int = 6,
        max_clusters: int = 10,
        max_pois_per_cluster: int = 10,
        ):
    # await asyncio.sleep(5)
    # received_data = {"result": data}
    logger.debug("create_graph %s", min_poi_count)

    return {"status": "OK", "data": "data"}

@routerDataNeo4j.post("/graph", response_description="Data Neo4j")
async def create_graph_neo4j(data: dict = Body(...)):
    # await asyncio.sleep(5)
    # received_data = {"result": data}
    logger.debug("create_graph %s", json.dumps(data, indent=4))

    return {"status": "OK", "data": data}
