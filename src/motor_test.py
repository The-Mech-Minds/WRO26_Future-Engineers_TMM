Standalone GPIO test for the drive motors, run directly on the Pi with the
driven wheels lifted off the ground.
 
Pin mapping (see README section 7 "GPIO Pin Assignment"):
    AIN1 = GPIO17 (physical pin 11)
    AIN2 = GPIO27 (physical pin 13)
    BIN1 = GPIO22 (physical pin 15)
    BIN2 = GPIO23 (physical pin 16)
    STBY = GPIO24 (physical pin 18)
 
IMPORTANT: physical-forward mapping.
Early testing with AIN1=1/AIN2=0 drove the chassis backward relative to its
mounting orientation. The verified forward mapping used everywhere else in
this project is:
    AIN1=0, AIN2=1   (Motor A forward)
    BIN1=1, BIN2=0   (Motor B forward)
Any new script must match this mapping or the robot will reverse direction.
 
Run:
    python3 motor_test.py
"""
 
import lgpio
import time
 
AIN1 = 17
AIN2 = 27
BIN1 = 22
BIN2 = 23
STBY = 24
 
PINS = [AIN1, AIN2, BIN1, BIN2, STBY]
 
 
def setup():
    h = lgpio.gpiochip_open(0)
    for pin in PINS:
        lgpio.gpio_claim_output(h, pin)
    return h
 
 
def stop(h):
    for pin in [AIN1, AIN2, BIN1, BIN2]:
        lgpio.gpio_write(h, pin, 0)
 
 
def one_motor_test(h):
    """Sanity-check Motor A alone: forward, stop, reverse."""
    try:
        lgpio.gpio_write(h, STBY, 1)
 
        print("Motor A forward")
        lgpio.gpio_write(h, AIN1, 0)
        lgpio.gpio_write(h, AIN2, 1)
        time.sleep(2)
 
        print("Stop")
        stop(h)
        time.sleep(1)
 
        print("Motor A reverse")
        lgpio.gpio_write(h, AIN1, 1)
        lgpio.gpio_write(h, AIN2, 0)
        time.sleep(2)
    finally:
        stop(h)
        lgpio.gpio_write(h, STBY, 0)
 
 
def both_motors_test(h):
    """Drive both motors together using the verified forward mapping."""
    try:
        lgpio.gpio_write(h, STBY, 1)
        print("Both motors FORWARD")
        lgpio.gpio_write(h, AIN1, 0)
        lgpio.gpio_write(h, AIN2, 1)
        lgpio.gpio_write(h, BIN1, 1)
        lgpio.gpio_write(h, BIN2, 0)
        time.sleep(3)
    finally:
        stop(h)
        lgpio.gpio_write(h, STBY, 0)
 
 
if __name__ == "__main__":
    h = setup()
    try:
        one_motor_test(h)
        time.sleep(1)
        both_motors_test(h)
    finally:
        lgpio.gpiochip_close(h)
