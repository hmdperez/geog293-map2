import geopandas as gpd
import pandas as pd
import fiona
from sqlalchemy import create_engine
import numpy as np
import os

# Configuration of the PostGreSQL Server
POSTGRES = {
    "host": "localhost",
    "port": "5432",
    # "dbname": "gis210_project",
    "user": "postgres",
    "password": "hdperez"
}

dbname = "gme210_project"

def get_pg_connection(dbname):
    """
    Connect to PostgreSQL database with a given dbname.
    """
    return f"postgresql://{POSTGRES['user']}:{POSTGRES['password']}@" \
           f"{POSTGRES['host']}:{POSTGRES['port']}/{dbname}"

def upload_csv_to_postgis(csv_path, pg_table_name, dbname):
    """
    Upload a CSV file to PostgreSQL/PostGIS.
    :param csv_path: Path to the CSV file.
    :param pg_table_name: Name of the target table in PostgreSQL.
    """
    # Load CSV
    df = pd.read_csv(csv_path)
    print(f"📦 Loaded CSV with {len(df)} records and {len(df.columns)} columns.")

    # Connect and upload to PostgreSQL
    engine = create_engine(get_pg_connection(dbname))
    df.to_sql(pg_table_name, engine, if_exists='replace', index=False)
    print(f"✅ Uploaded to PostgreSQL table '{pg_table_name}'")


def upload_gpkg(gpkg_path,layer_name, dbname):
    """
    Upload a GPKG file to PostgreSQL.
    :param gpkg_path: Input geopackage file for importing.
    :param layer_name: Layer name for newly uploaded geopackage.
    :return:
    """
    gdf = gpd.read_file(gpkg_path)
    engine = create_engine(get_pg_connection(dbname))
    gdf.to_postgis(layer_name, engine, if_exists="replace", index=False)
    print(f"✅ Uploaded {layer_name} to table!")


# Main
if __name__ == "__main__":
    print("📤 Starting upload to PostGIS...")
    # upload_points()
    # upload_raster()
    print("✅ Upload complete.")

