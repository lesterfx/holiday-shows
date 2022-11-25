
//#define SERIAL_DEBUG 1/

#include <EthernetENC.h>
#include <EthernetUdp.h>
#include <EEPROM.h>

EthernetUDP Udp;

#define UDP_TX_PACKET_MAX_SIZE 256
char packetBuffer[UDP_TX_PACKET_MAX_SIZE];  // buffer to hold incoming packet,
uint16_t msg_counter = 0;
// Local mac address, initialiser can be removed (when using initMacAddress)
uint8_t mac[6] = {0x00,0x01,0x02,0x03,0x04,0x05};

// Maps position in array to pin
const int pinMapping[] = {
 14, 17, 2, 3,
 15, 18, 1, 4,
 16, 19, 0, 5,
  6,  7, 8, 9
};

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
    #ifdef ENABLE_MAC_INIT_MESSAGES
      Serial.println("GENERATE NEW MAC ADDR");
    #endif
    randomSeed(analogRead(A7));
    for(int i=0;i<6;i++) {
      mac[i]=random(256);
      if(i==0) {mac[0]&=0xFC;mac[0]|=0x2;} // Make locally administered address

      EEPROM.update(i,mac[i]);

      #ifdef ENABLE_MAC_INIT_MESSAGES
        if(mac[i]<10) {Serial.print('0');}  // Print two digets
        Serial.print(mac[i],HEX);Serial.print(":");
      #endif
    }
    #ifdef ENABLE_MAC_INIT_MESSAGES
      Serial.println();
    #endif
    flash(0, 200);
    flash(0, 200);
  } else {
    #ifdef ENABLE_MAC_INIT_MESSAGES
        Serial.println("mac grabbed from eeprom");
    #endif
    flash(0, 400);
  }
}

void flash(uint8_t index, uint16_t milliseconds) {
    digitalWrite(pinMapping[index], LOW);
    delay(milliseconds);
    digitalWrite(pinMapping[index], HIGH);
    delay(milliseconds);
}
void setAllPins(int state){
  for(int n = 0; n < (sizeof(pinMapping) / sizeof(pinMapping[0])); n++){
          digitalWrite(pinMapping[n], state);
   }
}

void setup() {
  for(int i = 0; i < (sizeof(pinMapping) / sizeof(pinMapping[0])); i++){
    pinMode(pinMapping[i], OUTPUT);
    digitalWrite(pinMapping[i], HIGH);
  }
  
  initMacAddress();

  #ifdef SERIAL_DEBUG
    Serial.begin(9600);
    Serial.println("Begin");
   #endif

  Ethernet.begin(mac);
 //  Check for Ethernet hardware present
  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    #ifdef SERIAL_DEBUG
      Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
    #endif
    while (true) {
      delay(1); // do nothing, no point running without Ethernet hardware
    }
  }
  if (Ethernet.linkStatus() == LinkOFF) {
    #ifdef SERIAL_DEBUG
      Serial.println("Ethernet cable is not connected.");
    #endif
  }
  Udp.begin(2700);
}

void loop() {
  Ethernet.maintain();
  
  int packetSize = Udp.parsePacket();
  char re[3] = {0x00, 0x00, 0x00};
  if (packetSize > 0) {
      Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
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
          case 0xDD:
            msg_counter++;
            // There is probably a better way to do this but I'm too lazy right now to figure it out
            uint32_t states = 0;
            states = (uint32_t)((uint8_t)packetBuffer[1]) << 8;
            states |= (uint32_t)((uint8_t)packetBuffer[2]);
            for(int i = 0; i < (sizeof(pinMapping) / sizeof(pinMapping[0])); i++){
              if (bitRead(states, i) == 1) {
                digitalWrite(pinMapping[i], LOW);
              } else {
                digitalWrite(pinMapping[i], HIGH);
              }
            }
            break;
        }

      if((uint8_t)re[0] != 0x00){
        Udp.beginPacket(Udp.remoteIP(),Udp.remotePort());
        
        Udp.write((const char*)&re, 3);
       
        Udp.endPacket();
      }
    }
        
  }
       
  delay(10);
}
     
