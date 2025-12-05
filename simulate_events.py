import asyncio
import websockets
import json
import time

async def simulate_backend():
    uri = "ws://localhost:8765"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")

            # 1. Listen for initial student list
            message = await websocket.recv()
            print(f"Received: {message}")

            # 2. Start Session (mock frontend sending selection)
            print("Sending start_session...")
            await websocket.send(json.dumps({
                "message_type": "start_session",
                "student_name": "Test Student"
            }))

            # 3. Simulate Backend sending events
            # NOTE: In reality, backend broadcasts these. We can't easily force backend to broadcast
            # without modifying backend code.
            # BUT, since we are a client, we can send messages that might trigger broadcasts
            # OR we can just act as a second client receiving them if we had a way to trigger them.

            # Actually, `main.py` broadcasts `session_start` when AssemblyAI starts.
            # We can't fake AssemblyAI events easily without mocking the library.

            # WAIT. The task is to verify the UI.
            # I should run a MOCK SERVER, not a client.
            # The UI connects to localhost:8765.
            # I should kill the real backend and run this script as the server.
            pass

    except Exception as e:
        print(f"Client Error: {e}")

async def mock_server(websocket, path):
    print("Client connected!")

    # 1. Send Student List
    await websocket.send(json.dumps({
        "message_type": "student_list",
        "students": ["Alice", "Bob", "Charlie", "David"]
    }))
    print("Sent student list")

    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

            if data.get("message_type") == "start_session":
                # 2. Send Session Start
                await websocket.send(json.dumps({
                    "message_type": "session_start",
                    "session_id": "test-session-123"
                }))
                print("Sent session_start")

                # 3. Send Partials
                partials = ["Hello", "Hello I", "Hello I am", "Hello I am testing", "Hello I am testing the", "Hello I am testing the UI."]
                for p in partials:
                    await websocket.send(json.dumps({
                        "message_type": "partial",
                        "text": p
                    }))
                    await asyncio.sleep(0.2)

                # 4. Send Final
                await websocket.send(json.dumps({
                    "message_type": "transcript",
                    "text": "Hello, I am testing the UI.",
                    "speaker": "Test Student",
                    "turn_order": 1
                }))
                print("Sent transcript")

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

start_server = websockets.serve(mock_server, "localhost", 8765)

if __name__ == "__main__":
    print("Starting Mock WebSocket Server on port 8765...")
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(start_server)
    event_loop.run_forever()
