import os
from fastapi import APIRouter, Request, Body, status, HTTPException
import asyncio
import logging
import json
# from geopy.distance import geodesic
# from neo4j import GraphDatabase
# import psycopg2

# logger = logging.getLogger('uvicorn.error')
# logger.setLevel(logging.DEBUG)

routerNeo4j = APIRouter()

# Configurer le format de journalisation
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Créer un logger
logger = logging.getLogger(__name__)


@routerNeo4j.get("/", response_description="Data Tourisme")
async def hello():
    return {"data": "Hello Data Tourisme"}


@routerNeo4j.get("/clusters_poi", response_description="Data Tourisme")
async def get_clusters_poi_data(data: dict = Body(...)):
    await asyncio.sleep(5)
    received_data = {"result": data}
    logger.debug("create_graph %s", json.dumps(data, indent=4))

    return {"status": "OK", "data": data}

@routerNeo4j.post("/graph", response_description="Data Tourisme")
async def create_graph_neo4j(data: dict = Body(...)):
    await asyncio.sleep(5)
    received_data = {"result": data}
    logger.debug("create_graph %s", json.dumps(data, indent=4))

    return {"status": "OK", "data": data}
