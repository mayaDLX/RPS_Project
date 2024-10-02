import websockets
import asyncio

async def handle_connection(websocket, path):
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            # Respond or process the message if needed
    except websockets.ConnectionClosed:
        print("Client disconnected")

start_server = websockets.serve(handle_connection, "localhost", 5678)

asyncio.get_event_loop().run_until_complete(start_server)
print("WebSocket server is running...")
asyncio.get_event_loop().run_forever()
