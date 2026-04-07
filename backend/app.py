from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from psycopg2 import pool
import os
from dotenv import load_dotenv

load_dotenv("db.env")

# Create a connection pool globally
db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS")
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/data")
def get_data():
    try:
        conn = db_pool.getconn()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    place, country, title, period, description,
                    safety, inclusiveness, women_spaces,
                    ST_X(geom) AS lon,
                    ST_Y(geom) AS lat,
                    id
                FROM places
            """)
            rows = cur.fetchall()
            cur.close()

            features = []
            for row in rows:
                place, country, title, period, description, safety, inclusiveness, women_spaces, lon, lat, id = row
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "id": id,
                        "place": place,
                        "country": country,
                        "title": title,
                        "period": period,
                        "description": description,
                        "safety": safety,
                        "inclusiveness": inclusiveness,
                        "women_spaces": women_spaces
                    }
                })

            return {
                "type": "FeatureCollection",
                "features": features
            }

        finally:
            db_pool.putconn(conn)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files (HTML, CSS, JS) from the parent directory
app.mount("/", StaticFiles(directory="../", html=True), name="static")
