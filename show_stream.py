import pygame
import random
import args
import numpy as np

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((args.WIDTH, args.HEIGHT))
pygame.display.set_caption('Random Dots with Stripe Burst')

fps = args.FPS
clock = pygame.time.Clock()

g_constant_pattern = []

def generate_random_black_dots():
    """Generate random black pixels placed on the screen."""
    surface = pygame.Surface((args.WIDTH, args.HEIGHT))
    surface.fill(args.WHITE)  # Start with a white surface

    for _ in range(100):  # Add random black pixels
        x, y = random.randint(0, args.WIDTH - 1), random.randint(0, args.HEIGHT - 1)
        surface.set_at((x, y), args.BLACK)

    return surface


def generate_random_pattern(shape, min_value=0, max_value=256, step=255):
    return np.random.choice(np.arange(min_value, max_value + step, step), size=shape)


def generate_patten(pattern_type, shape):
    pattern = []
    if pattern_type == args.RANDOM:
        pattern = generate_random_pattern(shape)
    return pattern


def convert_array_to_frames(array: np.ndarray):
    """Convert a 3D NumPy array into a list of Pygame surfaces matching the quadrant size."""
    frames = []
    shape = array.shape  # shape = (F, H, W)
    for frame in array:
        surface = pygame.Surface((shape[2], shape[1]))  # Create surface matching quadrant size
        pygame.surfarray.blit_array(surface, np.stack([frame] * 3, axis=-1))  # Convert to RGB format
        frames.append(surface)

    return frames


def generate_moving_stripes():
    """Generate an array of frames with black and white moving stripes for one quadrant."""
    # The stripe array is created for a quadrant (half the width and height of the screen)
    stripe_array = generate_random_pattern((100, args.WIDTH // 2, args.HEIGHT // 2))
    burst_frames = convert_array_to_frames(stripe_array)
    return burst_frames


def get_location(quadrant):
    if quadrant == 1:  # Top-right
        x = args.WIDTH // 2
        y = 0
    elif quadrant == 2:  # Top-left
        x = 0
        y = 0
    elif quadrant == 3:  # Bottom-right
        x = args.WIDTH // 2
        y = args.HEIGHT // 2
    elif quadrant == 4:  # Bottom-left
        x = 0
        y = args.HEIGHT // 2
    else:
        return
    return x, y


def main():
    # Main loop
    running = True
    frame_index = 0
    burst_active = False
    active_quadrant = 0

    global g_constant_pattern
    pattern_array = generate_patten(args.RANDOM, args.PATTERN_SHAPE)
    g_constant_pattern = convert_array_to_frames(pattern_array)

    while running:

        # Generate random black dots on a white background
        screen.blit(generate_random_black_dots(), (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    burst_frames = g_constant_pattern
                    burst_active = True
                    frame_index = 0
                    active_quadrant = 1  # Top-right
                elif event.key == pygame.K_2:
                    burst_frames = g_constant_pattern
                    burst_active = True
                    frame_index = 0
                    active_quadrant = 2  # Top-left
                elif event.key == pygame.K_3:
                    burst_frames = g_constant_pattern
                    burst_active = True
                    frame_index = 0
                    active_quadrant = 3  # Bottom-right
                elif event.key == pygame.K_4:
                    burst_frames = g_constant_pattern
                    burst_active = True
                    frame_index = 0
                    active_quadrant = 4  # Bottom-left

        # If burst is active, play the animation in the selected location
        if burst_active:
            location = get_location(active_quadrant)
            # Blit the pattern into the specified location
            screen.blit(burst_frames[frame_index], location)
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
