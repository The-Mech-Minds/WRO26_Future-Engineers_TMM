#!/usr/bin/env python3

import os
from buildhat import Motor


STEERING_PORT = os.getenv("TMM_STEERING_PORT", "A")
DRIVE_PORT = os.getenv("TMM_DRIVE_PORT", "B")
CENTER_ANGLE = int(os.getenv("TMM_CENTER_ANGLE", "0"))
TURN_ANGLE = int(os.getenv("TMM_TURN_ANGLE", "25"))
CORRECTION_ANGLE = int(os.getenv("TMM_CORRECTION_ANGLE", "10"))
STEERING_SPEED = int(os.getenv("TMM_STEERING_SPEED", "30"))
DRIVE_SPEED = int(os.getenv("TMM_DRIVE_SPEED", "20"))
STEERING_DIRECTION = int(os.getenv("TMM_STEERING_DIRECTION", "1"))


class Vehicle:
    def __init__(self):
        if not (-180 <= CENTER_ANGLE - TURN_ANGLE and CENTER_ANGLE + TURN_ANGLE <= 180):
            raise ValueError("Steering targets must stay within -180 to 180 degrees")
        if not 0 < STEERING_SPEED <= 100 or not -100 <= DRIVE_SPEED <= 100:
            raise ValueError("Motor speeds must stay within the Build HAT limits")
        if not 0 < CORRECTION_ANGLE <= TURN_ANGLE or STEERING_DIRECTION not in (-1, 1):
            raise ValueError("Invalid steering configuration")

        self.steering = Motor(STEERING_PORT)
        self.drive = Motor(DRIVE_PORT)
        self._target = None
        self._driving = False

    def _steer(self, offset):
        target = CENTER_ANGLE + offset * STEERING_DIRECTION
        if target != self._target:
            self.steering.run_to_position(target, speed=STEERING_SPEED, blocking=False)
            self._target = target
        if not self._driving and DRIVE_SPEED:
            self.drive.start(DRIVE_SPEED)
            self._driving = True

    def straight(self):
        self._steer(0)

    def left(self):
        self._steer(-TURN_ANGLE)

    def right(self):
        self._steer(TURN_ANGLE)

    def left_correct(self):
        self._steer(-CORRECTION_ANGLE)

    def right_correct(self):
        self._steer(CORRECTION_ANGLE)

    def stop(self):
        self.drive.stop()
        self.steering.stop()
        self._driving = False
        self._target = None

    def center(self):
        if self._target != CENTER_ANGLE:
            self.steering.run_to_position(CENTER_ANGLE, speed=STEERING_SPEED, blocking=False)
            self._target = CENTER_ANGLE
