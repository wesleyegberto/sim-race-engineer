/*
 * Sim Race Engineer — Airflow Simulation manual bench-test firmware
 *
 * Lets you drive both fan channels by typing commands into any serial
 * terminal (Arduino IDE Serial Monitor, `screen`, `minicom`, etc.) at
 * 9600 baud — no PC app and no "FAN:" protocol involved. Use this to
 * validate the wiring (MOSFETs, resistors, diodes, fans) before wiring
 * the board up to Sim Race Engineer via the reference firmware.
 *
 * Commands (ASCII lines terminated by '\n', with or without '\r'):
 *   <0-255>       set BOTH fans to this PWM duty cycle
 *   1:<0-255>     set fan 1 (pin D9) only
 *   2:<0-255>     set fan 2 (pin D10) only
 *   0             stop both fans (same as sending bare "0")
 *   ?             print command help
 *
 * Unlike the reference firmware (fan_airflow.ino), there is NO failsafe
 * timeout here — a duty cycle you set stays applied until you change it.
 * That's intentional for bench testing (a human typing is much slower
 * than the 1s failsafe window) but means YOU must send "0" before
 * disconnecting, rather than relying on a timeout to stop the fans.
 *
 * Wiring is identical to the reference firmware — same pins, same
 * MOSFET/resistor/diode/fan circuit. See docs/hardware/microcontroller.md
 * for the connection table and BOM.
 */

const uint8_t FAN_PIN_1 = 9;   // PWM-capable digital pin, fan channel 1
const uint8_t FAN_PIN_2 = 10;  // PWM-capable digital pin, fan channel 2

const unsigned long BAUD_RATE = 9600;

String lineBuffer;

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(FAN_PIN_1, OUTPUT);
  pinMode(FAN_PIN_2, OUTPUT);

  // Pins 9/10 both run off Timer1 — drop its prescaler from the default 64
  // (~490Hz, audible whine) to 1 (~31.4kHz, ultrasonic). See fan_airflow.ino
  // for the full explanation; kept identical here so bench testing sounds
  // the same as production.
  TCCR1B = (TCCR1B & 0b11111000) | 0x01;

  // Boot with fans off.
  setFanDuty(FAN_PIN_1, 0);
  setFanDuty(FAN_PIN_2, 0);
  lineBuffer.reserve(32);

  printHelp();
}

void loop() {
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

void handleLine(const String& rawLine) {
  String line = rawLine;
  line.trim();
  if (line.length() == 0) {
    return;
  }

  if (line == "?" || line.equalsIgnoreCase("help")) {
    printHelp();
    return;
  }

  if (line.startsWith("1:")) {
    applyChannel(FAN_PIN_1, "Fan 1", line.substring(2));
    return;
  }

  if (line.startsWith("2:")) {
    applyChannel(FAN_PIN_2, "Fan 2", line.substring(2));
    return;
  }

  // Bare number -> both fans (mirrors the reference firmware's FAN: command).
  if (isValidDuty(line)) {
    uint8_t duty = (uint8_t)constrain(line.toInt(), 0, 255);
    setFanDuty(FAN_PIN_1, duty);
    setFanDuty(FAN_PIN_2, duty);
    printApplied("Both fans", duty);
    return;
  }

  Serial.println(F("Unrecognized command. Type ? for help."));
}

void applyChannel(uint8_t pin, const char* label, const String& valueStr) {
  if (!isValidDuty(valueStr)) {
    Serial.println(F("Unrecognized command. Type ? for help."));
    return;
  }
  uint8_t duty = (uint8_t)constrain(valueStr.toInt(), 0, 255);
  setFanDuty(pin, duty);
  printApplied(label, duty);
}

bool isValidDuty(const String& s) {
  if (s.length() == 0) {
    return false;
  }
  for (unsigned int i = 0; i < s.length(); i++) {
    if (!isDigit(s[i])) {
      return false;
    }
  }
  return true;
}

void setFanDuty(uint8_t pin, uint8_t duty) {
  analogWrite(pin, duty);
}

void printApplied(const char* label, uint8_t duty) {
  Serial.print(label);
  Serial.print(F(" -> duty "));
  Serial.print(duty);
  Serial.print(F("/255 ("));
  Serial.print((duty * 100UL) / 255);
  Serial.println(F("%)"));
}

void printHelp() {
  Serial.println(F("--- Sim Race Engineer: fan bench test ---"));
  Serial.println(F("<0-255>    set BOTH fans"));
  Serial.println(F("1:<0-255>  set fan 1 (D9) only"));
  Serial.println(F("2:<0-255>  set fan 2 (D10) only"));
  Serial.println(F("0          stop both fans"));
  Serial.println(F("?          show this help"));
  Serial.println(F("No failsafe timeout in this firmware - send 0 before disconnecting."));
}
