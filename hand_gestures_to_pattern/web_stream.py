import asyncio
import websockets
from pygame_screen import PygameScreen
from frame_processor import FrameProcessor
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
        self.screen = PygameScreen()
        self.frame_processor = FrameProcessor()
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
                        self.frame_processor.update(i)
                        self.current_posture = self.messages[i]  # Update the current posture
                        break

    async def check_input(self):
        # Check and process the client input
        if self.client_input is not None:
            print(f"Current client input: {self.client_input}")
            if self.client_input != self.current_posture:  # Only if posture has changed
                for i in range(len(self.messages)):
                    if self.client_input == self.messages[i]:
                        self.frame_processor.update(i)
                        self.current_posture = self.client_input  # Update the current posture
                        break
        else:
            print("No input from client yet.")
            await self.debug_react()

        await asyncio.sleep(0)  # Yield control to allow other tasks to run

    # Main loop to process client input and render animation
    async def screen_loop(self):
        while self.screen.running:

            # Handle Pygame events (this prevents freezing)
            self.key_events = pygame.event.get()
            for event in self.key_events:
                if event.type == pygame.QUIT:
                    self.screen.running = False

            await self.check_input()

            next_frame = self.frame_processor.get_next_frame()
            self.screen.screen_iteration(next_frame)


    # Main function to run both the WebSocket server and the screen loop concurrently
    async def run(self):
        # Start WebSocket server and screen loop concurrently
        await asyncio.gather(
            self.start_websocket_server(),
            self.screen_loop()
        )

