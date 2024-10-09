import pygame
import random
import args
import numpy as np
import patterns_generator


def convert_array_to_frames(array: np.ndarray):
    """Convert a 3D NumPy array into a list of Pygame surfaces matching the quadrant size."""
    frames = []
    shape = array.shape  # shape = (F, H, W)
    for frame in array:
        surface = pygame.Surface((shape[2], shape[1]))  # Create surface matching quadrant size
        pygame.surfarray.blit_array(surface, np.stack([frame] * 3, axis=-1))  # Convert to RGB format
        frames.append(surface)

    return frames


def generate_random_black_dots():
    """Generate random black pixels placed on the screen."""
    surface = pygame.Surface((args.WIDTH, args.HEIGHT))
    surface.fill(args.WHITE)  # Start with a white surface

    for _ in range(args.VOL_BACKGROUND_NOISE):  # Add random black pixels
        x, y = random.randint(0, args.WIDTH - 1), random.randint(0, args.HEIGHT - 1)
        surface.set_at((x, y), args.BLACK)

    return surface


def generate_visual_pattern(pattern_type, shape):
    array = patterns_generator.generate_patten_array(pattern_type, shape)
    frames = convert_array_to_frames(array)
    return frames


class VisualizeStream:

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
        self.burst_frames = []
        self.frame_index = 0
        self.burst_active = False
        self.active_quadrant = 0
        self.constant_pattern = generate_visual_pattern(args.CHOSEN_PATTERN, args.PATTERN_QUARTER_SHAPE)

        self.keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]

    def update_by_input(self, i):
        self.burst_frames = self.constant_pattern
        self.burst_active = True
        self.frame_index = 0
        self.active_quadrant = i + 1

    def check_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                for i in range(len(self.keys)):
                    if event.key == self.keys[i]:
                        self.update_by_input(i)

    def play_animation(self):
        if self.burst_active:
            location = args.calc_quarter_location(self.active_quadrant)
            # Blit the pattern into the specified location on the small screen
            self.pixels_screen.blit(self.burst_frames[self.frame_index], location)
            self.frame_index += 1
            if self.frame_index >= len(self.burst_frames):
                self.burst_active = False  # End the animation after all frames are shown

    def main_loop(self):
        while self.running:
            # Fill the small screen with a white background
            self.pixels_screen.fill(args.WHITE)

            self.check_input()

            # Generate random black dots as background
            self.pixels_screen.blit(generate_random_black_dots(), (0, 0))

            # If burst is active, play the animation in the selected location
            self.play_animation()

            # Scale up the small screen to the larger window
            scaled_screen = pygame.transform.scale(self.pixels_screen, args.SCALED_SIZE)

            # Blit the scaled surface to the actual screen
            self.view_screen.blit(scaled_screen, (0, 0))

            # Update the display
            pygame.display.flip()
            self.clock.tick(self.fps)  # Limit the frame rate to the specified FPS

            # Quit Pygame
        pygame.quit()


def main():
    vs = VisualizeStream()
    vs.main_loop()


if __name__ == '__main__':
    main()
