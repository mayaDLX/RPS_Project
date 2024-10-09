import asyncio
import websockets
import show_stream
import args
import pygame
from PyQt5.QtCore import pyqtSignal, QObject


class WebSocketServer:
    posture_changed = pyqtSignal(str)

    def __init__(self, host="localhost", port=5678):
        self.host = host
        self.port = port
        self.client_input = None  # Store input from the WebSocket client
        self.current_posture = None  # Track the current posture
        self.server = None
        self.stream = show_stream.VisualizeStream()
        self.messages = ["rock", "paper", "scissors"]
        self.key_events = []
        self.keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]

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

    async def debug_react(self):
        print("debug_react")
        for event in self.key_events:
            if event.type == pygame.KEYDOWN:
                for i in range(len(self.keys)):
                    if event.key == self.keys[i]:
                        self.stream.update_by_input(i)
                        self.current_posture = self.messages[i]  # Update the current posture
                        self.posture_changed.emit(self.current_posture)  # Emit posture change
                        break

    async def check_input(self):
        # Check and process the client input
        if self.client_input is not None:
            print(f"Current client input: {self.client_input}")
            if self.client_input != self.current_posture:  # Only if posture has changed
                for i in range(len(self.messages)):
                    if self.client_input == self.messages[i]:
                        self.stream.update_by_input(i)
                        self.current_posture = self.client_input  # Update the current posture
                        break
        else:
            print("No input from client yet.")
            await self.debug_react()

        await asyncio.sleep(0)  # Yield control to allow other tasks to run

    # Main loop to process client input and render animation
    async def screen_loop(self):
        while self.stream.running:

            # Handle Pygame events (this prevents freezing)
            self.key_events = pygame.event.get()
            for event in self.key_events:
                if event.type == pygame.QUIT:
                    self.stream.running = False

            # Fill the small screen with a white background
            self.stream.pixels_screen.fill(args.WHITE)

            # Generate random black dots as background
            self.stream.pixels_screen.blit(show_stream.generate_random_black_dots(), (0, 0))

            await self.check_input()

            # If burst is active, play the animation in the selected location
            self.stream.play_animation()

            # Scale up the small screen to the larger window
            scaled_screen = pygame.transform.scale(self.stream.pixels_screen, args.SCALED_SIZE)

            # Blit the scaled surface to the actual screen
            self.stream.view_screen.blit(scaled_screen, (0, 0))

            # Update the display
            pygame.display.flip()
            self.stream.clock.tick(self.stream.fps)  # Limit the frame rate to the specified FPS

    # Main function to run both the WebSocket server and the screen loop concurrently
    async def run(self):
        # Start WebSocket server and screen loop concurrently
        await asyncio.gather(
            self.start_websocket_server(),
            self.screen_loop()
        )

