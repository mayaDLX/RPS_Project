import asyncio
import websockets

# Global variable to store input from client
client_input = None


# WebSocket server handling
async def handle_connection(websocket, path):
    global client_input
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            client_input = message  # Store the input from the WebSocket client
    except websockets.ConnectionClosed:
        print("Client disconnected")


# Function to start the WebSocket server and keep it running
async def start_websocket_server():
    # Start the WebSocket server
    websocket_server = await websockets.serve(handle_connection, "localhost", 5678)
    await websocket_server.wait_closed()  # Keeps the server running


# Pygame main loop or test loop
async def main_loop():
    global client_input

    while True:
        # Here, you can check the client input and do something with it
        if client_input is not None:
            print(f"Current client input: {client_input}")
        else:
            print("No input from client yet.")

        await asyncio.sleep(1)  # Slow down the loop for demonstration


# Main function to run both the WebSocket server and main loop concurrently
async def main():
    # Run both the WebSocket server and the main loop concurrently
    await asyncio.gather(
        start_websocket_server(),
        main_loop()
    )


if __name__ == '__main__':
    asyncio.run(main())
