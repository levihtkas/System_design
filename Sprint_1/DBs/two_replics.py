import os
import time
from fastapi import FastAPI,Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pydantic import BaseModel


app = FastAPI()
load_dotenv()


read_DB_connection = os.getenv("READ_DB")
master_DB_connection = os.getenv("DB_PS_URL")
replica_engine = create_engine(read_DB_connection)
master_engine = create_engine(master_DB_connection)
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

 

# This defines the "Shape" of your data
class UserSchema(BaseModel):
    username: str
    email: str
    password_hash: str


def get_read_db():
        db = SessionLocal(bind = replica_engine)
        try:
            yield db
        finally:
            db.close()

def get_master_db():
        db = SessionLocal(bind = master_engine)
        try:
            yield db
        finally:
            db.close()


@app.get("/read")
def read_user(db = Depends(get_read_db)):
     res = db.execute(text("Select * from users"))
     return {'data':res.mappings().all()}


@app.post("/write")
def write_user(user:UserSchema,db = Depends(get_master_db)):
    db.execute(text("INSERT INTO users (username, email, password_hash) VALUES (:username, :email, :password_hash)"), {"username": user.username, "email": user.email, "password_hash": user.password_hash})
    db.commit()
    return {"message": "User created successfully"}

