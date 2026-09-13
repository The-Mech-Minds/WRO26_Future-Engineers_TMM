Combined test: centers the steering servo before the motors start, then
drives forward while sweeping steering left and right. Uses the verified
forward-motor mapping and the final steering calibration values together
for the first time (earlier tests in motor_test.py and
servo_calibration.py check each subsystem in isolation).
 
Run with the wheels lifted off the ground first; only move to floor testing
once this passes.
 
Run:
    python3 combined_drive_test.py
"""
 
import lgpio
import time
 
AIN1 = 17
AIN2 = 27
BIN1 = 22
BIN2 = 23
STBY = 24
SERVO = 18
 
STEER_RIGHT = 850
STEER_CENTER = 1000
STEER_LEFT = 1150
 
 
def setup():
    h = lgpio.gpiochip_open(0)
    for pin in [AIN1, AIN2, BIN1, BIN2, STBY, SERVO]:
        lgpio.gpio_claim_output(h, pin)
    return h
 
 
def forward(h):
    lgpio.gpio_write(h, AIN1, 0)
    lgpio.gpio_write(h, AIN2, 1)
    lgpio.gpio_write(h, BIN1, 1)
    lgpio.gpio_write(h, BIN2, 0)
 
 
def stop(h):
    lgpio.gpio_write(h, AIN1, 0)
    lgpio.gpio_write(h, AIN2, 0)
    lgpio.gpio_write(h, BIN1, 0)
    lgpio.gpio_write(h, BIN2, 0)
 
 
def center(h):
    lgpio.tx_servo(h, SERVO, STEER_CENTER)
 
 
def steer_left(h):
    lgpio.tx_servo(h, SERVO, STEER_LEFT)
 
 
def steer_right(h):
    lgpio.tx_servo(h, SERVO, STEER_RIGHT)
 
 
def run(h):
    print("CENTERING SERVO")
    center(h)
    time.sleep(2)
 
    lgpio.gpio_write(h, STBY, 1)
    forward(h)
 
    print("FORWARD - CENTER")
    time.sleep(3)
 
    print("FORWARD - LEFT")
    steer_left(h)
    time.sleep(2)
 
    print("FORWARD - CENTER")
    center(h)
    time.sleep(2)
 
    print("FORWARD - RIGHT")
    steer_right(h)
    time.sleep(2)
 
    print("FORWARD - CENTER")
    center(h)
    time.sleep(2)
 
 
if __name__ == "__main__":
    h = setup()
    try:
        run(h)
    finally:
        stop(h)
        center(h)
        time.sleep(1)
        lgpio.tx_servo(h, SERVO, 0)
        lgpio.gpio_write(h, STBY, 0)
        lgpio.gpiochip_close(h)
