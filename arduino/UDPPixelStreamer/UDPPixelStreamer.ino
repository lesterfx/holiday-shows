
/*
 * UIPEthernet TCPServer example.
 *
 * UIPEthernet is a TCP/IP stack that can be used with a enc28j60 based
 * Ethernet-shield.
 *
 * UIPEthernet uses the fine uIP stack by Adam Dunkels <adam@sics.se>
 *
 *      -----------------
 *
 * This Hello World example sets up a server at 192.168.1.6 on port 1000.
 * Telnet here to access the service.  The uIP stack will also respond to
 * pings to test if you have successfully established a TCP connection to
 * the Arduino.
 *
 * This example was based upon uIP hello-world by Adam Dunkels <adam@sics.se>
 * Ported to the Arduino IDE by Adam Nielsen <malvineous@shikadi.net>
 * Adaption to Enc28J60 by Norbert Truchsess <norbert.truchsess@t-online.de>
 */

#define SERIAL_DEBUG 1


#include <Ethernet.h>
#include <EthernetUdp.h>
#include <EEPROM.h>
#define FASTLED_INTERNAL
#include <FastLED.h>

#define NUM_LEDS 60
#define DATA_PIN 6

char packetBuffer[NUM_LEDS*3];
CRGB leds[NUM_LEDS];

EthernetUDP Udp;

uint16_t msg_counter = 0;
// Local mac address, initialiser can be removed (when using initMacAddress)
uint8_t mac[6] = {0x00,0x01,0x02,0x03,0x04,0x05};

// https://arduino.stackexchange.com/a/60174
void initMacAddress() {
  // Rather than having a fixed MAC address for an Arduino sketch,
  // this implements a different, random address which is persistant
  // by storing it to EEPROM (which only works when EEPROM is available).

  // Here the MAC ADDRESS IS LOCATED AT ADDRESS 0 OF THE EEPROM
  for(int i=0;i<6;i++) {
    mac[i]=EEPROM[i];
  }

  // Generating a new MAC address if the address found is not locally
  // Administrated.  This test requires that the 2 lower bits of the first
  // byte are equal to "2" (bits 1 and 0).
  // Normally it is only required that bit 1 is "1", but checking bit 0 for a 0
  // allows to detect an uninitialized EEPROM.
  if((mac[0]&0x03)!=2) { // Is this a locally administered address?
    // No a locally managed address, generate random address and store it.
    #ifdef SERIAL_DEBUG
      Serial.println("GENERATE NEW MAC ADDR");
    #endif
    randomSeed(analogRead(A7));
    for(int i=0;i<6;i++) {
      mac[i]=random(256);
      if(i==0) {mac[0]&=0xFC;mac[0]|=0x2;} // Make locally administered address

      EEPROM.update(i,mac[i]);

      #ifdef SERIAL_DEBUG
        if(mac[i]<10) {Serial.print('0');}  // Print two digets
        Serial.print(mac[i],HEX);Serial.print(":");
      #endif
    }
    #ifdef SERIAL_DEBUG
      Serial.println();
    #endif
    flash(0, 200);
    flash(0, 200);
  } else {
    #ifdef SERIAL_DEBUG
        Serial.println("mac grabbed from eeprom");
        for (int i=0;i<6;i++) {
          if(mac[i]<10) {Serial.print('0');}
          Serial.print(mac[i],HEX);Serial.print(":");
        }
        Serial.println();
    #endif
    flash(0, 400);
  }
}

void flash(uint8_t index, uint16_t milliseconds) {
  for (uint8_t i=0;i<NUM_LEDS;i++) {
    leds[i] = 0xff0000;
  }
  FastLED.show();
  delay(milliseconds);
  for (uint8_t i=0;i<NUM_LEDS;i++) {
    leds[i] = 0x000000;
  }
  FastLED.show();
  delay(milliseconds);
}

void setup() {
  #ifdef SERIAL_DEBUG
    Serial.begin(9600);
    Serial.println("hello world");
   #endif

  
  FastLED.addLeds<NEOPIXEL, DATA_PIN>(leds, NUM_LEDS);
  
  initMacAddress();

  #ifdef SERIAL_DEBUG
    Serial.println("Begin");
   #endif
  for (uint8_t i=0; i<NUM_LEDS; i++) {
    leds[i] = 0x0000ff;
    FastLED.show();
    delay(20);
  }
  for (uint8_t i=NUM_LEDS; i; i--) {
    leds[i-1] = 0;
    FastLED.show();
    delay(20);
  }

  Ethernet.begin(mac);
    #ifdef SERIAL_DEBUG
      Serial.println("Begun");
      Serial.println(Ethernet.localIP());
    #endif
  
 //  Check for Ethernet hardware present
  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    #ifdef SERIAL_DEBUG
      Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
    #endif
    while (true) {
      flash(0, 2000); // do nothing, no point running without Ethernet hardware
    }
  }
  while (Ethernet.linkStatus() == LinkOFF) {
    #ifdef SERIAL_DEBUG
      Serial.println("Ethernet cable is not connected.");
    #endif
    flash(0, 200);
  }
  for (uint8_t i=0; i<NUM_LEDS; i++) {
//    leds[i] = 0x00ff00;
//    FastLED.show();
    delay(20);
  }
  for (uint8_t i=NUM_LEDS-1; i; i++) {
//    leds[i] = 0;
//    FastLED.show();
    delay(20);
  }
  Udp.begin(2700);
}

void loop() {
  Ethernet.maintain();
  
  int packetSize = Udp.parsePacket();
  char re[3] = {0x00, 0x00, 0x00};
  if (packetSize > 0) {
      Udp.read(packetBuffer, NUM_LEDS*3);
      if (packetSize == 3){
        switch ((uint8_t)packetBuffer[0]) {
          case 0xAA:
              re[0] = 0xBB;
              break;
          case 0xCC:
              re[0] = 0xCC;
              re[1] = highByte(msg_counter);
              re[2] = lowByte(msg_counter);
              msg_counter = 0;
              break;
        }
        if((uint8_t)re[0] != 0x00){
          #ifdef SERIAL_DEBUG
            Serial.println("Responding");
          #endif
          Udp.beginPacket(Udp.remoteIP(),Udp.remotePort());
          Udp.write((const char*)&re, 3);
          Udp.endPacket();
        }
      } else if (packetSize == NUM_LEDS*3) {
          #ifdef SERIAL_DEBUG
            Serial.println("Showing Strip");
          #endif
            msg_counter++;
//            uint32_t states = 0;
//            for (uint8_t i=0;i<NUM_LEDS; i++) {
//              leds[i].r = packetBuffer[i*3];
//              leds[i].g = packetBuffer[i*3+1];
//              leds[i].b = packetBuffer[i*3+2];
//            }
            memmove( &leds[0], &packetBuffer[0], NUM_LEDS * sizeof( CRGB) );  // no need if it's in the same place!
            FastLED.show();
            Serial.println(leds[0]);
            Serial.println(leds[1]);
            Serial.println(leds[2]);
      } else {
          #ifdef SERIAL_DEBUG
            Serial.print("Unexpected Packet Size: ");
            Serial.println(packetSize);
            Serial.print("Expected 3 or ");
            Serial.println(NUM_LEDS*3);
          #endif
      }
        
  } else {
    #ifdef SERIAL_DEBUG
      Serial.print(".");
    #endif
  }
       
  delay(10);
}
     
