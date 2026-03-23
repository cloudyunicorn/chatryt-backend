import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Check if tables exist
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tables = [row[0] for row in cur.fetchall()]
            print(f"Tables found: {tables}")
            
            if "checkpoints" in tables:
                cur.execute("SELECT thread_id, count(*) FROM checkpoints GROUP BY thread_id")
                rows = cur.fetchall()
                print(f"Threads in database: {rows}")
            else:
                print("Checkpoints table does not exist!")
except Exception as e:
    print(f"Error querying database: {e}")
