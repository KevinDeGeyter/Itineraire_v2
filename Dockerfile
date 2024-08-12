FROM python:3.9

WORKDIR /app

RUN pip install --no-cache-dir \
    neo4j \
    scikit-learn \
    psycopg2-binary \
    geopy \
    streamlit \
    folium \
    openrouteservice \
    streamlit_folium \
    dash \
    plotly \
    asyncio \
    nest_asyncio \
    fastapi \
    bcrypt \
    beanie \
    email-validator \
    requests \
    httpx \
    Jinja2 \
    motor \
    passlib \
    pytest \
    python-multipart \
    python-dotenv \
    python-jose \
    sqlmodel \
    uvicorn

COPY app/Creation_Clusters.py .
COPY app/Streamlit_app.py .
# COPY app/dashboard_dash.py .
COPY app/clusters_data.csv .
COPY app/clusters_map.html .
COPY app/map.html .

RUN mkdir dash
COPY dash/dashboard_dash.py dash

RUN mkdir -p backend/routers
COPY backend/main.py backend
COPY backend/routers/__init__.py backend/routers
COPY backend/routers/tripadvisor.py backend/routers
COPY backend/routers/datatourisme.py backend/routers
COPY backend/routers/neo4j.py backend/routers


# EXPOSE 8501 8050
# Commande par défaut pour démarrer Streamlit (à ajuster selon votre besoin)
# CMD ["streamlit", "run", "Streamlit_app.py"]