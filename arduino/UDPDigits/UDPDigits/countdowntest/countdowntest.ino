//We always have to include the library
#include "LedControl.h"
//#define serial

/*
 Now we need a LedControl to work with.
 ***** These pin numbers will probably not work with your hardware *****
 pin 12 is connected to the DataIn 
 pin 11 is connected to the CLK 
 pin 10 is connected to LOAD 
 We have only a single MAX72XX.
 */
LedControl lc=LedControl(12,11,10,1);

/* we always wait a bit between updates of the display */
unsigned long delaytime=250;

void setup() {
  /*
   The MAX72XX is in power-saving mode on startup,
   we have to do a wakeup call
   */
  lc.shutdown(0,false);
  /* Set the brightness to a medium values */
  lc.setIntensity(0,1);
  /* and clear the display */
  lc.clearDisplay(0);
  #ifdef serial
  Serial.begin(9600);
  #endif
}




void hello(){

  lc.setChar(0,7,'H',false);
  lc.setChar(0,6,'E',false);
  lc.setChar(0,5,'L',false);
  lc.setChar(0,4,'L',false);
  lc.setChar(0,3,'0',false);
  lc.setChar(0,2,'.',false);
  lc.setChar(0,1,'.',false);
  lc.setChar(0,0,'.',false);
  delay(delaytime+1000);
  lc.clearDisplay(0);
  delay(delaytime);
  lc.setDigit(0,7,1,false);
  delay(delaytime);
  lc.setDigit(0,6,2,false);
  delay(delaytime);
  lc.setDigit(0,5,3,false);
  delay(delaytime);
  lc.setDigit(0,4,4,false);
  delay(delaytime);
  lc.setDigit(0,3,5,false);
  delay(delaytime);
  lc.setDigit(0,2,6,false);
  delay(delaytime);
  lc.setDigit(0,1,7,false);
  delay(delaytime);
  lc.setDigit(0,0,8,false);
  delay(1500);
  lc.clearDisplay(0);
  delay(delaytime);

}
void setNumbers(uint16_t number) {
  lc.setDigit(0, 7, (number / 10000000) % 10, false);
  lc.setDigit(0, 6, (number / 1000000) % 10, false);
  lc.setDigit(0, 5, (number / 100000) % 10, false);
  lc.setDigit(0, 4, (number / 10000) % 10, false);
  lc.setDigit(0, 3, (number / 1000) % 10, false);
  lc.setDigit(0, 2, (number / 100) % 10, false);
  lc.setDigit(0, 1, (number / 10) % 10, false);
  lc.setDigit(0, 0, (number / 1) % 10, false);
//  delay(200);
}

void setDigitPair(char start, uint16_t number) {
  lc.setDigit(0, start+1, number / 10, false);
  bool dot = start;
  lc.setDigit(0, start, number % 10, dot);
  #ifdef serial
  Serial.print(number);
  #endif
  if (dot) {
    #ifdef serial
    Serial.print('.');
    #endif
  }
}
uint32_t epoch = (uint32_t)604800000;
void loop() { 

  uint32_t t = millis();
  uint32_t remaining = epoch - t;
  delay(remaining % 1000);
  uint8_t seconds = (remaining / 1000) % 60;
  uint8_t minutes = (remaining / 1000 / 60) % 60;
  uint8_t hours = (remaining / 1000 / 60 / 60) % 24;
  uint8_t days = (remaining / 1000 / 60 / 60 / 24);

  lc.shutdown(0, true);
  lc.shutdown(0, false);
  lc.setIntensity(0, 1);
  setDigitPair(6, days);
  setDigitPair(4, hours);
  setDigitPair(2, minutes);
  setDigitPair(0, seconds);

  #ifdef serial
  Serial.println();
  #endif
}
