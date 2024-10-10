# @title      transform message from client to stimulation thread
# @file       WebSocketThread.py
# @author     Maya Moriya
# @date       09 Oct 2024
import numpy as np
import pygame
from hand_gestures_to_pattern import args, pygame_screen
import websockets
import asyncio
import threading
from PyQt5.QtCore import pyqtSignal, QObject, QThread


class WebSocketThread(QThread):
    posture_changed = pyqtSignal(str)  # Signal to notify posture changes

    def __init__(self, host="localhost", port=5678, parent=None):
        super(WebSocketThread, self).__init__(parent)
        self.host = host
        self.port = port
        self.client_input = None  # Store input from the WebSocket client
        self.current_posture = None  # Track the current posture
        self.server = None
        self.screen = pygame_screen.PygameScreen()
        self.messages = ["rock", "paper", "scissors"]
        self.key_events = []
        self.keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
        self.running = True  # To control the thread loop

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

    def run_websocket(self):
        asyncio.run(self.start_websocket_server())

    def receive_client_input(self):
        # Check and process the client input
        if self.client_input is not None:
            print(f"Current client input: {self.client_input}")
            if self.client_input != self.current_posture:  # Only if posture has changed
                for i in range(len(self.messages)):
                    if self.client_input == self.messages[i]:
                        self.screen.update_by_input(i)
                        self.current_posture = self.client_input  # Update the current posture
                        break
        else:
            print("No input from client yet.")

    def receive_key_input_debug(self):
        self.key_events = pygame.event.get()
        for event in self.key_events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                for i in range(len(self.keys)):
                    if event.key == self.keys[i]:
                        self.screen.update_by_input(i)
                        self.current_posture = self.messages[i]
                        self.posture_changed.emit(self.current_posture)  # Emit posture change
                        break

    def handle_key_interruptions(self):
        self.key_events = pygame.event.get()
        for event in self.key_events:
            if event.type == pygame.QUIT:
                self.running = False

    def run(self):
        # Start WebSocket server in a separate thread
        websocket_thread = threading.Thread(target=self.run_websocket)
        websocket_thread.start()

        # Pygame event loop
        while self.running:

            # Check client input and react
            self.receive_key_input_debug()

            self.screen.screen_iteration()

        # Clean up when loop exits
        websocket_thread.join()

