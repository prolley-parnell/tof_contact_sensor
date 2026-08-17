#include <Wire.h>
#include <math.h>

// --- Pin Definitions ---
//If not in mount use reset pin A3
// #define SWITCH_RESET_PIN A3
#define SWITCH_RESET_PIN_1 7
#define SWITCH_RESET_PIN_2 8


// --- I2C Addresses ---
#define VCNL_ADDR      0x60
#define TCA_ADDR_1     0x70
#define TCA_ADDR_2     0x71

// --- VCNL36825T Registers ---
#define VCNL_PS_CONF1  0x00 // High: Calibration and on/off, Low: Initialisation
#define VCNL_PS_CONF2  0x03 // 
#define VCNL_PS_CONF3  0x04 // Force mode and sunlight protect interrupt setting
#define VCNL_PS_CONF4  0x08 // High: Auto calibration period, number, interrupt setting Low: Low power mode setting
#define VCNL_PS_CANC   0x07 // Proximity sensor cancellation setting, essentially used as a tare button
#define VCNL_PS_DATA   0xF8 // Read only from proximity sensor
#define VCNL_INT_FLAG  0xF9 // Read the interrupt flags


void setup() {
  Serial.begin(115200);
  while (!Serial);
  Wire.begin();

  // Enable Switches
  pinMode(SWITCH_RESET_PIN_1, OUTPUT); // Set the pin as an output
  pinMode(SWITCH_RESET_PIN_2, OUTPUT); // Set the pin as an output
  delay(100);

  // Initialize sensors
  for (int j = 0; j < 2; j++)  {
    for (int i = 0; i < 16; i++) {
      initVCNL(j, i);
      selectChannel(j, i, 0);
    }
  }
  
  Serial.println("System Ready.");
  Serial.println("Commands:");
  Serial.println("  'r' = Read distance (mm)");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.equalsIgnoreCase("r")) {
      readAllSensors();
    }
  }
}

// --- Action Functions ---

void readAllSensors() {
  for (int j = 0; j < 2; j++) {
  // uint8_t finger_address = "L";
    for (int i = 0; i < 16; i++) {
      if (!selectChannel(j, i, 1)) {
        Serial.print("S");
        Serial.print(j);
        Serial.print("-");
        Serial.print(i+1);
        Serial.print(":");
        Serial.print("E\t");
      }
      else{
        uint16_t counts = readProximity();
        Serial.print("S");
        Serial.print(j);
        Serial.print("-");
        Serial.print(i+1);
        Serial.print(":");
        Serial.print(counts);
        Serial.print("\t");
      }
      
      disableAllSwitches();
      // selectChannel(j, i, 0);
    }
  }
  Serial.println();
}

// void enableSunlightCancel() {
//   Serial.println("Enabling Sunlight Cancellation...");
//   for (int i = 0; i < 16; i++) {
//     selectChannel(i, 1);
//     uint16_t conf3 = readVCNLReg(VCNL_PS_CONF3);
//     conf3 |= 0xE000;
//     writeVCNLReg(VCNL_PS_CONF3, conf3);
//     // disableAllSwitches();
//     selectChannel(i, 0);
//   }
//   Serial.println("Done.");
// }

// --- Low Level Functions ---

bool selectChannel(int finger, int sensorNum, bool state) { // This initialises or ends the communications
  // Allow checking of left or right sensor
  if (finger == 0) { // If the sensor is on the first finger
    digitalWrite(SWITCH_RESET_PIN_1, HIGH); // Set the reset to high
    digitalWrite(SWITCH_RESET_PIN_2, LOW); // Set the reset to high
  }
  else {
    digitalWrite(SWITCH_RESET_PIN_1, LOW); // Set the reset to high
    digitalWrite(SWITCH_RESET_PIN_2, HIGH); // Set the reset to high
  }
  uint8_t switchAddr = (sensorNum < 8) ? TCA_ADDR_1 : TCA_ADDR_2; //If the sensor is number 0 : 7, use address 1, else use address 2
  uint8_t channelNum = sensorNum % 8; // Cap the sensor index between 0 : 7

  Wire.beginTransmission(switchAddr);
  Wire.write(state << channelNum); // Write a 1 to the sensor address you want to read
  return (Wire.endTransmission() == 0);
}

void initVCNL(int side, int index) {
  selectChannel(side, index, 1);
  writeVCNLReg(VCNL_PS_CANC, 0x0000); // Reset the tare
  writeVCNLReg(VCNL_PS_CONF1, 0x0283); //Byte low = 10000011 Power on, enable bias circuit (PS_ON), Byte high = 00000010
  delay(10);
  writeVCNLReg(VCNL_PS_CONF2, 0xC000); // Byte low = 00000000 PS_Period = 10ms, PS_Pers = 1, PS_INT = interrupt disable, PS_SMART_PERS = disable smart persistence, PS_ST = PS start
  writeVCNLReg(VCNL_PS_CONF3, 0x1668); // Byte low = 01001000 PS_AF = Enable force mode, PS_TRIG = 0, no force trigger, PS_FORCENUM = one detect cycle, PS_SP_INT = disable sunlight protection

}

void disableAllSwitches() { // For one side only- whichever is active
  Wire.beginTransmission(TCA_ADDR_1); Wire.write(0); Wire.endTransmission();
  Wire.beginTransmission(TCA_ADDR_2); Wire.write(0); Wire.endTransmission();
}

uint16_t readProximity() { //Assumes the correct sensor has already been activated by selectChannel
  writeVCNLReg(VCNL_PS_CONF3, 0x1668); //  Data byte high 0x16 which is 00010110 = Set I_VCSEL to 18mA, and set PS output to 16 bits
  // Data byte low 0110100 PS_AF = Force mode, PS_TRIG = 1 = Trigger one time cycle (pull high), PS_FORCENUM = 0 = Detect 1 cycle after trigger, PS_SP_INT = 1 = PS Sunlight protect
  delay(5);
  return readVCNLReg(VCNL_PS_DATA);
}

bool writeVCNLReg(uint8_t reg, uint16_t data) {
  Wire.beginTransmission(VCNL_ADDR);
  Wire.write(reg); // Assume that each write has space for 1 clock cycle in between
  Wire.write(data & 0xFF); // Data byte low
  Wire.write((data >> 8) & 0xFF); // Data byte high
  return (Wire.endTransmission() == 0);
}

uint16_t readVCNLReg(uint8_t reg) { // Write to device
  Wire.beginTransmission(VCNL_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return 65535;

  Wire.requestFrom(VCNL_ADDR, 2); // If the transmission did not fail, read 2 bytes
  unsigned long startTime = millis();
  while (Wire.available() < 2) {
    if (millis() - startTime > 100) return 65535; // If waiting while the device is available for longer than 100ms then fail
  }
  uint16_t data = Wire.read();
  data |= (Wire.read() << 8);
  return data;
}