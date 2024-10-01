import numpy as np
import cv2
import noise
FRAME_SIZE = 100
PATTERN_LENGTH = 20
IMAGE_SIZE = 400
# Parameters
canvas_x_dim = 100
canvas_y_dim = 100
canvas_z_dim = 1  # Keeping Z-dimension as 1 for a 2D canvas
pattern_x_dim = 30
pattern_y_dim = 30
scale = 0.1
image_size = 400
first_circle_size = 0.1
last_circle_size = 0.6
organic_growth = True

center1 = (15, 15)
center2 = (15, 85)
center3 = (85, 50)

RANDOM = 1
PERLIN = 2
PULSE = 3
pattern_type = RANDOM

# Function to generate random pattern
def generate_random(min_value=0, max_value=1, step=0.1):
    return np.random.choice(np.arange(min_value, max_value + step, step), size=(pattern_x_dim, pattern_y_dim))

# Function to generate 2D Perlin noise
def generate_perlin_noise_2d(shape, scale=1.0, octaves=6, persistence=0.5, lacunarity=2.0, seed=None):
    if seed:
        np.random.seed(seed)
    noise_array = np.zeros(shape)

    for x in range(shape[0]):
        for y in range(shape[1]):
            noise_array[x][y] = noise.pnoise2(
                x * scale,
                y * scale,
                octaves=octaves,
                persistence=persistence,
                lacunarity=lacunarity,
                repeatx=1024,
                repeaty=1024,
                base=0
            )

    min_val = np.min(noise_array)
    max_val = np.max(noise_array)
    if max_val != min_val:
        noise_array = (noise_array - min_val) / (max_val - min_val)
    return noise_array

# Function to generate the pulse effect
def generate_pulse(x_dim, y_dim, first_circle_size=0.1, last_circle_size=0.9, first_intensity=0, last_intensity=255, organic_growth=True):
    pulse_array = np.ones((x_dim, y_dim)) * 255
    center_x = x_dim // 2
    center_y = y_dim // 2
    max_radius = np.hypot(center_x, center_y)

    def circle_radius_step(z_index, z_max):
        if organic_growth:
            return first_circle_size + (last_circle_size - first_circle_size) * np.sqrt(z_index / z_max)
        else:
            return first_circle_size + (last_circle_size - first_circle_size) * (z_index / z_max)

    radius = circle_radius_step(1, 1) * max_radius
    intensity = last_intensity

    for x in range(x_dim):
        for y in range(y_dim):
            distance = np.hypot(x - center_x, y - center_y)
            if distance <= radius:
                pulse_array[x, y] = min(pulse_array[x, y], intensity)

    pulse_array = pulse_array / 255.0
    return pulse_array

# Function to generate the pattern
def generate_pattern():
    if pattern_type == RANDOM:
        return generate_random(step=1)
    elif pattern_type == PERLIN:
        return generate_perlin_noise_2d((pattern_x_dim, pattern_y_dim), scale=0.1)
    elif pattern_type == PULSE:
        return generate_pulse(pattern_x_dim, pattern_y_dim, first_circle_size, last_circle_size, organic_growth)

# Create a white canvas
def create_canvas():
    return np.ones((canvas_x_dim, canvas_y_dim)) * 255

# Function to locate the pattern on the canvas
def locate_trigger(canvas_, pattern_, center):
    x_min = max(0, center[0] - (pattern_x_dim // 2))
    x_max = min(canvas_x_dim, x_min + pattern_x_dim)
    y_min = max(0, center[1] - (pattern_y_dim // 2))
    y_max = min(canvas_y_dim, y_min + pattern_y_dim)
    canvas_[x_min:x_max, y_min:y_max] = pattern_[:(x_max - x_min), :(y_max - y_min)]
    return canvas_

# Function to continuously display the canvas and update when a pattern is triggered
def update_canvas(canvas):
    # Resize the canvas for visualization
    image_resized = cv2.resize(canvas, (image_size, image_size))

    # Display the updated canvas
    cv2.imshow('Canvas', image_resized)

if __name__ == '__main__':
    # Generate an empty canvas
    canvas_ = create_canvas()

    # Continuously display the canvas and wait for user input
    while True:
        # Display the white canvas
        update_canvas(canvas_)

        # Wait for user input
        key = cv2.waitKey(1) & 0xFF

        if key == ord('1'):
            pattern_ = generate_pattern()
            canvas_ = locate_trigger(canvas_, pattern_, center1)
        elif key == ord('2'):
            pattern_ = generate_pattern()
            canvas_ = locate_trigger(canvas_, pattern_, center2)
        elif key == ord('3'):
            pattern_ = generate_pattern()
            canvas_ = locate_trigger(canvas_, pattern_, center3)
        elif key == ord('q'):
            break  # Quit the loop if 'q' is pressed

    # Clean up
    cv2.destroyAllWindows()
