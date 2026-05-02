from fastapi import FastAPI,Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from RoutingSession import RoutingSession
import os

app = FastAPI()
load_dotenv()
read_DB_connection = os.getenv("READ_DB")
master_DB_connection = os.getenv("DB_PS_URL")
replica_engine = create_engine(read_DB_connection)
master_engine = create_engine(master_DB_connection)
SessionLocal = sessionmaker(class_=RoutingSession, autocommit=False, autoflush=False)

SessionLocal.configure(
    master_engine=master_engine, 
    replica_engine=replica_engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/read")
def read_data(db=Depends(get_db)):
        res = db.execute(text("Select * from users"))
        return {'data':res.mappings().all()}

@app.post("/write")
def write_data(db=Depends(get_db)):
    db.execute(text("INSERT INTO users (username, email, password_hash) VALUES ('test_user', 'test@example.com', 'hashed_password')"))
    db.commit()
    return {"message": "User created successfully"}

