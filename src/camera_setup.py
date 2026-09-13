Basic USB camera test using OpenCV. Confirms the camera is detected and
streaming before any color-detection logic is layered on top.
 
Before running, confirm the camera is visible to Linux:
    lsusb
    ls /dev/video*
    v4l2-ctl --list-devices
    v4l2-ctl --device=/dev/video0 --list-formats-ext
 
IMPORTANT: the device index below (0) matches whatever /dev/videoN number
the camera is assigned -- this can change between boots/USB ports. Re-check
it before every run and update CAMERA_INDEX if needed (see README section 12
"Pre-Run Checklist").
 
Requires a display (VNC desktop) to show the preview window -- does not
work over a plain SSH terminal session.
 
Run:
    python3 camera_setup.py
Press 'q' in the preview window to quit.
"""
 
import os
os.environ["OPENCV_VIDEOIO_PRIORITY_BACKEND"] = "0"
 
import cv2
 
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FRAME_FPS = 30
 
 
def main():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FRAME_FPS)
 
    if not cap.isOpened():
        raise SystemExit("Could not open USB camera -- check CAMERA_INDEX and cabling")
 
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("USB Camera", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
 
 
if __name__ == "__main__":
    main()
 
