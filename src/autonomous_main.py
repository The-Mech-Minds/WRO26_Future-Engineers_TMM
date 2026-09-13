Integrated autonomous program: both motors drive forward, the camera
detects red/green obstacles, and the servo steers accordingly. This is a
reactive baseline -- it does not yet implement full wall tracking, lap
counting, or corner-state logic.
 
Startup sequence:
    1. Center the steering servo.
    2. Wait for the competition Start button to be pressed (see
       wait_for_start_button() below -- required by WRO general rules
       9.10-9.14: the vehicle must power on, sit idle, and only begin
       moving on a physical button press timed to the judge's "Go").
    3. Enable the motor driver (STBY) and begin the drive + detection loop.
 
TODO (team): wait_for_start_button() is a placeholder. Wire an actual GPIO
push button (or whichever button is used) and set START_BUTTON_PIN below
before relying on this at competition -- right now it is NOT yet reading a
real button.
 
Run:
    python3 autonomous_main.py
Press 'q' in the preview window to quit (requires a display / VNC session).
"""
 
import os
os.environ["OPENCV_VIDEOIO_PRIORITY_BACKEND"] = "0"
 
import cv2
import numpy as np
import lgpio
import time
 
AIN1, AIN2 = 17, 27
BIN1, BIN2 = 22, 23
STBY = 24
SERVO = 18
 
# TODO (team): set this to the actual GPIO pin wired to the start button.
START_BUTTON_PIN = None
 
STEER_RIGHT = 850
STEER_CENTER = 1000
STEER_LEFT = 1150
 
RED1_LO = np.array([0, 120, 70], np.uint8)
RED1_HI = np.array([10, 255, 255], np.uint8)
RED2_LO = np.array([170, 120, 70], np.uint8)
RED2_HI = np.array([180, 255, 255], np.uint8)
GREEN_LO = np.array([35, 80, 80], np.uint8)
GREEN_HI = np.array([85, 255, 255], np.uint8)
MIN_AREA = 500
 
 
def setup_gpio():
    h = lgpio.gpiochip_open(0)
    for pin in [AIN1, AIN2, BIN1, BIN2, STBY, SERVO]:
        lgpio.gpio_claim_output(h, pin)
    if START_BUTTON_PIN is not None:
        lgpio.gpio_claim_input(h, START_BUTTON_PIN)
    return h
 
 
def forward(h):
    lgpio.gpio_write(h, AIN1, 0)
    lgpio.gpio_write(h, AIN2, 1)
    lgpio.gpio_write(h, BIN1, 1)
    lgpio.gpio_write(h, BIN2, 0)
 
 
def stop(h):
    for pin in [AIN1, AIN2, BIN1, BIN2]:
        lgpio.gpio_write(h, pin, 0)
 
 
def wait_for_start_button(h):
    """
    Block until the competition Start button is pressed (WRO rule 9.11:
    the vehicle must sit in a waiting state after power-on until this
    press occurs). PLACEHOLDER until START_BUTTON_PIN is wired -- currently
    falls back to a short fixed delay so the script is still runnable for
    bench testing.
    """
    if START_BUTTON_PIN is None:
        print("WARNING: no start button wired yet -- using fallback delay only.")
        time.sleep(3)
        return
 
    print("Waiting for start button press...")
    while lgpio.gpio_read(h, START_BUTTON_PIN) == 0:
        time.sleep(0.05)
    print("Start button pressed -- beginning run.")
 
 
def classify(frame):
    roi = frame[240:480, 0:640]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
 
    red_mask = cv2.bitwise_or(
        cv2.inRange(hsv, RED1_LO, RED1_HI),
        cv2.inRange(hsv, RED2_LO, RED2_HI),
    )
    green_mask = cv2.inRange(hsv, GREEN_LO, GREEN_HI)
 
    red_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
 
    red_area = max([cv2.contourArea(c) for c in red_contours], default=0)
    green_area = max([cv2.contourArea(c) for c in green_contours], default=0)
    return red_area, green_area
 
 
def main():
    h = setup_gpio()
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
 
    try:
        lgpio.tx_servo(h, SERVO, STEER_CENTER)
        time.sleep(2)
 
        wait_for_start_button(h)
 
        lgpio.gpio_write(h, STBY, 1)
        forward(h)
 
        while True:
            ret, frame = cap.read()
            if not ret:
                break
 
            red_area, green_area = classify(frame)
 
            if green_area > MIN_AREA and green_area > red_area:
                lgpio.tx_servo(h, SERVO, STEER_LEFT)
                decision = "GREEN -> LEFT"
            elif red_area > MIN_AREA and red_area > green_area:
                lgpio.tx_servo(h, SERVO, STEER_RIGHT)
                decision = "RED -> RIGHT"
            else:
                lgpio.tx_servo(h, SERVO, STEER_CENTER)
                decision = "STRAIGHT"
 
            print(decision)
            cv2.putText(frame, decision, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imshow("WRO Autonomous", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        stop(h)
        lgpio.tx_servo(h, SERVO, STEER_CENTER)
        time.sleep(0.5)
        lgpio.tx_servo(h, SERVO, 0)
        lgpio.gpio_write(h, STBY, 0)
        lgpio.gpiochip_close(h)
        cap.release()
        cv2.destroyAllWindows()
 
 
if __name__ == "__main__":
    main()
