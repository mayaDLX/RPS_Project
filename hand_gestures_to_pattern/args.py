# Frame rate
FPS = 60

# Display size
WIDTH, HEIGHT = 32, 32
SCALE_SCREEN = 10
SCALED_SIZE = (WIDTH * SCALE_SCREEN, HEIGHT * SCALE_SCREEN)

# Pattern Size
PATTERN_LENGTH = 50
PATTERN_QUARTER_SHAPE = (PATTERN_LENGTH, HEIGHT // 2, WIDTH // 2)

VOL_BACKGROUND_NOISE = 2

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

RANDOM = 1
PERLIN = 2
PULSE = 3
PULSE_SPEED = 0.3

CHOSEN_PATTERN = PULSE


def calc_quarter_location(quadrant):
    if quadrant == 1:  # Top-right
        x = WIDTH // 2
        y = 0
    elif quadrant == 2:  # Top-left
        x = 0
        y = 0
    elif quadrant == 3:  # Bottom-right
        x = WIDTH // 2
        y = HEIGHT // 2
    elif quadrant == 4:  # Bottom-left
        x = 0
        y = HEIGHT // 2
    else:
        return
    return x, y
