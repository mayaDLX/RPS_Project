import pygame
import random
import args
import numpy as np
import noise

def generate_random_black_dots():
    """Generate random black pixels placed on the screen."""
    surface = pygame.Surface((args.WIDTH, args.HEIGHT))
    surface.fill(args.WHITE)  # Start with a white surface

    num_black_dots = int(0.005 * args.WIDTH * args.HEIGHT)
    for _ in range(num_black_dots):  # Add random black pixels
        x, y = random.randint(0, args.WIDTH - 1), random.randint(0, args.HEIGHT - 1)
        surface.set_at((x, y), args.BLACK)

    return surface


def generate_random_pattern(shape, min_value=0, max_value=256, step=255):
    return np.random.choice(np.arange(min_value, max_value + step, step), size=shape)


def generate_perlin_noise_3d(shape, scale=0.1, octaves=6, persistence=0.5, lacunarity=2.0, seed=None):
    if seed:
        np.random.seed(seed)
    noise_array = np.zeros(shape)

    for x in range(shape[0]):
        for y in range(shape[1]):
            for z in range(shape[2]):
                noise_array[x][y][z] = noise.pnoise3(
                    x * scale,
                    y * scale,
                    z * scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=8,
                    repeaty=8,
                    repeatz=8,
                    base=0
                )

    # Normalize the values to be between 0 and 1
    min_val = np.min(noise_array)
    max_val = np.max(noise_array)

    if max_val != min_val:
        noise_array = (noise_array - min_val) / (max_val - min_val)

    noise_array *= 255
    return noise_array

def generate_patten(pattern_type, shape):
    pattern = []
    if pattern_type == args.RANDOM:
        pattern = generate_random_pattern(shape)
    if pattern_type == args.PERLIN:
        pattern = generate_perlin_noise_3d(shape)
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
    # Initialize Pygame
    pygame.init()

    # Define the original small screen size and the scaling factor
    small_screen_width, small_screen_height = 32, 32  # Original size
    scale_factor = 10  # Scale up by a factor of 10 (adjust as needed)

    # Calculate the new window size after scaling
    scaled_width = small_screen_width * scale_factor
    scaled_height = small_screen_height * scale_factor

    # Set up the display with the new scaled size
    screen = pygame.display.set_mode((scaled_width, scaled_height))
    pygame.display.set_caption('Random Dots with Stripe Burst')

    fps = args.FPS
    clock = pygame.time.Clock()

    # Create a smaller surface to draw the original 32x32 content
    small_screen = pygame.Surface((small_screen_width, small_screen_height))

    # Main loop
    running = True
    frame_index = 0
    burst_active = False
    active_quadrant = 0

    pattern_array = generate_patten(args.PERLIN, args.PATTERN_QUARTER_SHAPE)
    constant_pattern_frames = convert_array_to_frames(pattern_array)
    print(constant_pattern_frames)

    while running:
        # Fill the small screen with a white background
        small_screen.fill((255, 255, 255))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    burst_frames = constant_pattern_frames
                    burst_active = True
                    frame_index = 0
                    active_quadrant = 1  # Top-right
                elif event.key == pygame.K_2:
                    burst_frames = constant_pattern_frames
                    burst_active = True
                    frame_index = 0
                    active_quadrant = 2  # Top-left
                elif event.key == pygame.K_3:
                    burst_frames = constant_pattern_frames
                    burst_active = True
                    frame_index = 0
                    active_quadrant = 3  # Bottom-right
                elif event.key == pygame.K_4:
                    burst_frames = constant_pattern_frames
                    burst_active = True
                    frame_index = 0
                    active_quadrant = 4  # Bottom-left

        # Generate random black dots on the small screen
        small_screen.blit(generate_random_black_dots(), (0, 0))

        # If burst is active, play the animation in the selected location
        if burst_active:
            location = get_location(active_quadrant)
            # Blit the pattern into the specified location on the small screen
            small_screen.blit(burst_frames[frame_index], location)
            frame_index += 1
            if frame_index >= len(burst_frames):
                burst_active = False  # End the animation after all frames are shown

        # Scale up the small screen to the larger window
        scaled_screen = pygame.transform.scale(small_screen, (scaled_width, scaled_height))

        # Blit the scaled surface to the actual screen
        screen.blit(scaled_screen, (0, 0))

        # Update the display
        pygame.display.flip()
        clock.tick(fps)  # Limit the frame rate to the specified FPS

    # Quit Pygame
    pygame.quit()


if __name__ == '__main__':
    main()
