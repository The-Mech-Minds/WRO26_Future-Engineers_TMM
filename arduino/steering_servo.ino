#include <Servo.h>

Servo steeringServo;
const int AIN1 = 3;
const int AIN2 = 5;
const int STBY = 4;
const int SERVO_PIN = 9;

unsigned long lastCommandTime = 0;
const unsigned long WATCHDOG_TIMEOUT = 1000;

void setup() {
  Serial.begin(9600);
  steeringServo.attach(SERVO_PIN);
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(STBY, OUTPUT);
  digitalWrite(STBY, HIGH);
  steeringServo.writeMicroseconds(1880);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    int commaIndex = input.indexOf(',');
    if (commaIndex > 0) {
      int servoVal = input.substring(0, commaIndex).toInt();
      int motorVal = input.substring(commaIndex + 1).toInt();
      
      servoVal = constrain(servoVal, 1750, 2150);
      
      // Invert servo direction to fix the steering reversal
      int invertedServoVal = map(servoVal, 1750, 2150, 2150, 1750);
      steeringServo.writeMicroseconds(invertedServoVal);
      
      runMotor(motorVal);
      lastCommandTime = millis();
    }
  }
  
  // Watchdog safety: cut power if Pi signal drops
  if (millis() - lastCommandTime > WATCHDOG_TIMEOUT) {
    runMotor(0);
    steeringServo.writeMicroseconds(1880);
  }
}

void runMotor(int speed) {
  speed = constrain(speed, -100, 100);
  int pwmVal = map(abs(speed), 0, 100, 0, 255);
  
  if (speed > 0) {
    digitalWrite(AIN2, LOW);
    analogWrite(AIN1, pwmVal);
  } else if (speed < 0) {
    digitalWrite(AIN1, LOW);
    analogWrite(AIN2, pwmVal);
  } else {
    analogWrite(AIN1, 0);
    analogWrite(AIN2, 0);
  }
}
