import os
from fastapi import APIRouter, Request, Body, status, HTTPException
import requests
import logging

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

routerTripAdvisor = APIRouter()


@routerTripAdvisor.get("/", response_description="TripAdvisor")
async def hello():
    return {"data": "Hello TripAdvisor"}


@routerTripAdvisor.get("/hello", response_description="TripAdvisor")
async def hello_tripadvisor():
    return {"data": "Hello TripAdvisor again"}


@routerTripAdvisor.get("/comments/{entity}/{lat}/{lng}", response_description="TripAdvisor")
async def get_comments(
        request: Request,
        entity: str = "123455",
        lat: str = "48.866667",
        lng: str = "2.333333",
):
    logger.debug('This is a debug message from get_comments')

    logger.debug('==============Entity: %s', entity)
    logger.debug('==============Latitude: %s', lat)
    logger.debug('==============Longitude: %s', lng)

    # logger.debug('========= request: ' + request)

    # Exemple d'utilisation de la fonction
    nom_etablissement = entity  # "l'auberge du gros"
    latitude = lat  # 49.1135  # Latitude de l'établissement
    longitude = lng  # 6.3513  # Longitude de l'établissement

    etablissement_trouve = trouver_etablissement_sur_tripadvisor(nom_etablissement, latitude, longitude)

    if etablissement_trouve["status"] == "OK":
        logger.debug("Établissement trouvé sur TripAdvisor : %s", etablissement_trouve["data"].get('location_id'))
        logger.debug("Nom de l'établissement trouvé sur TripAdvisor : %s", etablissement_trouve["data"].get('name'))

        # Utilisation de l'ID de l'établissement pour récupérer des avis
        location_id = etablissement_trouve["data"].get('location_id')

        avis_etablissement = recuperer_avis_etablissement(location_id)

        if avis_etablissement["status"] == "OK":
            logger.debug("Note de l'établissement : %s", avis_etablissement["data"])
            response = {
                "status": "OK",
                "data": avis_etablissement["data"],
            }
        else:
            logger.debug("Aucun avis trouvé sur TripAdvisor pour cet établissement.")
            response = {
                "status": "None",
                "data": "Aucun avis trouvé sur TripAdvisor pour cet établissement.",
            }

    else:
        logger.debug("Aucun établissement trouvé sur TripAdvisor.")
        response = {
            "status": "None",
            "data": "Aucun avis trouvé sur TripAdvisor pour cet établissement.",
        }

    return response


def trouver_etablissement_sur_tripadvisor(nom_etablissement, latitude, longitude):
    # Clé API de TripAdvisor
    API_KEY = os.getenv('TRIPADVISOR_API_KEY')

    # URL de l'API de TripAdvisor pour la recherche d'établissements
    search_url = "https://api.content.tripadvisor.com/api/v1/location/search"

    # Paramètres de la requête
    params = {
        "key": API_KEY,
        "searchQuery": nom_etablissement,
        "latLong": "{},{}".format(latitude, longitude),
        "radius": 1,
        "language": "en"
    }

    try:
        # Envoie de la requête à l'API de TripAdvisor
        response = requests.get(search_url, params=params)

        # Vérifie si la requête a réussi
        if response.status_code == 200:
            data = response.json()
            # Récupère le premier établissement trouvé
            etablissement = data.get('data', [])
            if etablissement:
                return {"status": "OK", "data": etablissement[0]}
            else:
                logger.debug("Aucun établissement trouvé sur TripAdvisor.")
                return {"status": "None", "data": None}
        else:
            # Affiche un message d'erreur si la requête a échoué
            logger.debug("Erreur lors de la requête à l'API TripAdvisor. Statut : %s", response.status_code)
            return {"status": "ERROR", "data": response.status_code}

    except Exception as ex:
        # Affiche un message d'erreur en cas d'exception
        logger.debug("Erreur : %s", ex)
        return {"status": "ERROR", "data": ex}


def recuperer_avis_etablissement(location_id):
    # Clé API de TripAdvisor
    API_KEY = os.getenv('TRIPADVISOR_API_KEY')

    # URL de l'API de TripAdvisor pour récupérer les avis de l'établissement
    reviews_url = f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/reviews"

    # Paramètres de la requête pour récupérer les avis
    params = {
        "key": API_KEY,
        "language": "en"
    }

    try:
        # Envoie de la requête à l'API de TripAdvisor pour récupérer les avis
        response = requests.get(reviews_url, params=params)

        # Vérifie si la requête a réussi
        if response.status_code == 200:
            data = response.json()
            rating = data['data'][0]['rating']
            return {"status": "OK", "data": rating}
        else:
            # Affiche un message d'erreur si la requête a échoué
            logger.debug("Erreur lors de la requête pour récupérer les avis. Statut : %s", response.status_code)
            return {"status": "ERROR", "data": response.status_code}

    except Exception as ex:
        # Affiche un message d'erreur en cas d'exception
        logger.debug("Erreur lors de la récupération des avis de l'établissement : %s", ex)
        return {"status": "ERROR", "data": ex}
