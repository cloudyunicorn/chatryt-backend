import os
import sys
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Testing connection to: {DATABASE_URL.split('@')[-1]}")

try:
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }
    pool = ConnectionPool(conninfo=DATABASE_URL, kwargs=connection_kwargs, timeout=10)
    print("Pool created. Attempting setup...")
    
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    print("Setup successful!")
    
except Exception as e:
    print(f"Error during diagnostic: {e}")
    sys.exit(1)
