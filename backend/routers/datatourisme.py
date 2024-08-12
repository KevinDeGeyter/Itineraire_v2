import os
from fastapi import APIRouter, Request, Body, status, HTTPException
import asyncio
import logging
import json
from geopy.distance import geodesic

# logger = logging.getLogger('uvicorn.error')
# logger.setLevel(logging.DEBUG)

routerDataTourisme = APIRouter()

# Configurer le format de journalisation
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Créer un logger
logger = logging.getLogger(__name__)


@routerDataTourisme.get("/", response_description="Data Tourisme")
async def hello():
    return {"data": "Hello Data Tourisme"}


@routerDataTourisme.post("/graph", response_description="Neo4j")
async def create_graph_neo4j(data: dict = Body(...)):
    # await asyncio.sleep(5)
    # received_data = {"result": data}
    logger.debug("create_graph %s", json.dumps(data, indent=4))

    return {"status": "OK", "data": data}
