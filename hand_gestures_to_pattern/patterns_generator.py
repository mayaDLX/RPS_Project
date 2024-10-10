import numpy as np
import noise
from hand_gestures_to_pattern import args
import random


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


def insert_2d_subarray(large_array, small_array, position):
    large_array[position[0]:position[0] + small_array.shape[0],
                position[1]:position[1] + small_array.shape[1]] = small_array


def generate_background_2d(shape):
    background = np.ones(shape) * args.WHITE[0]
    for _ in range(args.VOL_BACKGROUND_NOISE):  # Add random black pixels
        x, y = random.randint(0, args.WIDTH - 1), random.randint(0, args.HEIGHT - 1)
        background[x, y] = args.BLACK[0]
    return background


def white_background(shape):
    return np.ones(shape) * args.WHITE


def create_pulse_animation_array(shape, pulse_speed):
    animation_array = np.zeros(shape,
                               dtype=np.uint8)  # 3D numpy array for (frames, height, width)

    # Maximum radius is half of the smallest dimension
    max_radius = min(shape[1], shape[2]) // 2
    center = (shape[1] // 2, shape[2] // 2)

    # Precompute distances for all points from the center
    y, x = np.ogrid[:shape[1], :shape[2]]
    distance_from_center = np.sqrt((x - center[1]) ** 2 + (y - center[0]) ** 2)

    # For each frame, calculate the pulse and brightness
    for frame in range(shape[0]):
        radius = pulse_speed * frame
        radius = min(radius, max_radius)  # Cap the radius at max_radius
        brightness = int(255 * (radius / max_radius))  # Brightness grows as radius grows

        # Fill the frame with brightness where distance <= radius
        animation_array[frame] = np.where(distance_from_center <= radius, brightness, 255)

    return animation_array


def generate_patten_array(pattern_type, shape):
    pattern = []
    if pattern_type == args.RANDOM:
        pattern = generate_random_pattern(shape)
    if pattern_type == args.PERLIN:
        pattern = generate_perlin_noise_3d(shape)
    if pattern_type == args.PULSE:
        pattern = create_pulse_animation_array(shape, args.PULSE_SPEED)
    return pattern
