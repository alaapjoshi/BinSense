#include <Servo.h>

Servo servo1;  
Servo servo2;  

void setup() {
  Serial.begin(9600);

  servo1.attach(8);  
  servo2.attach(9);  

  // start positions
  servo1.write(90);
  servo2.write(0);
}

void loop() {
  if (Serial.available() > 0) {
    //serual input

    int incomingByte = Serial.parseInt();

    if (incomingByte == 0) {
      for (int pos = 90; pos <= 180; pos++) {
        servo1.write(pos);
        delay(15);
      }

      delay(10000);

      for (int pos = 180; pos >= 90; pos--) {
        servo1.write(pos);
        delay(15);
      }
    }

    else if (incomingByte == 1) {
      for (int pos = 0; pos <= 90; pos++) {
        servo2.write(pos);
        delay(15);
      }

      delay(10000);

      for (int pos = 90; pos >= 0; pos--) {
        servo2.write(pos);
        delay(15);
      }
    }

    // BIO (both servos move)
    else if (incomingByte == 2) {

      // Move both
      for (int pos = 0; pos <= 90; pos++) {
        servo2.write(pos);          
        servo1.write(90 + pos);    
        delay(15);
      }

      delay(10000);

      for (int pos = 90; pos >= 0; pos--) {
        servo2.write(pos);
        servo1.write(90 + pos);
        delay(15);
      }
    }

    else {
      Serial.println("nah");
    }
  }
}