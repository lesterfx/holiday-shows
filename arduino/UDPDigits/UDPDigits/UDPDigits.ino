/*
 * Write digits 0-7 into an 8-digit LED module using the MAX7219, set the
 * brightness, then render it by flushing the data bits to the MAX7219
 * controller over SPI using the HardSpiInterface class from the AceSPI library.
 */

#include <Arduino.h>
#include <SPI.h> // SPIClass, SPI
#include <AceSPI.h> // HardSpiInterface
#include <AceSegment.h> // Max7219Module

using ace_spi::HardSpiInterface;
using ace_segment::LedModule;
using ace_segment::Max7219Module;
using ace_segment::kDigitRemapArray8Max7219;

// Replace these with the PIN numbers of your dev board.
const uint8_t LATCH_PIN = 10;
const uint8_t DATA_PIN = MOSI;
const uint8_t CLOCK_PIN = SCK;
const uint8_t NUM_DIGITS = 8;

using SpiInterface = HardSpiInterface<SPIClass>;
SpiInterface spiInterface(SPI, LATCH_PIN);
Max7219Module<SpiInterface, NUM_DIGITS> ledModule(
    spiInterface, kDigitRemapArray8Max7219);

// LED segment patterns.
const uint8_t NUM_PATTERNS = 10;
const uint8_t PATTERNS[NUM_PATTERNS] = {
  0b00111111, // 0
  0b00000110, // 1
  0b01011011, // 2
  0b01001111, // 3
  0b01100110, // 4
  0b01101101, // 5
  0b01111101, // 6
  0b00000111, // 7
  0b01111111, // 8
  0b01101111, // 9
};

void setup() {
  Serial.begin(9600);
  delay(1000);

  SPI.begin();
  spiInterface.begin();
  ledModule.begin();
  setNumbers((uint16_t)12345678);
  ledModule.setBrightness(2);
  ledModule.flush();
  delay(5000);
}

void setNumber(uint8_t digit, uint8_t number, bool dp) {
  uint8_t patt = PATTERNS[number];
  if (dp) patt |= 0b10000000;
  ledModule.setPatternAt(digit, patt);
  Serial.print(number);
}
void setNumbers(uint16_t number) {
  Serial.print("numbers: ");
  setNumber(0, (number / 10000000) % 10, false);
  setNumber(1, (number / 1000000) % 10, false);
  setNumber(2, (number / 100000) % 10, false);
  setNumber(3, (number / 10000) % 10, false);
  setNumber(4, (number / 1000) % 10, false);
  setNumber(5, (number / 100) % 10, false);
  setNumber(6, (number / 10) % 10, false);
  setNumber(7, (number / 1) % 10, false);
//  for (uint8_t digit=0; digit<8; digit++) {
//    setNumber((uint8_t)7-digit, (number / (pow(10,digit)) % 10), false);
//  }
  Serial.println("!");
}
uint8_t j = 0;
void loop() {
//  for (uint8_t i=0; i<8; i++) {
//    setNumber(i, (j+8) % 8, false);
//  }
//  j++;
  uint16_t t = millis();
//  ledModule.begin();
  setNumbers(t);
  ledModule.setBrightness(2);
  ledModule.flush();
  delay(400);
}
