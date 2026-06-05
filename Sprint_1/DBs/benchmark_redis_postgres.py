import redis.asyncio as redis
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String
import os
import asyncio
from dotenv import load_dotenv
import ssl
from sqlalchemy import Column, String, Integer, select
load_dotenv()

raw_url = os.getenv("DB_PS_URL")
base_url = raw_url.split('?')[0]
async_url = base_url.replace("postgresql://", "postgresql+asyncpg://")

# 3. Create a standard Python SSL context
# This is the "proper" way to handle SSL with asyncpg
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 4. Create the engine with connect_args
engine = create_async_engine(
    async_url,
    connect_args={"ssl": ctx},
    echo=False
)
redis_url = "redis://localhost:6379"

AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users" # Ensure this matches your Neon table name
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50))
    email = Column(String(100))
    password_hash = Column(String)
    # --- 3. BENCHMARK LOGIC ---

async def run_benchmark():
    # Initialize Redis Client
    r = redis.from_url(redis_url, decode_responses=True)
    
    test_id = "user:sakthi_123"
    test_data = "Software Development Engineer II - July 2026 Goal"

    print(f"--- Starting Benchmark ---")
    
    # --- STEP 0: WARM-UP PHASE (The Fix for Cold Starts) ---
    print("⏳ Warming up Neon (Waking up serverless compute)...")
    async with AsyncSessionLocal() as session:
        # Simple query to trigger the Neon compute to start
        await session.execute(select(User).limit(1))
        print("✅ Neon is awake.\n")

    test_username = "sakthi_bench_1"
    test_email = "sakthsssi@example.com"

    # --- PHASE 1: REDIS (In-Memory) ---
    start_redis = time.perf_counter()
    await r.set(test_id, test_data)
    val_redis = await r.get(test_id)
    end_redis = time.perf_counter()
    
    redis_ms = (end_redis - start_redis) * 1000
    print(f"🚀 Redis Time: {redis_ms:.3f} ms")

    # --- PHASE 2: NEON (SQLAlchemy - Now Warm) ---
    start_neon = time.perf_counter()
    
    async with AsyncSessionLocal() as session:
        # 1. INSERT
        # Using a dynamic email to avoid UniqueViolation during the benchmark
        unique_email = f"sakthi_{int(time.time())}@example.com"
        new_user = User(username=test_username, email=unique_email, password_hash="hashed_123")
        session.add(new_user)
        await session.commit() 
        
        # 2. SELECT
        query = select(User).where(User.username == test_username)
        result = await session.execute(query)
        user_obj = result.scalars().first() # Using .scalars() for clean object access
        
    end_neon = time.perf_counter()
    neon_ms = (end_neon - start_neon) * 1000
    print(f"☁️  Neon Time (Warm): {neon_ms:.3f} ms")

    print(f"\n💡 Improvement: Neon is now reflecting actual query latency.")
    await r.close()
    
if __name__ == "__main__":
    asyncio.run(run_benchmark())