import os
import psycopg2
from urllib.parse import urlparse

db_url = os.environ.get("DATABASE_URL")
db_schema = os.environ.get("DB_SCHEMA", "ecommerce_schema")

if db_url:
    print(f"Creating schema {db_schema} if it doesn't exist...")
    result = urlparse(db_url)
    
    try:
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {db_schema};")
        print(f"Schema {db_schema} is ready!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to create schema: {e}")
else:
    print("No DATABASE_URL found, skipping schema creation.")
