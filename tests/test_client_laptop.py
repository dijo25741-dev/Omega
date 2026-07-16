import asyncio
import websockets
import sys

async def connect_agent():
    uri = "ws://localhost:8000/ws/omega-001"
    print(f"Connecting to Cloud Layer at {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Successfully connected to Cloud Layer!")
            
            # Start background task to send heartbeat every 5 seconds
            async def send_heartbeats():
                while True:
                    try:
                        await websocket.send("heartbeat")
                        print("[Laptop] Sent heartbeat")
                        await asyncio.sleep(5)
                    except Exception as e:
                        print(f"[Laptop] Heartbeat error: {e}")
                        break

            heartbeat_task = asyncio.create_task(send_heartbeats())

            # Listen for relayed commands
            while True:
                command = await websocket.recv()
                print(f"[Laptop] Received command: {command}")
                if command == "LOCK":
                    print("[Laptop] Action: System locked successfully!")
                elif command == "UNLOCK":
                    print("[Laptop] Action: System unlocked!")
                else:
                    print(f"[Laptop] Action: Unknown command '{command}' received.")

    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(connect_agent())
    except KeyboardInterrupt:
        print("\nAgent stopped.")
