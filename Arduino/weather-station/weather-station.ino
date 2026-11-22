#include "DHT.h"

DHT dht;

float temperature = 0;
int humidity = 0;

unsigned long lastMeasure = 0;
const unsigned long MEASURE_INTERVAL = 5000;  // ms

char cmdBuf[16];
uint8_t cmdLen = 0;

void setup() {
  Serial.begin(9600);
  pinMode(A5, INPUT);
  dht.setup(2);
  lastMeasure = millis() - MEASURE_INTERVAL;  // measure right away
}

void loop() {
  unsigned long now = millis();

  if (now - lastMeasure >= MEASURE_INTERVAL) {
    lastMeasure = now;

    float h = dht.getHumidity();
    if (dht.getStatus() == DHT::ERROR_NONE) {
      humidity = (int)h;
    }

    float volt = analogRead(A5);
    temperature = volt / 1023 * 5 * 100;
  }

  handleSerial();
}

unsigned long lastByte = 0;

void processCommand() {
  cmdBuf[cmdLen] = '\0';
  if (strcmp(cmdBuf, "GET") == 0) {
    Serial.print(temperature);
    Serial.print(";");
    Serial.println(humidity);
  }
  cmdLen = 0;
}

void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    lastByte = millis();

    if (c == '\r') continue;

    if (c == '\n') {
      processCommand();
    } else if (cmdLen < sizeof(cmdBuf) - 1) {
      cmdBuf[cmdLen++] = c;
    } else {
      cmdLen = 0;  // overflow, discard
    }
  }

  // No newline received: treat 50 ms of silence as end of command
  if (cmdLen > 0 && millis() - lastByte > 50) {
    processCommand();
  }
}