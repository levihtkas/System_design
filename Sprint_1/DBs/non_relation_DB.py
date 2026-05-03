import os
from contextlib import asynccontextmanager
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from fastapi import FastAPI,Depends,Request
from pydantic import BaseModel
from neo4j import AsyncGraphDatabase
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

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
class RedisManager:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        self.redis = redis.from_url("redis://localhost:6379")
        await self.redis.ping()
    
    async def close(self):
        if self.redis:
            await self.redis.close()


class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
    
    async def connect(self):
        self.client = AsyncIOMotorClient(mongo_db_url)
        list_of_db = await self.client.list_database_names()
        print(list_of_db)
        self.db = self.client.test
    
    async def close(self):
        if self.client:
            self.client.close()
mongo_db_con = MongoDBManager()
neo4j_database_con = Neo4jManager()
redis_con = RedisManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Connect to everything
    await mongo_db_con.connect()
    await neo4j_database_con.connect()
    await redis_con.connect()
    print("Databases connected")
    
    # 2. Yield: This makes the drivers available to the app
    # We attach them to 'app.state' so they are easy to access
    yield {
        "mongo": mongo_db_con.db,
        "neo4j": neo4j_database_con.driver,
        "redis": redis_con.redis
    }
    
    # 3. Shutdown: Close everything
    await mongo_db_con.close()
    await neo4j_database_con.close()
    await redis_con.close()
    print("Databases closed")

app = FastAPI(lifespan=lifespan)

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
    
@app.get("/mongo")
async def read_mongo_data(request:Request):
    db = request.state.mongo
    # Just a simple test to show we can read from MongoDB
    users = await db.users.find().to_list(length=1)
    # Convert ObjectId to string
    for user in users:
        user["_id"] = str(user["_id"])
    return {"status": "Connected", "data": users}

@app.post("/redis")
async def write_to_redis(key: str, value: str, request: Request):
    redis_client = request.state.redis
    await redis_client.set(key, value)
    return {"status": "Value written to Redis"}

@app.get("/redis")
async def read_from_redis(key: str, request: Request):
    redis_client = request.state.redis
    value = await redis_client.get(key)
    if value is None:
        return {"status": "Key not found in Redis", "key": key}
    return {"status": "Value retrieved from Redis", "key": key, "value": value.decode('utf-8')}

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
