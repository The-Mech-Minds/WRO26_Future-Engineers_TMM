import cv2
import numpy as np
import serial
import time

uart = serial.Serial('/dev/serial0', 9600, timeout=0.1)
time.sleep(2)

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    uart.close()
    exit()

kernel = np.ones((5, 5), np.uint8)

blue_line_count = 0
lap_count = 0
last_blue_time = 0
BLUE_COOLDOWN = 1.5
line_was_visible = False

STEER_LEFT = 1750
STEER_CENTER = 1880
STEER_RIGHT = 2150

last_valid_turn = "CENTER"
turn_memory_time = 0
TURN_MEMORY_DURATION = 0.4

red_lower1 = np.array([0, 160, 100], np.uint8)
red_upper1 = np.array([6, 255, 255], np.uint8)
red_lower2 = np.array([172, 160, 100], np.uint8)
red_upper2 = np.array([180, 255, 255], np.uint8)

green_lower = np.array([35, 100, 100], np.uint8)
green_upper = np.array([85, 255, 255], np.uint8)

blue_lower = np.array([100, 150, 50], np.uint8)
blue_upper = np.array([140, 255, 255], np.uint8)

WALL_THRESHOLD = 120
MIN_CONTOUR_AREA = 400
OBSTACLE_MIN_AREA = 700

parking_state = 0
parking_timer = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h_frame, w_frame, _ = frame.shape
        roi_top = int(h_frame * 0.50)
        margin = 0

        roi = frame[roi_top:h_frame, margin:w_frame - margin]
        roi_h, roi_w, _ = roi.shape
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        blue_mask = cv2.inRange(hsv_roi, blue_lower, blue_upper)
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_OPEN, kernel)
        contours_blue, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        line_currently_visible = False
        for cnt in contours_blue:
            if cv2.contourArea(cnt) > 800:
                line_currently_visible = True
                break

        current_time = time.time()

        if line_currently_visible and not line_was_visible and (current_time - last_blue_time > BLUE_COOLDOWN):
            blue_line_count += 1
            last_blue_time = current_time
            lap_count = blue_line_count // 4

            if blue_line_count >= 12 and parking_state == 0:
                parking_state = 1
                parking_timer = current_time

        line_was_visible = line_currently_visible

        if parking_state > 0:
            elapsed = current_time - parking_timer

            if parking_state == 1:
                servo_val = STEER_CENTER
                motor_val = 40
                if elapsed > 1.2:
                    parking_state = 2
                    parking_timer = current_time

            elif parking_state == 2:
                servo_val = STEER_CENTER
                motor_val = -40
                if elapsed > 0.8:
                    parking_state = 3
                    parking_timer = current_time

            elif parking_state == 3:
                servo_val = STEER_LEFT
                motor_val = -35
                if elapsed > 1.0:
                    parking_state = 4
                    parking_timer = current_time

            elif parking_state == 4:
                servo_val = STEER_RIGHT
                motor_val = -30
                if elapsed > 0.8:
                    parking_state = 5

            elif parking_state == 5:
                servo_val = STEER_CENTER
                motor_val = 0
                command_str = f"{servo_val},{motor_val}\n"
                uart.write(command_str.encode('utf-8'))
                break

        else:
            mask_red1 = cv2.inRange(hsv_roi, red_lower1, red_upper1)
            mask_red2 = cv2.inRange(hsv_roi, red_lower2, red_upper2)
            red_mask = cv2.bitwise_or(mask_red1, mask_red2)
            red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

            green_mask = cv2.inRange(hsv_roi, green_lower, green_upper)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)

            contours_red, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours_green, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            largest_red_area = max([cv2.contourArea(c) for c in contours_red], default=0)
            largest_green_area = max([cv2.contourArea(c) for c in contours_green], default=0)

            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray_roi, WALL_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

            contours_walls, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            left_wall_max_x = 0
            right_wall_min_x = roi_w
            left_detected = False
            right_detected = False
            front_wall_detected = False
            mid_x = roi_w // 2

            for cnt in contours_walls:
                area = cv2.contourArea(cnt)
                if area > MIN_CONTOUR_AREA:
                    x, y, w, th = cv2.boundingRect(cnt)
                    cx = x + w // 2

                    if y < 5 and w > (roi_w * 0.75) and area > 2000:
                        front_wall_detected = True

                    if cx < mid_x:
                        right_edge = x + w
                        if right_edge > left_wall_max_x:
                            left_wall_max_x = right_edge
                            left_detected = True
                    else:
                        left_edge = x
                        if left_edge < right_wall_min_x:
                            right_wall_min_x = left_edge
                            right_detected = True

            servo_val = STEER_CENTER
            motor_val = 0

            if largest_green_area > OBSTACLE_MIN_AREA and largest_green_area > largest_red_area:
                servo_val = STEER_LEFT
                motor_val = 65
                last_valid_turn = "LEFT"
                turn_memory_time = current_time
            elif largest_red_area > OBSTACLE_MIN_AREA and largest_red_area > largest_green_area:
                servo_val = STEER_RIGHT
                motor_val = 65
                last_valid_turn = "RIGHT"
                turn_memory_time = current_time
            elif front_wall_detected:
                servo_val = STEER_RIGHT
                motor_val = 60
                last_valid_turn = "RIGHT"
                turn_memory_time = current_time
            elif left_detected and right_detected:
                calculated_center = (left_wall_max_x + right_wall_min_x) // 2
                error = calculated_center - mid_x
                proportional_steer = STEER_CENTER + int(error * 1.2)
                servo_val = max(STEER_LEFT, min(STEER_RIGHT, proportional_steer))
                motor_val = 80
                last_valid_turn = "CENTER"
            elif left_detected and not right_detected:
                servo_val = STEER_RIGHT
                motor_val = 70
                last_valid_turn = "RIGHT"
                turn_memory_time = current_time
            elif right_detected and not left_detected:
                servo_val = STEER_LEFT
                motor_val = 70
                last_valid_turn = "LEFT"
                turn_memory_time = current_time
            else:
                if current_time - turn_memory_time < TURN_MEMORY_DURATION:
                    if last_valid_turn == "RIGHT":
                        servo_val = STEER_RIGHT
                        motor_val = 70
                    elif last_valid_turn == "LEFT":
                        servo_val = STEER_LEFT
                        motor_val = 70
                    else:
                        servo_val = STEER_CENTER
                        motor_val = 75
                else:
                    servo_val = STEER_CENTER
                    motor_val = 75

        command_str = f"{servo_val},{motor_val}\n"
        uart.write(command_str.encode('utf-8'))

finally:
    uart.write(f"{STEER_CENTER},0\n".encode('utf-8'))
    cap.release()
    cv2.destroyAllWindows()
    uart.close()
