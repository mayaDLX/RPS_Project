from hand_gestures_to_pattern import args, patterns_generator

class FrameProcessor:

    def __init__(self):
        # loop setup:
        self.burst_array = []
        self.frame_index = 0
        self.burst_active = False
        self.active_quadrant = 0
        self.constant_pattern_array = patterns_generator.generate_patten_array(args.CHOSEN_PATTERN,
                                                                               args.PATTERN_QUARTER_SHAPE)

    def update(self, input_key):
        self.burst_array = self.constant_pattern_array
        self.burst_active = True
        self.frame_index = 0
        self.active_quadrant = input_key + 1

    def get_next_frame(self):
        background = patterns_generator.generate_background_2d((args.WIDTH, args.HEIGHT))

        if self.burst_active:
            location = args.calc_quarter_location(self.active_quadrant)
            # Blit the pattern into the specified location on the small screen
            patterns_generator.insert_2d_subarray(background, self.burst_array[self.frame_index], location)
            self.frame_index += 1
            if self.frame_index >= len(self.burst_array):
                self.burst_active = False  # End the animation after all frames are shown

        return background
