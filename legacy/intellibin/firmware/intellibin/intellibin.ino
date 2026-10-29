#include <Stepper.h>
const int stepsPerRevolution = 2038;

// Creates an instance of stepper class
// Pins entered in sequence IN1-IN3-IN2-IN4 for proper step sequence
Stepper Trash = Stepper(stepsPerRevolution, 8, 9, 10, 11);
Stepper Recycle = Stepper(stepsPerRevolution, 4, 5, 6, 7);

Stepper Bio = Stepper(stepsPerRevolution, A3, A2, A1, A0);

float duration, distance;

// String string_in;

void setup()
{
  Serial.begin(9600);
}
void loop()
{
  // Checks for serial input
  if (Serial.available() > 0)
  {

    int incomingByte = Serial.parseInt(); // read the incoming byte:
    // incomingByte.trim();
    // incomingByte = incomingByte.replace("\r\n", "").replace("\r", "").replace("\n", "").replace("b", "");
    // If the arduino recives trash from the serial port
    if (incomingByte == 0)
    {
      Trash.setSpeed(5);
      Trash.step(stepsPerRevolution / 2);
      delay(10000);
      Trash.step(stepsPerRevolution / 2);
    }
    // If the arduino recives recycle from the serial port

    else if (incomingByte == 1)
    {
      Recycle.setSpeed(5);
      Recycle.step(stepsPerRevolution / 2);
      delay(10000);
      Recycle.step(stepsPerRevolution / 2);
    }
    // If the arduino recives Bio from the serial port

    else if (incomingByte == 2)
    {
      Bio.setSpeed(30);
      Bio.step(stepsPerRevolution / 2);
      delay(10000);
      Bio.step(stepsPerRevolution / 2);
    }
    else
    {
      Serial.print("nah");
    }
    Serial.flush();
    incomingByte = "";
  }
}