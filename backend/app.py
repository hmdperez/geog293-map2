from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from psycopg_pool import ConnectionPool
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

    conninfo = (
        f"host={os.getenv('DB_HOST')} "
        f"port={os.getenv('DB_PORT')} "
        f"dbname={os.getenv('DB_NAME')} "
        f"user={os.getenv('DB_USER')} "
        f"password={os.getenv('DB_PASS')}"
    )
    db_pool = ConnectionPool(conninfo=conninfo, min_size=1, max_size=10)
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
        with conn_pool.connection() as conn:
            with conn.cursor() as cur:
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve the frontend only when index.html exists in the deployed filesystem.
frontend_dir = Path(__file__).resolve().parent.parent
if (frontend_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")
else:
    @app.get("/")
    def root():
        return {"status": "ok", "message": "API is running. Open /docs or /data."}
