#define reverse 1
//#define SERIAL_DEBUG 1

#define FASTLED_INTERNAL
#include <FastLED.h>

#define RELAY_PIN 2
#define DATA_PIN 6

#define NUM_LEDS 100
#define PATTERN_SIZE 40

CRGB leds[NUM_LEDS];

#ifndef reverse
CRGB pattern[] = {
CRGB(211, 0, 0),
CRGB(173, 0, 0),
CRGB(139, 0, 0),
CRGB(112, 0, 0),
CRGB(88, 0, 0),
CRGB(68, 0, 0),
CRGB(52, 0, 0),
CRGB(38, 0, 0),
CRGB(28, 0, 0),
CRGB(20, 0, 0),
CRGB(13, 0, 0),
CRGB(8, 0, 0),
CRGB(6, 0, 0),
CRGB(3, 0, 0),
CRGB(1, 0, 0),
CRGB(1, 0, 0),
CRGB(0, 0, 0),
CRGB(0, 0, 0),
CRGB(0, 0, 0),
CRGB(0, 0, 0),
CRGB(0, 211, 0),
CRGB(0, 172, 0),
CRGB(0, 140, 0),
CRGB(0, 112, 0),
CRGB(0, 88, 0),
CRGB(0, 68, 0),
CRGB(0, 51, 0),
CRGB(0, 39, 0),
CRGB(0, 28, 0),
CRGB(0, 19, 0),
CRGB(0, 14, 0),
CRGB(0, 8, 0),
CRGB(0, 5, 0),
CRGB(0, 3, 0),
CRGB(0, 2, 0),
CRGB(0, 1, 0),
CRGB(0, 0, 0),
CRGB(0, 0, 0),
CRGB(0, 0, 0),
CRGB(0, 0, 0)
};
#endif
#ifdef reverse
CRGB pattern[] = {
  CRGB(0, 0, 0),
  CRGB(0, 0, 0),
  CRGB(0, 0, 0),
  CRGB(0, 0, 0),
  CRGB(0, 1, 0),
  CRGB(0, 2, 0),
  CRGB(0, 3, 0),
  CRGB(0, 5, 0),
  CRGB(0, 8, 0),
  CRGB(0, 14, 0),
  CRGB(0, 19, 0),
  CRGB(0, 28, 0),
  CRGB(0, 39, 0),
  CRGB(0, 51, 0),
  CRGB(0, 68, 0),
  CRGB(0, 88, 0),
  CRGB(0, 112, 0),
  CRGB(0, 140, 0),
  CRGB(0, 172, 0),
  CRGB(0, 211, 0),
  CRGB(0, 0, 0),
  CRGB(0, 0, 0),
  CRGB(0, 0, 0),
  CRGB(0, 0, 0),
  CRGB(1, 0, 0),
  CRGB(1, 0, 0),
  CRGB(3, 0, 0),
  CRGB(6, 0, 0),
  CRGB(8, 0, 0),
  CRGB(13, 0, 0),
  CRGB(20, 0, 0),
  CRGB(28, 0, 0),
  CRGB(38, 0, 0),
  CRGB(52, 0, 0),
  CRGB(68, 0, 0),
  CRGB(88, 0, 0),
  CRGB(112, 0, 0),
  CRGB(139, 0, 0),
  CRGB(173, 0, 0),
  CRGB(211, 0, 0)
};
#endif

void setup() {
  #ifdef SERIAL_DEBUG
    Serial.begin(9600);
    Serial.println("hello world");
  #endif
  pinMode(RELAY_PIN,INPUT_PULLUP);
  FastLED.addLeds<NEOPIXEL, DATA_PIN>(leds, NUM_LEDS);
}

uint8_t i = 1;
uint8_t brightness = 0;
const int8_t midpoint = 21;

CRGB get_pixel(uint8_t x) {
//  return pattern[15];
  return pattern[(x + i) % PATTERN_SIZE];
}

void loop() {
//    i = (i + 1) % PATTERN_SIZE;
    if (i) {
      i --;
    } else {
      i = PATTERN_SIZE - 1;
    }
    if (digitalRead(RELAY_PIN)) {
      brightness = brightness / 2;
    } else {
      brightness = qadd8(brightness, 4);
    }
    #ifdef SERIAL_DEBUG
      Serial.print(i);
      Serial.print(",");
      Serial.println(brightness);
    #endif
    FastLED.setBrightness(brightness);

    for (int8_t x=0; x<=30; x++) {
        CRGB color = get_pixel(x);
        if (midpoint + x < 47) {
          leds[midpoint + x] = color;
        }
        if (x <= midpoint) {
          leds[midpoint - x] = color;
        }
    }
    FastLED.show();
    delay(1000/30);
}
