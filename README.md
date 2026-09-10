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

