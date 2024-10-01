import pygame
import random
import arg
import numpy as np

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((arg.WIDTH, arg.HEIGHT))
pygame.display.set_caption('Random Dots with Stripe Burst')

fps = arg.FPS
clock = pygame.time.Clock()


def generate_random_black_dots():
    """Generate random black pixels placed on the screen."""
    surface = pygame.Surface((arg.WIDTH, arg.HEIGHT))
    surface.fill(arg.WHITE)  # Start with a white surface

    for _ in range(100):  # Add random black pixels
        x, y = random.randint(0, arg.WIDTH - 1), random.randint(0, arg.HEIGHT - 1)
        surface.set_at((x, y), arg.BLACK)

    return surface


def create_stripes_array(frames, width, height, stripe_width, speed):
    """Create a 3D NumPy array representing black and white moving stripes."""
    # Initialize a 3D array: (number of frames, height, width)
    stripe_array = np.ones((frames, height, width), dtype=np.uint8) * 255  # Start with white (255)

    for frame in range(frames):
        offset = (frame * speed) % (stripe_width * 2)  # Calculate moving offset

        for i in range(-stripe_width, width, stripe_width * 2):  # Fix to ensure consistent rendering
            start = (i + offset) % width
            end = min(start + stripe_width, width)
            stripe_array[frame, :, start:end] = 0  # Set stripe to black

    return stripe_array


def convert_array_to_frames(stripe_array):
    """Convert a 3D NumPy array into a list of Pygame surfaces."""
    frames = []

    for frame in stripe_array:
        surface = pygame.Surface((arg.WIDTH, arg.HEIGHT))
        pygame.surfarray.blit_array(surface, np.stack([frame] * 3, axis=-1))  # Convert to RGB format
        frames.append(surface)

    return frames


def generate_moving_stripes():
    """Generate an array of frames with black and white moving stripes."""
    # Increase stripe width for less flicker and reduce speed for smoother transition
    stripe_array = create_stripes_array(100, arg.WIDTH, arg.HEIGHT, stripe_width=50, speed=2)
    burst_frames = convert_array_to_frames(stripe_array)
    return burst_frames


def main():
    # Main loop
    running = True
    burst_frames = []
    frame_index = 0
    burst_active = False

    while running:

        # Generate random black dots on a white background
        screen.blit(generate_random_black_dots(), (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    burst_frames = generate_moving_stripes()
                    burst_active = True
                    frame_index = 0

        # If burst is active, play the animation
        if burst_active:
            screen.blit(burst_frames[frame_index], (0, 0))
            frame_index += 1
            if frame_index >= len(burst_frames):
                burst_active = False  # End the animation after all frames are shown

        # Update the screen
        pygame.display.flip()
        clock.tick(fps)  # Limit the frame rate to 60 FPS

    # Quit Pygame
    pygame.quit()


if __name__ == '__main__':
    main()
