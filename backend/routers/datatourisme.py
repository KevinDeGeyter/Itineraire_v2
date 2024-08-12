import os
from fastapi import APIRouter, Request, Body, status, HTTPException
import asyncio
import requests
import logging
import json
# from geopy.distance import geodesic

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


@routerDataTourisme.post("/poi", response_description="Data Tourisme")
async def create_poi(data: dict = Body(...)):
    # await asyncio.sleep(5)
    # received_data = {"result": data}
    logger.debug("create_poi %s", json.dumps(data, indent=4))

    return {"status": "OK", "data": data}
