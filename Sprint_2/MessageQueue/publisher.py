import json
from google.cloud import pubsub_v1

project_id = "prefab-overview-416104"
topic_id = "flight-prices"


pubClient = pubsub_v1.PublisherClient()
topic_path = pubClient.topic_path(project_id, topic_id)

def send_flight(origin,dest,price):
    message = {
        "origin": origin,
        "destination": dest,
        "price": price
    }
    message_json = json.dumps(message)
    message_bytes = message_json.encode("utf-8")
    isdealstr = "true" if price < 30000 else "false"
    future = pubClient.publish(topic_path, data=message_bytes,is_deal=isdealstr)
    
    print(f"Published message ID: {future.result()}")
    
send_flight("BLR", "SIN", 25000) # Should be a deal
send_flight("BLR", "LHR", 65000) # Normal price