import os
from fastapi import FastAPI,Depends
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
app = FastAPI()

load_dotenv()
DB_connection = os.getenv("DB_PS_URL")

engine = create_engine(DB_connection)

def get_db():
     with engine.connect() as connection:
        yield connection


@app.get("/")
async def test_connection():
    try:
        with engine.connect() as connection:
            stmt  = text("INSERT INTO users (username,email,password_hash) VALUES ((:name),'sakti@example.com','hashed_password') returning id")
            result = connection.execute(stmt,{"name":"ankit"})
            new_id = result.fetchone()[0]
            connection.commit()
            return {
                "status": "success",
                "message": "User created",
                "user_id": new_id
            }
    except Exception as e:
        return {"message": f"Database connection failed: {str(e)}"}
    
@app.get("/users")
async def get_users(db=Depends(get_db)):
        result = db.execute(text("SELECT id, username, email FROM users"))
        return {"users":result.mappings().all()}


 
