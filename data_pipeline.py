"""
Taipei Day Trip - Data Pipeline Module
--------------------------------------
This script handles reading raw JSON data of Taipei attractions,
cleaning & transforming the data into structured DataFrames, and loading it into MySQL.
"""

import json
import logging
import os
import re
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def load_raw_data(file_path: str) -> Dict[str, Any]:
    """Reads JSON file containing raw attraction data."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    logger.info(f"Loading raw data from: {file_path}")
    with open(file_path, "r", encoding="utf-8") as file:
        raw_data = json.load(file)
    return raw_data


def extract_clean_urls(url_string: str) -> list:
    """Extracts valid image URLs ending with .jpg, .jpeg, or .png."""
    pattern = r'((?:https?://|/).*?(?:\.jpg|\.jpeg|\.png))'
    matches = re.findall(pattern, str(url_string), flags=re.IGNORECASE)
    return matches


def transform_data(raw_data: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transforms raw JSON data into two cleaned DataFrames:
    1. Attractions DataFrame (df_a)
    2. Attraction Images DataFrame (df_attraction_image)
    """
    logger.info("Transforming raw data...")
    if "list" not in raw_data:
        raise KeyError("Expected 'list' key in raw JSON data.")
    
    df = pd.DataFrame(raw_data["list"])

    # 1. Extract required columns
    cols_to_extract = ["_id", "name", "CAT", "description", "address", "direction", "MRT", "latitude", "longitude", "imgurls"]
    df_data = df.loc[:, cols_to_extract]

    # 2. Process Attractions DataFrame (df_a)
    df_a = df_data.iloc[:, :-1].copy()
    df_a.columns = ["id", "name", "category", "description", "address", "transport", "mrt", "lat", "lng"]
    
    # Remove spaces from address string
    df_a["address"] = df_a["address"].astype(str).str.replace(" ", "")

    # Convert lat and lng to float
    df_a["lat"] = pd.to_numeric(df_a["lat"], errors="coerce")
    df_a["lng"] = pd.to_numeric(df_a["lng"], errors="coerce")

    # Replace NaN with None for MySQL NULL compatibility
    df_a = df_a.replace({np.nan: None})

    # 3. Process Attraction Images DataFrame (df_attraction_image)
    df_ai = df_data.iloc[:, [0, -1]].copy()
    df_ai.columns = ["attraction_id", "image_url"]

    # Extract image URLs and explode
    df_ai["image_url"] = df_ai["image_url"].apply(extract_clean_urls)
    df_attraction_image = df_ai.explode("image_url", ignore_index=True)
    df_attraction_image = df_attraction_image.dropna(subset=["image_url"])
    df_attraction_image = df_attraction_image.replace({np.nan: None})

    logger.info(f"Cleaned {len(df_a)} attraction records and {len(df_attraction_image)} image records.")
    return df_a, df_attraction_image


def get_db_connection():
    """Establishes connection to MySQL database using environment variables."""
    load_dotenv()

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_name = os.getenv("DB_NAME")
    db_port = os.getenv("DB_PORT", "3306")

    if not all([db_user, db_password, db_host, db_name]):
        logger.warning("Some DB environment variables are missing in .env file.")

    logger.info(f"Connecting to MySQL database '{db_name}' at {db_host}:{db_port}...")
    con = mysql.connector.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        port=int(db_port),
        database=db_name
    )
    return con


def load_to_db(df_a: pd.DataFrame, df_attraction_image: pd.DataFrame, connection=None):
    """
    Inserts cleaned data into MySQL database tables:
    - attraction
    - attraction_image
    """
    close_conn = False
    if connection is None:
        connection = get_db_connection()
        close_conn = True

    # Format data into tuples for executemany
    data_a = [tuple(row) for row in df_a.values]
    data_ai = [tuple(row) for row in df_attraction_image.values]

    cursor = connection.cursor()
    try:
        logger.info("Executing batch insert into 'attraction' table...")
        sql_attraction = """
            INSERT INTO attraction (id, name, category, description, address, transport, mrt, lat, lng)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                category = VALUES(category),
                description = VALUES(description),
                address = VALUES(address),
                transport = VALUES(transport),
                mrt = VALUES(mrt),
                lat = VALUES(lat),
                lng = VALUES(lng)
        """
        cursor.executemany(sql_attraction, data_a)
        logger.info(f"✅ Successfully inserted/updated {cursor.rowcount} attraction rows.")

        logger.info("Executing batch insert into 'attraction_image' table...")
        # Clear previous image records for these attractions to avoid duplicates on re-runs
        attraction_ids = tuple(df_a["id"].tolist())
        if attraction_ids:
            format_strings = ",".join(["%s"] * len(attraction_ids))
            cursor.execute(f"DELETE FROM attraction_image WHERE attraction_id IN ({format_strings})", attraction_ids)

        sql_image = """
            INSERT INTO attraction_image (attraction_id, image_url)
            VALUES (%s, %s)
        """
        cursor.executemany(sql_image, data_ai)
        logger.info(f"✅ Successfully inserted {cursor.rowcount} image rows.")

        connection.commit()
        logger.info("🎉 Data commit successful!")

    except mysql.connector.Error as err:
        logger.error(f"❌ Database error occurred: {err}")
        connection.rollback()
        logger.info("Transaction rolled back.")
        raise err
    finally:
        cursor.close()
        if close_conn:
            connection.close()
            logger.info("🚪 Database connection closed.")


def run_pipeline(json_path: str = "data/taipei-attractions.json"):
    """Runs the complete Data Pipeline (Extract -> Transform -> Load)."""
    logger.info("Starting Data Pipeline execution...")
    raw_data = load_raw_data(json_path)
    df_a, df_attraction_image = transform_data(raw_data)
    load_to_db(df_a, df_attraction_image)
    logger.info("Data Pipeline completed successfully! 🎉")


if __name__ == "__main__":
    # Standard script invocation
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_json = os.path.join(script_dir, "data", "taipei-attractions.json")
    run_pipeline(default_json)
