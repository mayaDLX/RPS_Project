import numpy as np
import noise


def generate_random(shape, min_value=0, max_value=1, step=0.1):
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


def generate_pulse(shape, first_circle_size=0.1, last_circle_size=0.9,  first_intensity=0, last_intensity=255, organic_growth=True):
    # Start with a white background (255 for full brightness)
    pulse_array = np.ones(shape) * 255

    center_x = shape[0] // 2
    center_y = shape[1] // 2

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
    for z in range(shape[2]):
        for i in range(z + 1):  # Ensures every previous circle is included in every subsequent frame
            # Calculate radius for each circle using the custom growth function
            radius = circle_radius_step(i, shape[2]) * max_radius

            # Calculate the intensity of each circle using a linear interpolation
            intensity = circle_intensity_step(i, shape[2])

            # Draw each circle in every frame
            for x in range(shape[0]):
                for y in range(shape[1]):
                    distance = np.hypot(x - center_x, y - center_y)

                    # For pixels inside the current radius, set the intensity
                    if distance <= radius:
                        pulse_array[x, y, z] = min(pulse_array[x, y, z], intensity)

    # Normalize the pulse array between 0 and 1 for proper display
    pulse_array = pulse_array / 255.0
    return pulse_array


def locate_pattern_on_canvas(canvas_shape, location, ):
    return np.ones((canvas_x_dim, canvas_y_dim)) * 255