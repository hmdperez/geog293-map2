from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from psycopg2 import pool
import os
from pathlib import Path
from dotenv import load_dotenv

# Load local env file only when it exists (Railway uses injected env vars).
env_file = Path(__file__).resolve().parent / "db.env"
if env_file.exists():
    load_dotenv(env_file)

db_pool = None


def get_db_pool():
    global db_pool
    if db_pool is not None:
        return db_pool

    required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS"]
    missing = [name for name in required_vars if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing database environment variables: " + ", ".join(missing)
        )

    db_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
    )
    return db_pool

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
        conn_pool = get_db_pool()
        conn = conn_pool.getconn()
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
            conn_pool.putconn(conn)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files (HTML, CSS, JS) from the parent directory
app.mount("/", StaticFiles(directory="../", html=True), name="static")
