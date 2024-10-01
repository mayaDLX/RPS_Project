import asyncio
import websockets

class WebSocketServer:
    def __init__(self, host="localhost", port=5678):
        self.host = host
        self.port = port
        self.client_input = None  # Store input from the WebSocket client
        self.server = None

    # WebSocket server handling
    async def handle_connection(self, websocket, path):
        try:
            async for message in websocket:
                print(f"Received message: {message}")
                self.client_input = message  # Store the input from the WebSocket client
        except websockets.ConnectionClosed:
            print("Client disconnected")

    # Function to start the WebSocket server and keep it running
    async def start(self):
        self.server = await websockets.serve(self.handle_connection, self.host, self.port)
        await self.server.wait_closed()  # Keeps the server running

    # Main loop to process client input
    async def main_loop(self):
        while True:
            # Check and process the client input
            if self.client_input is not None:
                print(f"Current client input: {self.client_input}")
            else:
                print("No input from client yet.")
            await asyncio.sleep(1)  # Slow down the loop for demonstration

    # Main function to run both the WebSocket server and main loop concurrently
    async def run(self):
        await asyncio.gather(
            self.start(),
            self.main_loop()
        )


if __name__ == '__main__':
    server = WebSocketServer()
    asyncio.run(server.run())
