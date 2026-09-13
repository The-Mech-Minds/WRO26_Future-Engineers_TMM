# WRO26_Future-Engineers_TMM
Raspberry Pi-based self-driving robot built by Team TMM for the WRO Future Engineers category. First place at the WRO Oman National Qualifiers; competing at the WRO Open Championship Asia & Pacific 2026 in Hyderabad, India.

Team members: 
Ahmed Suleiman, Ismail Nassor, & Hajer Al Salmani. 
Coach: Alex Savariyar.

Table of contents:
1. system Overview.
2. Hardware Components.
3. Power System & Safety.
4. Wiring.
5. Raspberry Pi Setup.
6. Software Environmnet.
7. GPIO Pin Assignment.
8. Design Decisions & Iteration.
9. Autonomous Driving Strategy.
10. Running Autonomously at Boot.
11. Safe Shutdown.
12. Pre-Run Checklist.
13. Troubleshooting.
14. Repository Structure.

1. System Overview:
USB Camera → Raspberry Pi 4B:
GPIO → Motor Driver → Motor A + Motor B
GPIO18 → Steering Servo
power:
- 30W power bank → Raspberry Pi
- 7.4V battery → Motor driver VM/GND
- 5-6V BEC/buck → Servo +/-
- All grounds → common ground
The robot uses a single forward-facing USB camera for obstacle detection, a dual-channel DC motor driver for propulsion, and a hobby servo for front-wheel (Ackerman-style) steering. The Raspberry Pi 4B runs the full control loop camera capture, color classification, and GPIO output onboard, with no external components.

2. Hardware components:
   - Controller: Raspberry Pi 4B - Runs python, OpenCV, motor and servo control.
   - Camera: USB 640x480, 30 fps, ~130° wide angle - Obstacle/wall/color detection.
   - Motor driver: TB6612-type dual DC motor driver board - controls two DC motors.
   - Drive motors: 2 x DC motors - Robot propulsion.
   - Steering: 3-wire hobby servo - Front-wheel steering.
   - Pi power: 30W USB power banks, 5V/3A output - Stable Raspberry Pi supply.
   - Motor power: 7.4V battery - Motor-driver VM supply.
   - Servo power: 5-6V regulated BEC/buck supply - Servo power without stressing the Pi rail.

  3. Power System & Safty
     - A 30W power bank is sufficient for the Pi 4B, provided it supplies 5V/3A.
     - Never connect the 7.4V battery directly to a Raspberry Pi 5V pin. The power bank powers the Pi; the 7.4V battery is used only for the motor-driver VM input.
     - Do not power a standard 5-6V servo directly from 7.4V unless that servo is explicitly rated for 2S/7.4V operation, use a regulated 5-6V BEC/buck converter instead.
     - The Pi, motor driver, and servo supply all share a common ground. Without this, GPIO signal levels become unreliable and the servo can behave erratically even when the logic is correct.
     - Always lift the driven wheels off the ground for first motor and steering test, before any floor testing.

4. Wiring
   4.1 Power distribution
   - 30W power bank → Raspberry Pi USB-C power input.
   - 7.4V battery + → Motor driver VM.
   - 7.4V battery - → Motor driver GND.
   - Pi GND → Motor-driver GND.
   - Servo + → 5-6V regulated BEC/buck output.
   - Servo GND → BEC/buck GND and Pi common GND.

   4.2 Motor driver
   - (AIN1) connect to (GPIO17) Pin 11
   - (AIN2) connect to (GPIO27) Pin 13
   - (BIN1) connect to (GPIO22) Pin 15
   - (BIN2) connect to (GPIO23) Pin 16
   - (STBY) connect to (GPIO24) Pin 18
   - (GND) connect to (Pi GND) Pin 6 or another Pi GND
   - (VM) connect to (7.4V battery +) Motor supply
   - (GND) connect to (7.4V battery -) common ground
   - (AO1/AO2) connect to (Motor A) Motor output
   - (BO1/BO2) connect to (Motor B) Motor output
 (This pinout follows the labels printed on the board actually used for testing).

   4.3 Steering servo
   -servo wires:
   - Orange/yellow/white:
     function: signal
     connection: GPIO18, physical pin 12
   - Red:
     function: +5V power
     connection: 5-6V regulated BEC/buck
   - Brown/Black:
     function: Ground
     connection: Common GND

