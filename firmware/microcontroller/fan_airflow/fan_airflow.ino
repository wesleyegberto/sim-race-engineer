/*
 * Sim Race Engineer — Airflow Simulation reference firmware
 *
 * Wire protocol (9600 baud, ASCII lines terminated by '\n'):
 *   App -> device : "FAN:<0-255>\n"  set PWM duty cycle for both frontal fans
 *   App -> device : "PING\n"         connection test
 *   Device -> app : "PONG\n"         reply to PING
 *
 * Safety property: fans are turned off if no valid "FAN:" command arrives
 * within FAILSAFE_TIMEOUT_MS. PING/PONG traffic never resets this timer —
 * a test-connection loop must never be able to keep fans spinning without
 * genuine speed data.
 *
 * Target: Arduino Uno/Nano-class board (5V logic, digital PWM pins).
 * See docs/hardware/airflow-simulation.md for wiring and parts list.
 */

const uint8_t FAN_PIN_1 = 9;   // PWM-capable digital pin, fan channel 1
const uint8_t FAN_PIN_2 = 10;  // PWM-capable digital pin, fan channel 2

const unsigned long FAILSAFE_TIMEOUT_MS = 5000;
const unsigned long BAUD_RATE = 9600;

unsigned long lastFanCommandMillis = 0;
String lineBuffer;

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(FAN_PIN_1, OUTPUT);
  pinMode(FAN_PIN_2, OUTPUT);

  // Pins 9/10 both run off Timer1, whose default prescaler (64) puts the PWM
  // switching frequency around 490Hz — squarely in the audible range, heard
  // as a whine/buzz that changes pitch with duty cycle. Dropping the
  // prescaler to 1 pushes it to ~31.4kHz (ultrasonic, above human hearing),
  // with no effect on millis()/micros() (Timer0) or the analogWrite() API
  // itself — only the underlying switching frequency changes.
  TCCR1B = (TCCR1B & 0b11111000) | 0x01;

  // Boot with fans off; stay off until the first valid FAN: command arrives.
  setFanDuty(0);
  lineBuffer.reserve(32);
}

void loop() {
  readSerialLines();
  applyFailsafe();
}

// Reads any bytes available on Serial, splitting on '\n' into complete
// lines and dispatching each one. Never blocks — only acts on bytes already
// buffered by the hardware UART.
void readSerialLines() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      handleLine(lineBuffer);
      lineBuffer = "";
    } else if (c != '\r') {
      lineBuffer += c;
    }
  }
}

// Dispatches one complete line (without the trailing newline). Any line
// that doesn't parse as "FAN:<int>" or "PING" is ignored silently — no
// error reply, keeps the reference firmware minimal.
void handleLine(const String& line) {
  if (line == "PING") {
    Serial.println("PONG");
    return;
  }

  if (line.startsWith("FAN:")) {
    String valueStr = line.substring(4);
    if (valueStr.length() == 0) {
      return;  // malformed, e.g. "FAN:" with nothing after it
    }
    for (unsigned int i = 0; i < valueStr.length(); i++) {
      if (!isDigit(valueStr[i])) {
        return;  // malformed, non-numeric payload — ignore silently
      }
    }

    long duty = valueStr.toInt();
    duty = constrain(duty, 0, 255);  // defensive clamp, even though the app already clamps
    setFanDuty((uint8_t)duty);
    lastFanCommandMillis = millis();
    return;
  }

  // Unrecognized line — ignored silently.
}

// Turns fans off if too much time has passed since the last valid FAN:
// command. Deliberately not reset by PING/PONG (see file header comment).
void applyFailsafe() {
  if (millis() - lastFanCommandMillis > FAILSAFE_TIMEOUT_MS) {
    setFanDuty(0);
  }
}

void setFanDuty(uint8_t duty) {
  analogWrite(FAN_PIN_1, duty);
  analogWrite(FAN_PIN_2, duty);
}
