/*
 * Sim Race Engineer — Airflow Simulation LED bring-up firmware
 *
 * Same manual bench-test protocol as fan_manual_test.ino, but with output
 * text worded for driving an LED on each channel instead of a fan. Use
 * this to validate the MOSFET switching stage (gate resistor, pull-down,
 * MOSFET, flyback diode) with a cheap, instantly-visible load before
 * risking the actual fans — an LED lights up (or doesn't) immediately,
 * with no moving parts or current draw to worry about.
 *
 * Circuit: identical to the fan wiring, except each fan is replaced by
 * an LED with a series current-limiting resistor (the fan's own coil
 * resistance limited current; a bare LED has none). Wire the resistor
 * between the +12V rail and the LED anode (long leg), and the LED
 * cathode (short leg / flat side) to the same node the fan's negative
 * wire used — the MOSFET drain. The flyback diode isn't doing useful
 * work with an LED load (no inductive kickback to suppress) but is
 * harmless to leave in place. See docs/hardware/microcontroller.md for
 * the full wiring table and resistor value guidance.
 *
 * Commands (ASCII lines terminated by '\n', with or without '\r'):
 *   <0-255>       set BOTH LEDs to this PWM duty cycle (brightness)
 *   1:<0-255>     set LED 1 (pin D9) only
 *   2:<0-255>     set LED 2 (pin D10) only
 *   0             turn off both LEDs
 *   ?             print command help
 *
 * Like fan_manual_test.ino, there is NO failsafe timeout here — a duty
 * cycle you set stays applied until you change it.
 */

const uint8_t LED_PIN_1 = 9;   // PWM-capable digital pin, LED channel 1
const uint8_t LED_PIN_2 = 10;  // PWM-capable digital pin, LED channel 2

const unsigned long BAUD_RATE = 9600;

String lineBuffer;

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(LED_PIN_1, OUTPUT);
  pinMode(LED_PIN_2, OUTPUT);

  // Boot with LEDs off.
  setLedDuty(LED_PIN_1, 0);
  setLedDuty(LED_PIN_2, 0);
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
    applyChannel(LED_PIN_1, "LED 1", line.substring(2));
    return;
  }

  if (line.startsWith("2:")) {
    applyChannel(LED_PIN_2, "LED 2", line.substring(2));
    return;
  }

  // Bare number -> both LEDs (mirrors the reference firmware's FAN: command).
  if (isValidDuty(line)) {
    uint8_t duty = (uint8_t)constrain(line.toInt(), 0, 255);
    setLedDuty(LED_PIN_1, duty);
    setLedDuty(LED_PIN_2, duty);
    printApplied("Both LEDs", duty);
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
  setLedDuty(pin, duty);
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

void setLedDuty(uint8_t pin, uint8_t duty) {
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
  Serial.println(F("--- Sim Race Engineer: LED bring-up test ---"));
  Serial.println(F("<0-255>    set BOTH LEDs"));
  Serial.println(F("1:<0-255>  set LED 1 (D9) only"));
  Serial.println(F("2:<0-255>  set LED 2 (D10) only"));
  Serial.println(F("0          turn off both LEDs"));
  Serial.println(F("?          show this help"));
  Serial.println(F("No failsafe timeout in this firmware - send 0 before disconnecting."));
}
