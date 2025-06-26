/*
 * MFRC522 RFID Reader - Basic Test Sketch
 * 
 * This sketch verifies that the MFRC522 module is correctly wired and functional.
 * It reads the Unique ID (UID) of an RFID tag and prints it to the Serial Monitor.
 * 
 * Required Library:
 * - MFRC522 by GithubCommunity (install from Arduino IDE Library Manager)
 * 
 * Wiring (as per previous recommendation):
 * - MFRC522 VCC -> Arduino 3.3V (Important: NOT 5V)
 * - MFRC522 RST -> Arduino Pin 8
 * - MFRC522 GND -> Arduino GND
 * - MFRC522 MISO -> Arduino Pin 12 (Hardware SPI)
 * - MFRC522 MOSI -> Arduino Pin 11 (Hardware SPI)
 * - MFRC522 SCK  -> Arduino Pin 13 (Hardware SPI)
 * - MFRC522 SDA(SS) -> Arduino Pin 7
 */

#include <SPI.h>
#include <MFRC522.h>

// Define the pins used for the MFRC522 reader
#define SS_PIN 7  // Slave Select (SDA) pin
#define RST_PIN 8 // Reset pin

// Create an instance of the MFRC522 reader
MFRC522 mfrc522(SS_PIN, RST_PIN);  

void setup() {
  // Start serial communication for debugging
  Serial.begin(9600);
  while (!Serial); // Wait for the serial port to connect (needed for some Arduinos)

  // Initialize the SPI bus
  SPI.begin();      
  
  // Initialize the MFRC522 reader
  mfrc522.PCD_Init();   
  
  Serial.println("RFID Reader Test Sketch");
  Serial.println("-----------------------");
  Serial.println("Scan a card or tag to read its UID...");
  Serial.println();
}

void loop() {
  // Look for new cards. If a new card is not detected, exit the loop.
  if ( ! mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Select one of the cards. If the card could not be read, exit the loop.
  if ( ! mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // If a card is found and read, print its UID to the Serial Monitor
  Serial.print("Card UID: ");
  String content = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(mfrc522.uid.uidByte[i], HEX);
    content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " "));
    content.concat(String(mfrc522.uid.uidByte[i], HEX));
  }
  Serial.println();
  Serial.println();
  
  // Halt PICC (stops communication with the card) to allow for new card reads
  mfrc522.PICC_HaltA();
  
  // Add a small delay to avoid spamming the serial monitor if the card is held near the reader
  delay(1000); 
}
