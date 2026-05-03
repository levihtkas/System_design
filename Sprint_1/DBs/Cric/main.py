from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from Cric.ConnectionManager import manager
import asyncio
import httpx
import os
import redis

RAPID_API_URL = "https://unofficial-cricbuzz.p.rapidapi.com/matches/get-overs?matchId=151998"
HEADERS = {
    'x-rapidapi-key': os.getenv("RAPID_API_KEY"),
    'x-rapidapi-host': "unofficial-cricbuzz.p.rapidapi.com",
    'Content-Type': "application/json"
}

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

@asynccontextmanager
async def startup_event():
    print("Starting up the application...")
    asyncio.create_task(cricket_data_poller())
    yield
    print("Shutting down the application...")
    
app = FastAPI(lifespan=startup_event)

async def cricket_data_poller():
    last_ball_id = 0
    while True:
        async with httpx.AsyncClient() as client:
            response = await client.get(RAPID_API_URL, headers=HEADERS)
            live_data = response.json()
            miniscore = live_data.get("miniscore", {})
            current_ball_id = live_data["overSepList"][0]["overSep"][0]["overNum"]
            current_score = miniscore["inningsScores"][0]["inningsScore"][0]["runs"]
            match_status = miniscore.get("custStatus")
        
        match_id = "151998" # change it manually wrt to cricbuzz
        current_ball_id = float(current_ball_id)
        if current_ball_id > last_ball_id:
            summary_str = live_data["overSepList"][0]["overSep"][0]["overSummary"]
            actual_ball = summary_str.strip().split(" ")[-1]
            prediction_key = f"match:{match_id}:ball:{current_ball_id}:predictions"
            predictions = r.hgetall(prediction_key)
            winners = []
            for user_id, guess in predictions.items():
                if guess == actual_ball:
                    r.zincrby(f"match:{match_id}:leaderboard", 10, user_id)
                    winners.append(user_id)
            top_score = r.zrevrange(f"match:{match_id}:leaderboard", 0, 0, withscores=True)


            broadcast_payload = {
                        "type": "LIVE_UPDATE",
                        "ball": str(current_ball_id),
                        "score": f"{current_score} runs",
                        "status": match_status,
                        "score_ball": actual_ball,
                        "winners_this_ball": winners,
                        "top_score": top_score,
                        "last_over_summary": summary_str
            }
            print(f"DEBUG: Shouting to room: {match_id}")
            await manager.broadcast_to_match(match_id, broadcast_payload)
            r.expire(prediction_key, 120)
            last_ball_id = current_ball_id
        await asyncio.sleep(15) 


@app.websocket("/ws/{match_id}/{user_id}")
async def cricket_prediction_circuit(websocket: WebSocket, match_id: str, user_id: str):
    await manager.connect(websocket, match_id)
    r.zadd(f"match:{match_id}:leaderboard", {user_id: 0}, nx=True)
    try:
        while True:
            data = await websocket.receive_json()
            ball_id = data.get("ball_id")
            guess = data.get("prediction")
            prediction = f"match:{match_id}:ball:{ball_id}:predictions"
            r.hset(prediction, user_id, guess)
            r.expire(prediction, 300)
            await manager.broadcast_to_match(match_id, {
                "type": "PREDICTION_PLACED",
                "user": user_id,
                "ball": ball_id
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)