#!/usr/bin/env python3

import time
import cv2
from buildhat import ForceSensor

from vehicle import Vehicle
from vision import Vision

vision = Vision()
vehicle = Vehicle()
button = ForceSensor("C")


def show_video(data):
    frame = data["frame"].copy()
    frame = vision.draw_debug(frame, data)
    cv2.imshow("WRO LIVE", frame)
    key = cv2.waitKey(1) & 0xFF
    return key != ord("q")


print("Press button to start...")
vehicle.stop()

while not button.is_pressed():
    data = vision.process()
    if data["ok"] and not show_video(data):
        raise SystemExit
    time.sleep(0.02)

print("START")

while button.is_pressed():
    data = vision.process()
    if data["ok"]:
        show_video(data)
    time.sleep(0.02)

try:
    while True:
        if button.is_pressed():
            print("STOP BUTTON PRESSED")
            break

        data = vision.process()
        if not data["ok"] or not show_video(data):
            print("Q PRESSED OR VISION ERROR -> STOP")
            break

        direction = data["direction"]
        front = data["front_state"]
        front_ratio = data["front_wall"]
        obstacle = data["obstacle"]

        if data["race_complete"]:
            print("3 LAPS COMPLETED")
            vehicle.straight()
            time.sleep(0.5)
            print("STOP")
            break

        if obstacle == "GREEN":
            print("GREEN -> LEFT")
            vehicle.left()

        elif obstacle == "RED":
            print("RED -> RIGHT")
            vehicle.right()

        elif front == "FRONT_WALL":
            print("FRONT WALL -> TURN")
            turn_action = vehicle.right if direction == "CLOCKWISE" else vehicle.left

            while True:
                turn_action()
                data = vision.process()

                if not data["ok"] or not show_video(data) or button.is_pressed():
                    raise KeyboardInterrupt

                if data["race_complete"]:
                    vehicle.straight()
                    time.sleep(0.5)
                    raise KeyboardInterrupt

                if data["front_state"] == "FRONT_CLEAR":
                    break

            vehicle.straight()

        else:
            navigation = data["navigation"]
            if navigation == "LEFT_CORRECT":
                vehicle.left_correct()
            elif navigation == "RIGHT_CORRECT":
                vehicle.right_correct()
            else:
                vehicle.straight()

        print(
            f"DIR: {direction} | FRONT: {front} | F: {front_ratio} | OBS: {obstacle} | LINE: {data['line_count']}"
        )

except KeyboardInterrupt:
    print("STOP")

finally:
    vehicle.stop()
    vehicle.center()
    vision.close()
    cv2.destroyAllWindows()
