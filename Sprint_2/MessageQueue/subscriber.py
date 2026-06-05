import time
from google.cloud import pubsub_v1

project_id = "prefab-overview-416104"
# Run this once with "flight-prices-sub" and once with "deal-alerts-sub"
SUBSCRIPTION_ID = "flight-prices-sub" 

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, SUBSCRIPTION_ID)

def callback(message):
    print(f"[{SUBSCRIPTION_ID}] Received: {message.data.decode('utf-8')}")
    
    # Simulate a heavy task (like writing to a database)
    time.sleep(2) 
    
    # This is the most important part of a Message Broker!
    message.ack() 
    print(f"[{SUBSCRIPTION_ID}] Acknowledged message.")

streaming_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {SUBSCRIPTION_ID}...")

try:
    streaming_future.result()
except KeyboardInterrupt:
    streaming_future.cancel()