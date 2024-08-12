import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from routers.datatourisme import routerDataTourisme as dataTourisme_router
from routers.neo4j import routerDataNeo4j as dataNeo4j_router

# define origins
origins = ["*"]

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

# instantiate the app
app = FastAPI()

# add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.debug('This is a debug message from startup_event')

@app.on_event("shutdown")
async def shutdown_event():
    logger.debug('This is a debug message from shutdown_event')

app.include_router(dataTourisme_router, prefix="/data", tags=["DataTourisme"])
app.include_router(dataNeo4j_router, prefix="/neo4j", tags=["Neo4j"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
