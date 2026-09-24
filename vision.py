#!/usr/bin/env python3

import cv2
import numpy as np


# ============================================================
# CAMERA
# ============================================================

CAMERA_INDEX = 0
WIDTH = 640
HEIGHT = 480
FPS = 30


# ============================================================
# ROI SETTINGS
# ============================================================

# Obstacle detection
OBSTACLE_ROI = (50, 210, 590, 455)

# Large ROI ONLY for direction detection
DIRECTION_ROI = (20, 150, 620, 440)

# Normal line / lap counting
LINE_ROI = (40, 220, 600, 440)

# Wall ROIs
LEFT_ROI = (20, 260, 150, 455)
RIGHT_ROI = (490, 260, 620, 455)
FRONT_ROI = (145, 205, 495, 350)


# ============================================================
# WALL SETTINGS
# ============================================================

WALL_THRESHOLD = 100
SIDE_WALL_HIGH = 0.22
FRONT_WALL_HIGH = 0.15


# ============================================================
# OBSTACLE SETTINGS
# ============================================================

MIN_RED_OBSTACLE_AREA = 1800
MIN_GREEN_OBSTACLE_AREA = 1000

MIN_OBSTACLE_HEIGHT = 35
MAX_OBSTACLE_ASPECT = 1.8


# ============================================================
# LINE SETTINGS
# ============================================================

MIN_LINE_AREA = 80

# Direction settings
DIRECTION_CONFIRM_FRAMES = 3
DIRECTION_MIN_GAP = 20

# Line must disappear before re-arm
LINE_CLEAR_FRAMES = 5

# 12 crossings = 3 laps
# 13th line = stop reference
TOTAL_LINE_COUNT = 13


# ============================================================
# HSV - ORANGE
# ============================================================

ORANGE_LOW = (8, 80, 70)
ORANGE_HIGH = (30, 255, 255)


# ============================================================
# HSV - BLUE
# ============================================================

BLUE_LOW = (90, 70, 80)
BLUE_HIGH = (140, 255, 255)


# ============================================================
# HSV - GREEN
# ============================================================

GREEN_LOW = (35, 45, 25)
GREEN_HIGH = (85, 255, 255)


# ============================================================
# HSV - RED
# ============================================================

RED1_LOW = (0, 100, 60)
RED1_HIGH = (7, 255, 255)

RED2_LOW = (173, 100, 60)
RED2_HIGH = (180, 255, 255)


# ============================================================
# VISION
# ============================================================

