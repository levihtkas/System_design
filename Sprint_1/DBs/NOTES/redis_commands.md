# XADD [key] [ID] [field] [value] ...
    XADD concert_feed * action "like" user "alice"
    ```
   

---

### Comparison for your Notes
| Command           | Data Structure | Best Use Case                                  |
| :---------------- | :------------- | :--------------------------------------------- |
| **`SET` / `GET`** | String         | Simple caching, session storage.               |
| **`PFADD`**       | HyperLogLog    | Counting unique visitors with minimal RAM.     |
| **`XADD`**        | Stream         | Real-time event logs, message queues.          |
| **`ZADD`**        | Sorted Set     | Real-time leaderboards (auto-sorted by score). |

### How it looks in FastAPI
You can use these specialized commands directly in your code to handle millions of events without slowing down your API:
```python
import redis
from fastapi import FastAPI

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.post("/concert/{id}/interaction")
async def track_interaction(id: str, user_id: str):
    # 1. Count unique viewer (Probabilistic)
    r.pfadd(f"unique_viewers:{id}", user_id)
    
    # 2. Add event to stream for analytics
    r.xadd(f"concert_stream:{id}", {"user": user_id, "action": "click"})
    
    return {"status": "ok"}