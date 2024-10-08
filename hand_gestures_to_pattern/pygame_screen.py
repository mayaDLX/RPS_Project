import pygame
from hand_gestures_to_pattern import args, patterns_generator
import numpy as np


class PygameScreen:

    def __init__(self):
        # Game screen setup:
        # Initialize Pygame
        pygame.init()

        # Set up the display with the new scaled size
        self.view_screen = pygame.display.set_mode(args.SCALED_SIZE)
        pygame.display.set_caption('Random Dots with Stripe Burst')

        self.fps = args.FPS
        self.clock = pygame.time.Clock()

        # Create a smaller surface to draw the original 32x32 content
        self.pixels_screen = pygame.Surface((args.WIDTH, args.HEIGHT))

        # Main loop setup:
        self.running = True
        self.burst_array = []
        self.frame_index = 0
        self.burst_active = False
        self.active_quadrant = 0
        self.constant_pattern_array = patterns_generator.generate_patten_array(args.CHOSEN_PATTERN, args.PATTERN_QUARTER_SHAPE)

    def update_by_input(self, i):
        self.burst_array = self.constant_pattern_array
        self.burst_active = True
        self.frame_index = 0
        self.active_quadrant = i + 1

    def screen_iteration(self, frame_data):

        surface = pygame.Surface((args.WIDTH, args.HEIGHT))

        pygame.surfarray.blit_array(surface, np.stack([frame_data] * 3, axis=-1))

        # # Generate random black dots as background
        self.pixels_screen.blit(surface, (0, 0))

        # Scale up the small screen to the larger window
        scaled_screen = pygame.transform.scale(self.pixels_screen, args.SCALED_SIZE)

        # Blit the scaled surface to the actual screen
        self.view_screen.blit(scaled_screen, (0, 0))

        # Update the display
        pygame.display.flip()
        self.clock.tick(self.fps)  # Limit the frame rate to the specified FPS