class Vision:

    def __init__(self):

        # ----------------------------------------------------
        # CAMERA
        # ----------------------------------------------------

        self.cap = cv2.VideoCapture(
            CAMERA_INDEX
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            WIDTH
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            HEIGHT
        )

        self.cap.set(
            cv2.CAP_PROP_FPS,
            FPS
        )

        # ----------------------------------------------------
        # DIRECTION
        # ----------------------------------------------------

        self.direction = "UNKNOWN"

        self.first_color = None
        self.first_color_frames = 0

        # ----------------------------------------------------
        # LINE / LAP COUNTING
        # ----------------------------------------------------

        self.line_count = 0

        self.line_locked = False
        self.line_clear_frames = 0

        self.counting_enabled = False
        self.waiting_for_start_clear = False

        self.race_complete = False

        print("[VISION] Camera started")
        print("[VISION] Direction: UNKNOWN")


    # ========================================================
    # CROP ROI
    # ========================================================

    def crop(
        self,
        image,
        roi
    ):

        x1, y1, x2, y2 = roi

        return image[
            y1:y2,
            x1:x2
        ]


    # ========================================================
    # COLOR MASK
    # ========================================================

    def color_mask(
        self,
        hsv,
        lower,
        upper
    ):

        lower = np.array(
            lower,
            dtype=np.uint8
        )

        upper = np.array(
            upper,
            dtype=np.uint8
        )

        mask = cv2.inRange(
            hsv,
            lower,
            upper
        )

        kernel = np.ones(
            (3, 3),
            np.uint8
        )

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            kernel
        )

        return mask


    # ========================================================
    # LARGEST OBJECT
    # ========================================================

    def largest_object(
        self,
        mask,
        min_area
    ):

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        valid = []

        for contour in contours:

            area = cv2.contourArea(
                contour
            )

            if area >= min_area:
                valid.append(contour)

        if not valid:
            return None

        contour = max(
            valid,
            key=cv2.contourArea
        )

        area = cv2.contourArea(
            contour
        )

        x, y, w, h = cv2.boundingRect(
            contour
        )

        return {

            "x": x,
            "y": y,

            "w": w,
            "h": h,

            "cx": x + w // 2,
            "cy": y + h // 2,

            "area": area
        }


    # ========================================================
    # VALID OBSTACLE
    # ========================================================

    def valid_obstacle(
        self,
        obj,
        color
    ):

        if obj is None:
            return False

        # ----------------------------------------------------
        # AREA
        # ----------------------------------------------------

        if color == "RED":

            if (
                obj["area"]
                < MIN_RED_OBSTACLE_AREA
            ):

                return False

        elif color == "GREEN":

            if (
                obj["area"]
                < MIN_GREEN_OBSTACLE_AREA
            ):

                return False

        # ----------------------------------------------------
        # HEIGHT
        # ----------------------------------------------------

        if (
            obj["h"]
            < MIN_OBSTACLE_HEIGHT
        ):

            return False

        # ----------------------------------------------------
        # SHAPE
        # ----------------------------------------------------

        aspect = (
            obj["w"]
            / max(
                obj["h"],
                1
            )
        )

        if (
            aspect
            > MAX_OBSTACLE_ASPECT
        ):

            return False

        return True


    # ========================================================
    # WALL MASK
    # ========================================================

    def create_wall_mask(
        self,
        frame
    ):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.GaussianBlur(
            gray,
            (5, 5),
            0
        )

        _, mask = cv2.threshold(
            gray,
            WALL_THRESHOLD,
            255,
            cv2.THRESH_BINARY_INV
        )

        kernel = np.ones(
            (5, 5),
            np.uint8
        )

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            kernel
        )

        return mask


    # ========================================================
    # WALL RATIO
    # ========================================================

    def wall_ratio(
        self,
        mask,
        roi
    ):

        section = self.crop(
            mask,
            roi
        )

        if section.size == 0:
            return 0.0

        return (
            np.count_nonzero(section)
            / section.size
        )


    # ========================================================
    # WALL DETECTION
    # ========================================================

    def detect_walls(
        self,
        frame
    ):

        mask = self.create_wall_mask(
            frame
        )

        left = self.wall_ratio(
            mask,
            LEFT_ROI
        )

        front = self.wall_ratio(
            mask,
            FRONT_ROI
        )

        right = self.wall_ratio(
            mask,
            RIGHT_ROI
        )

        return (
            left,
            front,
            right,
            mask
        )


    # ========================================================
    # OBSTACLE DETECTION
    # ========================================================

    def detect_obstacle(
        self,
        frame
    ):

        x1, y1, x2, y2 = (
            OBSTACLE_ROI
        )

        roi = frame[
            y1:y2,
            x1:x2
        ]

        hsv = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2HSV
        )

        # ----------------------------------------------------
        # GREEN
        # ----------------------------------------------------

        green_mask = self.color_mask(
            hsv,
            GREEN_LOW,
            GREEN_HIGH
        )

        # ----------------------------------------------------
        # RED
        # ----------------------------------------------------

        red1 = self.color_mask(
            hsv,
            RED1_LOW,
            RED1_HIGH
        )

        red2 = self.color_mask(
            hsv,
            RED2_LOW,
            RED2_HIGH
        )

        red_mask = cv2.bitwise_or(
            red1,
            red2
        )

        # ----------------------------------------------------
        # FIND OBJECTS
        # ----------------------------------------------------

        green = self.largest_object(
            green_mask,
            200
        )

        red = self.largest_object(
            red_mask,
            200
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        if not self.valid_obstacle(
            green,
            "GREEN"
        ):

            green = None

        if not self.valid_obstacle(
            red,
            "RED"
        ):

            red = None

        # ----------------------------------------------------
        # FULL-FRAME COORDINATES
        # ----------------------------------------------------

        for obj in (
            green,
            red
        ):

            if obj:

                obj["x"] += x1
                obj["y"] += y1

                obj["cx"] += x1
                obj["cy"] += y1

        # ----------------------------------------------------
        # SELECT OBSTACLE
        # ----------------------------------------------------

        if green and red:

            if (
                green["area"]
                >= red["area"]
            ):

                return (
                    "GREEN",
                    green,
                    green_mask,
                    red_mask
                )

            return (
                "RED",
                red,
                green_mask,
                red_mask
            )

        if green:

            return (
                "GREEN",
                green,
                green_mask,
                red_mask
            )

        if red:

            return (
                "RED",
                red,
                green_mask,
                red_mask
            )

        return (
            "NO_OBSTACLE",
            None,
            green_mask,
            red_mask
        )


    # ========================================================
    # DIRECTION LINE DETECTION
    #
    # LARGE ROI ONLY FOR INITIAL DIRECTION LOCK
    # ========================================================

    def detect_direction_lines(
        self,
        frame
    ):

        x1, y1, x2, y2 = (
            DIRECTION_ROI
        )

        roi = frame[
            y1:y2,
            x1:x2
        ]

        roi = cv2.GaussianBlur(
            roi,
            (3, 3),
            0
        )

        hsv = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2HSV
        )

        # ----------------------------------------------------
        # ORANGE
        # ----------------------------------------------------

        orange_mask = self.color_mask(
            hsv,
            ORANGE_LOW,
            ORANGE_HIGH
        )

        # ----------------------------------------------------
        # BLUE
        # ----------------------------------------------------

        blue_mask = self.color_mask(
            hsv,
            BLUE_LOW,
            BLUE_HIGH
        )

        orange = self.largest_object(
            orange_mask,
            MIN_LINE_AREA
        )

        blue = self.largest_object(
            blue_mask,
            MIN_LINE_AREA
        )

        # Reject blue objects that look vertical
        if blue is not None:

            if (
                blue["h"]
                > blue["w"] * 1.5
            ):

                blue = None

        # ----------------------------------------------------
        # FULL-FRAME COORDINATES
        # ----------------------------------------------------

        if orange:

            orange["x"] += x1
            orange["y"] += y1

            orange["cx"] += x1
            orange["cy"] += y1

        if blue:

            blue["x"] += x1
            blue["y"] += y1

            blue["cx"] += x1
            blue["cy"] += y1

        return (
            orange,
            blue
        )


    # ========================================================
    # NORMAL LINE DETECTION
    #
    # NORMAL LINE_ROI FOR LAP COUNTING
    # ========================================================

    def detect_lines(
        self,
        frame
    ):

        x1, y1, x2, y2 = (
            LINE_ROI
        )

        roi = frame[
            y1:y2,
            x1:x2
        ]

        roi = cv2.GaussianBlur(
            roi,
            (3, 3),
            0
        )

        hsv = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2HSV
        )

        # ----------------------------------------------------
        # ORANGE
        # ----------------------------------------------------

        orange_mask = self.color_mask(
            hsv,
            ORANGE_LOW,
            ORANGE_HIGH
        )

        # ----------------------------------------------------
        # BLUE
        # ----------------------------------------------------

        blue_mask = self.color_mask(
            hsv,
            BLUE_LOW,
            BLUE_HIGH
        )

        orange = self.largest_object(
            orange_mask,
            MIN_LINE_AREA
        )

        blue = self.largest_object(
            blue_mask,
            MIN_LINE_AREA
        )

        # Reject blue objects that look like pillar
        if blue is not None:

            if (
                blue["h"]
                > blue["w"] * 1.5
            ):

                blue = None

        # ----------------------------------------------------
        # FULL-FRAME COORDINATES
        # ----------------------------------------------------

        if orange:

            orange["x"] += x1
            orange["y"] += y1

            orange["cx"] += x1
            orange["cy"] += y1

        if blue:

            blue["x"] += x1
            blue["y"] += y1

            blue["cx"] += x1
            blue["cy"] += y1

        return (
            orange,
            blue,
            orange_mask,
            blue_mask
        )


    # ========================================================
    # DIRECTION LOCK
    #
    # BOTH COLORS REQUIRED
    #
    # Larger Y = closer line
    #
    # ORANGE closer -> CLOCKWISE
    # BLUE closer   -> COUNTERCLOCKWISE
    # ========================================================

    def update_direction(
        self,
        orange,
        blue
    ):

        # Already locked
        if (
            self.direction
            != "UNKNOWN"
        ):

            return

        # ----------------------------------------------------
        # BOTH COLORS MUST BE VISIBLE
        # ----------------------------------------------------

        if (
            orange is None
            or blue is None
        ):

            self.first_color = None
            self.first_color_frames = 0

            return

        # ----------------------------------------------------
        # Y POSITION
        # ----------------------------------------------------

        orange_y = orange["cy"]
        blue_y = blue["cy"]

        gap = abs(
            orange_y - blue_y
        )

        # ----------------------------------------------------
        # TOO CLOSE = UNRELIABLE
        # ----------------------------------------------------

        if (
            gap
            < DIRECTION_MIN_GAP
        ):

            self.first_color = None
            self.first_color_frames = 0

            print(
                "[DIR] WAIT | GAP:",
                gap
            )

            return

        # ----------------------------------------------------
        # CLOSER LINE
        #
        # Larger Y means closer to bottom of image / robot
        # ----------------------------------------------------

        if (
            orange_y
            > blue_y
        ):

            current = "ORANGE"

        else:

            current = "BLUE"

        # ----------------------------------------------------
        # CONFIRM SAME RESULT
        # ----------------------------------------------------

        if (
            current
            == self.first_color
        ):

            self.first_color_frames += 1

        else:

            self.first_color = current
            self.first_color_frames = 1

        print(
            "[DIR]",
            current,
            self.first_color_frames,
            "/",
            DIRECTION_CONFIRM_FRAMES,
            "| O:",
            orange_y,
            "| B:",
            blue_y,
            "| GAP:",
            gap
        )

        # ----------------------------------------------------
        # WAIT FOR CONFIRMATION
        # ----------------------------------------------------

        if (
            self.first_color_frames
            < DIRECTION_CONFIRM_FRAMES
        ):

            return

        # ----------------------------------------------------
        # LOCK DIRECTION
        # ----------------------------------------------------

        if current == "ORANGE":

            self.direction = (
                "CLOCKWISE"
            )

        else:

            self.direction = (
                "COUNTERCLOCKWISE"
            )

        # Starting lines must clear
        # before normal counting starts
        self.waiting_for_start_clear = True

        print("")
        print(
            "=============================="
        )

        print(
            "[DIRECTION LOCKED]",
            self.direction
        )

        print(
            "=============================="
        )
        print("")


    # ========================================================
    # ENABLE LINE COUNTING
    # ========================================================

    def update_counting_state(
        self,
        orange,
        blue
    ):

        # Direction must be known
        if (
            self.direction
            == "UNKNOWN"
        ):

            return

        if self.counting_enabled:
            return

        # Wait for starting line to clear
        if (
            self.waiting_for_start_clear
            and orange is None
            and blue is None
        ):

            self.waiting_for_start_clear = False

            self.counting_enabled = True

            self.line_locked = False
            self.line_clear_frames = 0

            print(
                "[LINE COUNTING ENABLED]"
            )


    # ========================================================
    # LINE / LAP COUNTER
    #
    # ORANGE OR BLUE = ONE CROSSING
    # ========================================================

    def update_line_count(
        self,
        orange,
        blue
    ):

        if not self.counting_enabled:
            return False

        if self.race_complete:
            return False

        line_present = (
            orange is not None
            or blue is not None
        )

        # ----------------------------------------------------
        # LINE PRESENT
        # ----------------------------------------------------

        if line_present:

            self.line_clear_frames = 0

            # New crossing
            if not self.line_locked:

                self.line_count += 1

                self.line_locked = True

                # Debug detected color
                if (
                    orange is not None
                    and blue is not None
                ):

                    detected = (
                        "ORANGE+BLUE"
                    )

                elif orange is not None:

                    detected = (
                        "ORANGE"
                    )

                else:

                    detected = (
                        "BLUE"
                    )

                print(
                    "[LINE CROSSING]",
                    self.line_count,
                    "/",
                    TOTAL_LINE_COUNT,
                    "|",
                    detected
                )

                # --------------------------------------------
                # LAP COMPLETE
                # --------------------------------------------

                if (
                    self.line_count % 4
                    == 0
                ):

                    lap = (
                        self.line_count
                        // 4
                    )

                    print(
                        "[LAP COMPLETED]",
                        lap
                    )

                # --------------------------------------------
                # THREE LAPS COMPLETE
                # --------------------------------------------

                if (
                    self.line_count
                    >= TOTAL_LINE_COUNT
                ):

                    self.race_complete = True

                    print("")
                    print(
                        "=============================="
                    )

                    print(
                        "[3 LAPS COMPLETED]"
                    )

                    print(
                        "=============================="
                    )
                    print("")

                return True

            return False

        # ----------------------------------------------------
        # NO LINE
        # ----------------------------------------------------

        if self.line_locked:

            self.line_clear_frames += 1

            if (
                self.line_clear_frames
                >= LINE_CLEAR_FRAMES
            ):

                self.line_locked = False
                self.line_clear_frames = 0

                print(
                    "[LINE COUNTER ARMED]"
                )

        return False


    # ========================================================
    # NAVIGATION HINT
    # ========================================================

    def navigation_hint(
        self,
        front,
        left,
        right
    ):

        # ----------------------------------------------------
        # FRONT WALL PRIORITY
        # ----------------------------------------------------

        if (
            front
            > FRONT_WALL_HIGH
        ):

            if (
                self.direction
                == "CLOCKWISE"
            ):

                return "RIGHT_TURN"

            if (
                self.direction
                == "COUNTERCLOCKWISE"
            ):

                return "LEFT_TURN"

            return "FRONT_WALL"

        # ----------------------------------------------------
        # SIDE WALL CORRECTION
        # ----------------------------------------------------

        left_high = (
            left
            > SIDE_WALL_HIGH
        )

        right_high = (
            right
            > SIDE_WALL_HIGH
        )

        if (
            left_high
            and not right_high
        ):

            return "RIGHT_CORRECT"

        if (
            right_high
            and not left_high
        ):

            return "LEFT_CORRECT"

        return "STRAIGHT"


    # ========================================================
    # PROCESS
    # ========================================================

    def process(self):

        ok, frame = self.cap.read()

        if not ok:

            return {
                "ok": False
            }

        frame = cv2.resize(
            frame,
            (WIDTH, HEIGHT)
        )

        # ----------------------------------------------------
        # OBSTACLE
        # ----------------------------------------------------

        (
            obstacle,
            obstacle_data,
            green_mask,
            red_mask
        ) = self.detect_obstacle(
            frame
        )

        # ----------------------------------------------------
        # NORMAL LINE DETECTION
        # ----------------------------------------------------

        (
            orange,
            blue,
            orange_mask,
            blue_mask
        ) = self.detect_lines(
            frame
        )

        # ----------------------------------------------------
        # DIRECTION
        #
        # LARGE ROI USED ONLY UNTIL LOCKED
        # ----------------------------------------------------

        if (
            self.direction
            == "UNKNOWN"
        ):

            (
                dir_orange,
                dir_blue
            ) = self.detect_direction_lines(
                frame
            )

            self.update_direction(
                dir_orange,
                dir_blue
            )

        # ----------------------------------------------------
        # ENABLE COUNTING
        # ----------------------------------------------------

        self.update_counting_state(
            orange,
            blue
        )

        # ----------------------------------------------------
        # COUNT LINE
        # ----------------------------------------------------

        line_event = (
            self.update_line_count(
                orange,
                blue
            )
        )

        # ----------------------------------------------------
        # WALLS
        # ----------------------------------------------------

        (
            left,
            front,
            right,
            wall_mask
        ) = self.detect_walls(
            frame
        )

        # ----------------------------------------------------
        # FRONT STATUS
        # ----------------------------------------------------

        if (
            front
            > FRONT_WALL_HIGH
        ):

            front_state = (
                "FRONT_WALL"
            )

        else:

            front_state = (
                "FRONT_CLEAR"
            )

        # ----------------------------------------------------
        # NAVIGATION
        # ----------------------------------------------------

        navigation = (
            self.navigation_hint(
                front,
                left,
                right
            )
        )

        # ----------------------------------------------------
        # LAP STATUS
        # ----------------------------------------------------

        completed_laps = min(
            self.line_count // 4,
            3
        )

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return {

            "ok": True,

            # Direction
            "direction":
                self.direction,

            "direction_locked":
                self.direction
                != "UNKNOWN",

            # Obstacle
            "obstacle":
                obstacle,

            "obstacle_data":
                obstacle_data,

            # Colors
            "orange_detected":
                orange is not None,

            "blue_detected":
                blue is not None,

            "orange_data":
                orange,

            "blue_data":
                blue,

            # Line / Lap
            "line_count":
                self.line_count,

            "line_event":
                line_event,

            "counting_enabled":
                self.counting_enabled,

            "line_locked":
                self.line_locked,

            "completed_laps":
                completed_laps,

            "race_complete":
                self.race_complete,

            # Walls
            "left_wall":
                round(left, 3),

            "front_wall":
                round(front, 3),

            "right_wall":
                round(right, 3),

            "front_state":
                front_state,

            # Navigation
            "navigation":
                navigation,

            # Frame
            "frame":
                frame,

            # Masks
            "wall_mask":
                wall_mask,

            "orange_mask":
                orange_mask,

            "blue_mask":
                blue_mask,

            "red_mask":
                red_mask,

            "green_mask":
                green_mask
        }


    # ========================================================
    # DRAW ROI
    # ========================================================

    def draw_roi(
        self,
        frame,
        roi,
        label,
        color
    ):

        x1, y1, x2, y2 = roi

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.putText(
            frame,
            label,
            (
                x1 + 5,
                y1 + 18
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            color,
            1
        )


    # ========================================================
    # DRAW OBJECT
    # ========================================================

    def draw_object(
        self,
        frame,
        obj,
        label,
        color
    ):

        if obj is None:
            return

        x1 = obj["x"]
        y1 = obj["y"]

        x2 = (
            x1 + obj["w"]
        )

        y2 = (
            y1 + obj["h"]
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        cv2.circle(
            frame,
            (
                obj["cx"],
                obj["cy"]
            ),
            5,
            color,
            -1
        )

        cv2.putText(
            frame,
            label,
            (
                x1,
                max(
                    20,
                    y1 - 5
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            2
        )


    # ========================================================
    # DEBUG DISPLAY
    # ========================================================

    def draw_debug(
        self,
        frame,
        data
    ):

        # ----------------------------------------------------
        # WALL ROIs
        # ----------------------------------------------------

        self.draw_roi(
            frame,
            LEFT_ROI,
            "L "
            + str(
                data["left_wall"]
            ),
            (255, 255, 255)
        )

        self.draw_roi(
            frame,
            FRONT_ROI,
            "FRONT "
            + str(
                data["front_wall"]
            ),
            (255, 255, 255)
        )

        self.draw_roi(
            frame,
            RIGHT_ROI,
            "R "
            + str(
                data["right_wall"]
            ),
            (255, 255, 255)
        )

        # ----------------------------------------------------
        # OBSTACLE ROI
        # ----------------------------------------------------

        self.draw_roi(
            frame,
            OBSTACLE_ROI,
            "OBSTACLE",
            (0, 255, 255)
        )

        # ----------------------------------------------------
        # DIRECTION ROI
        #
        # DISPLAY ONLY WHILE UNKNOWN
        # ----------------------------------------------------

        if (
            data["direction"]
            == "UNKNOWN"
        ):

            self.draw_roi(
                frame,
                DIRECTION_ROI,
                "DIRECTION",
                (255, 0, 255)
            )

        # ----------------------------------------------------
        # NORMAL LINE ROI
        # ----------------------------------------------------

        self.draw_roi(
            frame,
            LINE_ROI,
            "LINE",
            (255, 255, 0)
        )

        # ----------------------------------------------------
        # LINE OBJECTS
        # ----------------------------------------------------

        self.draw_object(
            frame,
            data["orange_data"],
            "ORANGE",
            (0, 165, 255)
        )

        self.draw_object(
            frame,
            data["blue_data"],
            "BLUE",
            (255, 0, 0)
        )

        # ----------------------------------------------------
        # OBSTACLE
        # ----------------------------------------------------

        if (
            data["obstacle"]
            == "GREEN"
        ):

            obstacle_color = (
                0, 255, 0
            )

        else:

            obstacle_color = (
                0, 0, 255
            )

        self.draw_object(
            frame,
            data["obstacle_data"],
            data["obstacle"],
            obstacle_color
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        cv2.putText(
            frame,
            "DIR: "
            + data["direction"],
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "NAV: "
            + data["navigation"],
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "OBS: "
            + data["obstacle"],
            (10, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "LINES: "
            + str(
                data["line_count"]
            )
            + "/12",
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "LAPS: "
            + str(
                data["completed_laps"]
            )
            + "/3",
            (10, 125),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            data["front_state"],
            (10, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2
        )

        return frame


    # ========================================================
    # PRINT STATUS
    # ========================================================

    def print_status(
        self,
        data
    ):

        print(

            "DIR:",
            data["direction"],

            "| NAV:",
            data["navigation"],

            "| OBS:",
            data["obstacle"],

            "| ORANGE:",
            data["orange_detected"],

            "| BLUE:",
            data["blue_detected"],

            "| L:",
            data["left_wall"],

            "| F:",
            data["front_wall"],

            "| R:",
            data["right_wall"],

            "| LINE:",
            data["line_count"],

            "| LAP:",
            data["completed_laps"],

            "| COMPLETE:",
            data["race_complete"]
        )


    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.cap.release()

        cv2.destroyAllWindows()

        print(
            "[VISION] Closed"
        )


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    vision = Vision()

    try:

        while True:

            data = vision.process()

            if not data["ok"]:

                print(
                    "[ERROR] Camera failed"
                )

                break

            # ------------------------------------------------
            # TERMINAL
            # ------------------------------------------------

            vision.print_status(
                data
            )

            # ------------------------------------------------
            # CAMERA
            # ------------------------------------------------

            debug = vision.draw_debug(
                data["frame"].copy(),
                data
            )

            cv2.imshow(
                "WRO Vision",
                debug
            )

            # ------------------------------------------------
            # CALIBRATION MASKS
            # ------------------------------------------------

            cv2.imshow(
                "Blue Mask",
                data["blue_mask"]
            )

            cv2.imshow(
                "Orange Mask",
                data["orange_mask"]
            )

            cv2.imshow(
                "Red Mask",
                data["red_mask"]
            )

            cv2.imshow(
                "Wall Mask",
                data["wall_mask"]
            )

            # ------------------------------------------------
            # QUIT
            # ------------------------------------------------

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            if key == ord("q"):
                break

    except KeyboardInterrupt:

        print(
            "\n[VISION] Interrupted"
        )

    finally:

        vision.close()
