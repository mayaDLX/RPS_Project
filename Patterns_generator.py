import numpy as np
import matplotlib.pyplot as plt
import cv2
import noise

# Parameters
canvas_x_dim = 100
canvas_y_dim = 100
canvas_z_dim = 100
pattern_x_dim = 30  # Increased dimensions for better visualization
pattern_y_dim = 30
pattern_z_dim = 20
scale = 0.1  # Adjust the scale to create smooth transitions
fps = 20
image_size = 400
first_circle_size = 0.1  # Small initial circle
last_circle_size = 0.6   # Almost the entire area
organic_growth = True      # Enable non-linear, organic growth
RANDOM = 1
PERLIN = 2
PULSE = 3
pattern_type = RANDOM

center1 = (15, 15, 0)
center2 = (15, 85, 0)
center3 = (85, 50, 0)
# Function to generate 3D Perlin noise
def generate_perlin_noise_3d(shape, scale=1.0, octaves=6, persistence=0.5, lacunarity=2.0, seed=None):
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
                    repeatx=1024,
                    repeaty=1024,
                    repeatz=1024,
                    base=0
                )

    # Normalize the values to be between 0 and 1
    min_val = np.min(noise_array)
    max_val = np.max(noise_array)

    if max_val != min_val:
        noise_array = (noise_array - min_val) / (max_val - min_val)

    return noise_array

def generate_random(min_value = 0, max_value = 1, step = 0.1):
    return np.random.choice(np.arange(min_value, max_value + step, step), size=(pattern_x_dim, pattern_y_dim, pattern_z_dim))


# Function to generate a pulse effect
def generate_pulse(x_dim, y_dim, z_dim, first_circle_size=0.1, last_circle_size=0.9,  first_intensity=0, last_intensity=255, organic_growth=True):
    # Start with a white background (255 for full brightness)
    pulse_array = np.ones((x_dim, y_dim, z_dim)) * 255

    center_x = x_dim // 2
    center_y = y_dim // 2

    max_radius = np.hypot(center_x, center_y)  # Maximum possible radius from the center

    # Generate organic growth if enabled
    def circle_radius_step(z_index, z_max):
        if organic_growth:
            # Organic growth using a non-linear easing function (square root)
            return first_circle_size + (last_circle_size - first_circle_size) * np.sqrt(z_index / z_max)
        else:
            # Linear growth
            return first_circle_size + (last_circle_size - first_circle_size) * (z_index / z_max)

    # Generate intensity values for each circle
    def circle_intensity_step(z_index, z_max):
        return first_intensity + (last_intensity - first_intensity) * (z_index / z_max)

    # Loop over z_dim to create multiple circles for each "time" slice
    for z in range(z_dim):
        for i in range(z + 1):  # Ensures every previous circle is included in every subsequent frame
            # Calculate radius for each circle using the custom growth function
            radius = circle_radius_step(i, z_dim) * max_radius

            # Calculate the intensity of each circle using a linear interpolation
            intensity = circle_intensity_step(i, z_dim)

            # Draw each circle in every frame
            for x in range(x_dim):
                for y in range(y_dim):
                    distance = np.hypot(x - center_x, y - center_y)

                    # For pixels inside the current radius, set the intensity
                    if distance <= radius:
                        pulse_array[x, y, z] = min(pulse_array[x, y, z], intensity)

    # Normalize the pulse array between 0 and 1 for proper display
    pulse_array = pulse_array / 255.0
    return pulse_array

def generate_pattern():
    if pattern_type == RANDOM:
        return generate_random(step=1)
    elif pattern_type == PERLIN:
        return generate_perlin_noise_3d((pattern_x_dim, pattern_y_dim, pattern_z_dim), scale=0.1)
    elif pattern_type == PULSE:
        return generate_pulse(pattern_x_dim, pattern_y_dim, pattern_z_dim, first_circle_size, last_circle_size, organic_growth)

def preview_pattern(pattern):
    # List to hold precomputed frames
    frames = []

    # Create a figure and axis for consistent sizing
    fig, ax = plt.subplots(figsize=(6, 6))

    # Precompute frames (this happens before the video starts playing)
    for z in range(pattern_z_dim):
        ax.clear()
        # Visualize each slice as grayscale Perlin noise
        ax.imshow(pattern[:, :, z], cmap='gray', interpolation='none', vmin=0, vmax=1)
        ax.set_title(f'Perlin Noise Slice {z + 1}')
        ax.set_axis_off()
        fig.canvas.draw()

        # Convert the Matplotlib figure to an OpenCV-compatible image
        image = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8').reshape(fig.canvas.get_width_height()[::-1] + (3,))
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Convert the image to grayscale
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Resize the image to the desired video frame size
        image_resized = cv2.resize(image_gray, (image_size, image_size))

        # Store the frame
        frames.append(image_resized)

    # Now play the precomputed frames
    for frame in frames:
        cv2.imshow('Perlin Noise Video', frame)
        if cv2.waitKey(int(1000 / fps)) & 0xFF == ord('q'):
            break

    # Release and close windows
    cv2.destroyAllWindows()

def create_canvas():
    return np.ones((canvas_x_dim, canvas_y_dim, canvas_z_dim))


def locate_trigger(canvas_, pattern_, center = (15, 15, 0)):
    x_min = max(0, center[0] - (pattern_x_dim // 2))
    x_max = min(canvas_x_dim, x_min + pattern_x_dim)
    y_min = max(0, center[1] - (pattern_y_dim // 2))
    y_max = min(canvas_y_dim, y_min + pattern_y_dim)
    z_min = max(0, center[2] - (pattern_z_dim // 2))
    z_max = min(canvas_z_dim, z_min + pattern_z_dim)
    canvas_[x_min:x_max, y_min:y_max, z_min:z_max] = pattern_[:(x_max-x_min), :(y_max-y_min), :(z_max-z_min)]
    return canvas_


if __name__ == '__main__':
    # Generate Perlin noise
    canvas_ = create_canvas()
    pattern_ = generate_pattern()
    canvas_ = locate_trigger(canvas_, pattern_, center=center1)
    canvas_ = locate_trigger(canvas_, pattern_, center=center2)
    canvas_ = locate_trigger(canvas_, pattern_, center=center3)
    preview_pattern(canvas_)
    print("Video played and closed!")
