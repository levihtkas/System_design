import os
import time
from fastapi import FastAPI,Depends
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()
ISOLATION_LEVELS = "READ COMMITTED"  # You can change this to the desired isolation level
DB_connection = os.getenv("DB_PS_URL")
engine = create_engine(DB_connection, isolation_level=ISOLATION_LEVELS)

def get_db():
        with engine.connect() as connection:
            yield connection

@app.get("/isolation")
async def test_isolation(connection=Depends(get_db)):
      try:
            result = connection.execute(text("SELECT username FROM users WHERE id = 1"))
            print(result.fetchall())
            time.sleep(15)  # Simulate long transaction
            result = connection.execute(text("SELECT username FROM users WHERE id = 1"))
            print(result.fetchall())
            return {"status": "success", "message": "Isolation level tested"}
      except Exception as e:
            return {"message": f"Database connection failed: {str(e)}"}