5. Raspberry Pi Setup
   Build configuration used:
   - Hostname: tmm
   - Username: pi
   - SSH: Enabled
   - SSH authentication: password authentication
   - Wi-Fi: phone hotspot or local Wi-Fi
     
   5.1 connect over SSH
     ssh pi@tmm.local
   if the host identification changes (like after re-flashing the SD card):
     ssh-keygen -R tmm.local
     ssh pi@tmm.local

   5.2 Remote desktop (VNC)
   (enable VNC from Raspberry Pi configuration rather than running a standalone server, so the VNC session shares the active desktop instead of creating a sperate one)
   sudo raspi-config
   sudo reboot
connect from a VNC viewer to tmm.local (or the IP from hostname -I).
only use a standalone TigerVNC server (tigervnc-standalone-server, vncserver :1) if a separate virtual desktop session is specifically needed, it does not share the Pi's physical desktop.

6. Software Environment
   sudo apt update
   sudo apt install -y python3-lgpio python3-opencv python3-smbus2 i2c-tools
   verify:
   python3 -c "import lgpio; print('lgpio OK')"
   python3 -c "import cv2; print('OpenCV OK')"
   python3 -c "import smbus2; print('smbus2 OK')"
(Raspberry Pi OS Trixie: don't rely on the older pigpio daemon package for this build, all GPIO code in this project uses lgpio)

7. GPIO Pin assignment
   - Motor A IN1: GPIO17 - PIN 11
   - Motor A IN2: GPIO27 - PIN 13
   - Motor B IN1: GPIO22 - PIN 15
   - Motor B IN2: GPIO23 - PIN 16
   - Motor driver STBY: GPIO24 - PIN 18
   - Steering servo signal: GPIO18 - PIN 12
   - Ground: GND - 6 (or another GND pin)

8. Design decisions & Iteration
   This section document the reasoning behind the current configuration, what was tried, what failed, and why the final values were chosed. (see /src for the tested scripts referenced below).
- **Motor direction mapping.** Initial GPIO-level testing (AIN1=1/AIN2=0) drove the robot backward relative to its physical chassis orientation. Rather than rewire the driver board, the fix was applied in software: the verified physical-forward mapping is (AIN1=0, AIN2=1, BIN1=1, BIN2=0). (All later test scripts and the autonomous program use this corrected mapping, any future script must match it or the robot will reverse its intended direction).
- **Steering calibration.** Earlier pulse values (Right=700, center=1000, left=1300) pushed the servo close to it mechanical end stops, risking gear strain and inconsistent centering. The values were pulled in to (right=850, center=1000, left=1150), a deliberately softer range that keeps the servo within safe mechanical travel while still producing a usable steering angle.
- **GPIO Library choice**. lgpio was chosen over the legacy pigpio daemon because Raspberry Pi OS Trixie does not reliably support the gipio background daemon this project would otherwise depend on. lgpio needs no daemon and matches the current OS.
- **Servo idle state**. lgpio.tx_servo(h, servo, 0) stops pulse output, it does not command a 0° angle. Every test and the main program explicitly re-centers the servo (steer_center) before cutting the pulse, so the wheels don't default to an unpredictable angle when the program exits.
- **Startup sequencing**. The autonomous program centers the steering servo and waits before enabling STBY and driving the motors, so the robot never lurches or steers hard immediately after power-on.
  ##

  9. Autonomous Driving Strategy
      The current implimintation:
     1. Both drive motors run forward continuously.
     2. The camera captures frames and works only on the lower half of the frame (frame [240:480, 0:640]) as the region of interest, reducing noise from the upper field of view and barrel distortion introduced by the wide-angle lens.
     3. The frame is converted to HSV and thresholded for red (two hue ranges, since red wraps around 0°/180° in HSV) and green.
     4. The largest contour area for each color is compared against a minimum-area threshold (MIN_AREA = 500) to reject noise.
     5. Steering decision:
        - Green detected (area > threshold > red area) → steer left.
        - Red detected (area > threshold > green area) → steer right.
        - otherwise → steer center (straight).
HSV ranges must be re-tuned under actual competition lighting before relying on this logic in a run.
- (src/color_steering.py) → decision logic only
- (src/autonomous_main.py) → full integrated loop, for the tested implementations.

10. Running autonomously at Boot
    A 'systemd' service starts the robot program automatically on power-up.
    # /etc/systemd/system/robot.service
[Unit]
Description=WRO Robot Startup
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/python3 /home/pi/motor_test_final.py
Restart=no

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl enable robot.service
sudo systemctl start robot.service
sudo systemctl status robot.service

Diagnostics:
journalctl -u robot.service -b --no-pager
ls -l /home/pi/motor_test_final.py

11. Safe shutdown
    sudo shutdown -h now
wait until the Pi has fully halted and all activity LEDs stop before disconnecting power. Removing power while Linux is still writing to storage can corrupt the filesystem.

 12. Pre-Run Checklist
     - Pi powered from a 30W power band with a 5V/3A capable output.
     - Motor driver VM receives 7.4V battery power; polarity checked.
     - Pi GND, motor-driver GND, and servo-supply GND are common.
     - Servo signal connected to GPIO18 (physical pin 12).
     - Steering center verified at 1000µs before allowing the robot to move.
     - Steering range confirmed: RIGHT 850, CENTER 1000, LEFT 1150.
     - Both motors rotate in the physical forward direction (A: 0/1, B: 1/0).
     - Camera's assigned device number checked right before the run (Linux can assign a different number than last time) and confirmed to match what the program is set to read from.
     - Robot tested first with wheels lifted, then at low speed on the floor.
     - Boot service tested manually before relying on autonomous power-on.
     - A safe method exists to stop the robot and shut down the Pi.
    
13. Troubleshooting (problem → check/fix)
    - SSH host key changed → ssh-keygen _R tmm.local, then reconnect,
    - Cannot find Pi → ping tmm.local; check hotspot/Wi-Fi; use hostname -I on the Pi directly.
    - VNC freezes/ disconnects → confirm the Pi is reachable via pin/SSH first; reboot if needed.
    - 'systemd' service fails with 'status=2' → ExecStart path is wrong, verify the exact filename with ls -l.
    - Robot moves backward → Use the final physical-forward mapping: A 0/1, B 1/0.
    - Motor does not move → Check VM battery, common ground, STBY=HIGH, and motor output terminals.
    - Servo moves to mechanical end → Use the softer calibration values: 850/1000/1150.
    - Servo causes Pi instability → Power the servo from a separate 5-6V BEC/buck, sharing only ground with the Pi.
    - USB camera not detected → check lsusb and /dev/video*; try 'videoCapture (0, cv2.CAP_V4L2).
    - OpenCV window unavailable over SSH → Use a VNC desktop, or run headless and log decisions instead of cv2.imshow.
    - I²C scan empty on old adapter → Adapter/controller may be disconnected or faulty; the current motor-driver build avoids this dependency.
   
Useful commands:
- SSH from Mac → ssh pi@tmm.local
- IP address → hostname -I
- Hostname → hostmane
- USB device → ls /dev/video*
- GPIO config → pinctrl get 18
- Reboot → sudo reboot
- shutdown → sudo shutdown -h now
- Service status → sudo systemctl status robot.service
- Service logs → jounalctl -u robot.service -b --no-pager

