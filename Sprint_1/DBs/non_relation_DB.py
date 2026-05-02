import os
from contextlib import asynccontextmanager
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from fastapi import FastAPI,Depends,Request
from pydantic import BaseModel
from neo4j import AsyncGraphDatabase
from contextlib import asynccontextmanager


load_dotenv()

class UserSchema(BaseModel):
    name: str
    role: str
    age: int

class FollowRequest(BaseModel):
    follower_name: str
    following_name: str

#Drivers
mongo_db_url = os.getenv("mongo_db_url")
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")
neo4j_database = os.getenv("NEO4J_DATABASE")
postgres_db_url = os.getenv("DB_PS_URL")

class Neo4jManager:
    def __init__(self):
        self.driver = None
    
    async def connect(self):
        self.driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        await self.driver.verify_connectivity()
    async def close(self):
        if self.driver:
            await self.driver.close()

neo4j_database_con = Neo4jManager()

@asynccontextmanager
async def get_neo4j_session(app:FastAPI):
    await neo4j_database_con.connect()
    yield {"neo4j_driver": neo4j_database_con.driver}
    await neo4j_database_con.close()

app = FastAPI(lifespan=get_neo4j_session)

@app.get("/neo4j")
async def read_neo4j_data(name:str,request:Request):
    driver = request.state.neo4j_driver

    query = "MATCH (u:User {name: $name}) return u"
    async with driver.session() as session:
        result = await session.run(query,name=name)
        record = await result.data() 
        # If record is empty, let's return a clearer message
        if not record:
            return {"status": "User not found", "searched_for": name}
        return {"status":"Connected",'data':record}
    
@app.post("/neo4j")
async def create_user(user:UserSchema,request:Request):
    driver = request.state.neo4j_driver
    query = "MERGE (u:User {name: $name}) SET u.role = $role, u.age = $age RETURN u"
    async with driver.session() as session:
        await session.run(
            query,
            name=user.name,
            role=user.role,
            age=user.age
        )
    return {"message": "User created successfully in Neo4j"}



@app.post("/neo4j/follow")
async def follow_user(data: FollowRequest, request: Request):
    driver = request.state.neo4j_driver
    query = """
    MATCH (follower:User {name: $follower_name}), (following:User {name: $following_name})
    MERGE (follower)-[:FOLLOWS]->(following)
    """
    async with driver.session() as session:
        await session.run(
            query,
            follower_name=data.follower_name,
            following_name=data.following_name
        )
    return {"message": f"{data.follower_name} now follows {data.following_name} in Neo4j"}

@app.get("/neo4j/followers/{username}")
async def get_followers(username: str, request: Request):
    driver = request.state.neo4j_driver
    query = """
    MATCH (follower:User)-[:FOLLOWS]->(following:User {name: $username})
    RETURN follower.name AS follower_name
    """
    async with driver.session() as session:
        result = await session.run(query, username=username)
        data = await result.data()
        
    follower_list = [record["follower_name"] for record in data]
        
    return {"username": username, "followers": follower_list}
