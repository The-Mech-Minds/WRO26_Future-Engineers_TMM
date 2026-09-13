Standalone servo test used to find and verify safe steering pulse-width
values, run with the wheels lifted off the ground.
 
Pin mapping:
    SERVO signal = GPIO18 (physical pin 12)
 
IMPORTANT: calibration history.
Earlier values (RIGHT=700, CENTER=1000, LEFT=1300) pushed the servo close to
its mechanical end stops. Final, safer values used everywhere else in this
project:
    STEER_RIGHT  = 850
    STEER_CENTER = 1000
    STEER_LEFT   = 1150
 
Note: lgpio.tx_servo(h, SERVO, 0) stops pulse output -- it does NOT command a
0-degree angle. Always re-center the servo before cutting the signal.
 
Run:
    python3 servo_calibration.py
"""
 
import lgpio
import time
 
SERVO = 18
 
STEER_RIGHT = 850
STEER_CENTER = 1000
STEER_LEFT = 1150
 
 
def setup():
    h = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(h, SERVO)
    return h
 
 
def sweep_test(h):
    """Move through center -> left -> center -> right -> center."""
    print("CENTER")
    lgpio.tx_servo(h, SERVO, STEER_CENTER)
    time.sleep(2)
 
    print("LEFT")
    lgpio.tx_servo(h, SERVO, STEER_LEFT)
    time.sleep(2)
 
    print("CENTER")
    lgpio.tx_servo(h, SERVO, STEER_CENTER)
    time.sleep(2)
 
    print("RIGHT")
    lgpio.tx_servo(h, SERVO, STEER_RIGHT)
    time.sleep(2)
 
    print("CENTER")
    lgpio.tx_servo(h, SERVO, STEER_CENTER)
    time.sleep(2)
 
 
if __name__ == "__main__":
    h = setup()
    try:
        sweep_test(h)
    finally:
        # Re-center before cutting the pulse -- see note above.
        lgpio.tx_servo(h, SERVO, STEER_CENTER)
        time.sleep(0.5)
        lgpio.tx_servo(h, SERVO, 0)
        lgpio.gpiochip_close(h)
 
