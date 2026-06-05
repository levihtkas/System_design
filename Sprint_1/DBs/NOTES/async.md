Understanding Async Context Managers
An Async Context Manager is a Python object that manages the lifecycle of a resource (like a database connection or a network client) using asynchronous setup and teardown. It ensures that resources are opened and closed properly without blocking the rest of your application.

1. The Core Differences: Sync vs. Async
Feature	Standard Context Manager (with)	Async Context Manager (async with)
Methods	Uses __enter__ and __exit__.	Uses __aenter__ and __aexit__.
Execution	Blocks the thread until the resource is ready.	Yields control back to the event loop while waiting.
Usage	Local files, basic locks, non-I/O tasks.	Databases (Redis, Neo4j), APIs (HTTPX), WebSockets.
Lifespan	Immediate and sequential.	Can stay open across many background tasks.
2. Main Concepts for Your Notes
Non-Blocking Cleanup: In a high-concurrency app, you cannot afford to wait for a database to "close." Async context managers allow the "Chef" (Event Loop) to handle other users while the connection is shutting down.

The yield Keyword: When using the @asynccontextmanager decorator, yield acts as the boundary. Everything before it is Setup; everything after it is Teardown.

Resource Safety: It guarantees that even if your code crashes (e.g., the Cricbuzz API returns an error), the __aexit__ or the code after yield will still run to close the connection.

3. Implementation Guide
A. The Global Lifespan (FastAPI)
This is used to manage resources that should live as long as the server is running (like your cricket poller and Redis connection).

Python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- SETUP (Starts when you run the server) ---
    print("Startup: Opening Redis and starting background tasks")
    # Example: asyncio.create_task(cricket_data_poller())
    
    yield  # The application runs while "sitting" here
    
    # --- TEARDOWN (Starts when you stop the server) ---
    print("Shutdown: Closing Redis and cleaning up resources")
    # Example: await redis_client.close()

app = FastAPI(lifespan=lifespan)
B. Reusable Client (HTTPX Optimization)
Instead of opening a new client every 15 seconds, keep the manager open outside your loop to reuse the connection.

Python
import httpx
import asyncio

async def cricket_data_poller():
    # 'async with' ensures the client is created once and closed at the very end
    async with httpx.AsyncClient() as client:
        while True:
            # Reusing the same 'client' for every request
            response = await client.get("https://api.example.com/scores")
            data = response.json()
            
            # Wait for 15 seconds without blocking the server
            await asyncio.sleep(15) 
4. Why use async with instead of manual connect()?
Implicit Closing: You don't have to remember to type await client.close(). The indent level of the async with block handles it for you.

Exception Handling: If client.get() fails, the context manager still triggers the "close" logic. A manual connect() would leave the connection "leaking" in memory if the script crashed before reaching the manual close() line.

SDE-2 Standard: Senior engineers use context managers to make code atomic—either the whole block works and cleans up, or it fails and cleans up anyway.