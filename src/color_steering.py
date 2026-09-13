Camera-only test of the obstacle color-detection and steering-decision
logic (no motors/servo driven here -- see autonomous_main.py for the full
integrated version). Useful for tuning HSV ranges and MIN_AREA against the
actual competition lighting without risking the robot moving.
 
Decision logic:
    GREEN detected  -> "turn LEFT"
    RED detected    -> "turn RIGHT"
    neither         -> "go STRAIGHT"
 
Notes:
- HSV is used instead of RGB because it separates color (hue) from
  lighting/brightness, so detection is more stable across venues.
- Red requires two HSV ranges because red sits at both ends (0 and 180) of
  OpenCV's hue scale.
- Only the lower half of the frame is analyzed (see ROI below) to reduce
  noise from the upper field of view and lens distortion at the edges.
- MIN_AREA filters out small false-positive detections (reflections, stray
  pixels) -- tune this value alongside the HSV ranges under real lighting.
 
Run:
    python3 color_steering.py
Press 'q' in the preview window to quit.
"""
 
import os
os.environ["OPENCV_VIDEOIO_PRIORITY_BACKEND"] = "0"
 
import cv2
import numpy as np
 
CAMERA_INDEX = 0
 
RED1_LO = np.array([0, 120, 70], np.uint8)
RED1_HI = np.array([10, 255, 255], np.uint8)
RED2_LO = np.array([170, 120, 70], np.uint8)
RED2_HI = np.array([180, 255, 255], np.uint8)
GREEN_LO = np.array([35, 80, 80], np.uint8)
GREEN_HI = np.array([85, 255, 255], np.uint8)
MIN_AREA = 500
 
 
def classify(frame):
    """Return (decision_string, annotated_frame) for one camera frame."""
    roi = frame[240:480, 0:640]  # lower-half region of interest
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
 
    if green_area > MIN_AREA and green_area > red_area:
        decision = "GREEN -> LEFT"
    elif red_area > MIN_AREA and red_area > green_area:
        decision = "RED -> RIGHT"
    else:
        decision = "STRAIGHT"
 
    cv2.putText(frame, decision, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return decision, frame
 
 
def main():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
 
    if not cap.isOpened():
        raise SystemExit("Could not open USB camera -- check CAMERA_INDEX and cabling")
 
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            decision, annotated = classify(frame)
            print(decision)
            cv2.imshow("Color Steering Test", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
 
 
if __name__ == "__main__":
    main()
