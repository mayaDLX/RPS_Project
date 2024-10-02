import asyncio
import websockets
import show_stream
import args
import pygame


class WebSocketServer:
    def __init__(self, host="localhost", port=5678):
        self.host = host
        self.port = port
        self.client_input = None  # Store input from the WebSocket client
        self.server = None
        self.stream = show_stream.visualize_stream()
        self.messages = ["rock", "paper", "scissors"]

    # WebSocket server handling
    async def handle_connection(self, websocket, path):
        try:
            async for message in websocket:
                print(f"Received message: {message}")
                self.client_input = message  # Store the input from the WebSocket client
        except websockets.ConnectionClosed:
            print("Client disconnected")

    # Function to start the WebSocket server
    async def start_websocket_server(self):
        self.server = await websockets.serve(self.handle_connection, self.host, self.port)
        print(f"WebSocket server started on {self.host}:{self.port}")
        await self.server.wait_closed()  # Keeps the server running

    # Main loop to process client input and render animation
    async def screen_loop(self):
        while self.stream.running:
            # Fill the small screen with a white background
            self.stream.pixels_screen.fill(args.WHITE)

            # Generate random black dots as background
            self.stream.pixels_screen.blit(self.stream.generate_random_black_dots(), (0, 0))

            # Scale up the small screen to the larger window
            scaled_screen = pygame.transform.scale(self.stream.pixels_screen, args.SCALED_SIZE)

            # Blit the scaled surface to the actual screen
            self.stream.view_screen.blit(scaled_screen, (0, 0))

            # Update the display
            pygame.display.flip()
            self.stream.clock.tick(self.stream.fps)  # Limit the frame rate to the specified FPS

            # Check and process the client input
            if self.client_input is not None:
                print(f"Current client input: {self.client_input}")
            else:
                print("No input from client yet.")

            await asyncio.sleep(0)  # Yield control to allow other tasks to run

    # Main function to run both the WebSocket server and the screen loop concurrently
    async def run(self):
        # Start WebSocket server and screen loop concurrently
        await asyncio.gather(
            self.start_websocket_server(),
            self.screen_loop()
        )


if __name__ == '__main__':
    server = WebSocketServer()
    asyncio.run(server.run())
