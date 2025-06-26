#include "rfid_functions.h"
#include "servo_actions.h"

/**
 * Handles RFID scanning specifically for the authentication phase.
 */
void handleAuthenticationScan() {
  // Look for new cards
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    
    // A card has been detected!
    Serial.print("Card detected for auth! UID:"); // Note the prefix matches Python's expectation
    String uidString = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      if(mfrc522.uid.uidByte[i] < 0x10) {
        uidString += "0";
      }
      uidString += String(mfrc522.uid.uidByte[i], HEX);
    }
    uidString.toUpperCase();
    Serial.println(uidString); // Send the UID to the Python script

    // Halt PICC to prevent reading the same card repeatedly right away
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
  }
}

/**
 * The implementation of the normal RFID handling logic.
 */
void handleRfid() {
  // Look for new cards, but only if one isn't already being displayed
  if (currentDisplayState != RFID_DETECTED && mfrc522.PICC_IsNewCardPresent()) {
    
    // Select one of the cards
    if (mfrc522.PICC_ReadCardSerial()) {
      
      // --- A card has been detected! ---
      Serial.print("Card detected! UID: ");
      String uidString = "";
      for (byte i = 0; i < mfrc522.uid.size; i++) {
        // Add a leading zero if the hex value is smaller than 10
        if(mfrc522.uid.uidByte[i] < 0x10) {
          uidString += "0";
        }
        uidString += String(mfrc522.uid.uidByte[i], HEX);
      }
      Serial.println(uidString);
      uidString.toUpperCase();

      // Update state and display
      currentDisplayState = RFID_DETECTED;
      rfidDisplayStartTime = millis();
      lcd.clear();
      lcd.setCursor(0,0);
      lcd.print("Card Scanned!");
      lcd.setCursor(0,1);
      lcd.print("UID: " + uidString);

      // Give physical feedback by nodding
      executeNod(1);

      // Halt PICC and stop encryption to prevent reading the same card repeatedly
      mfrc522.PICC_HaltA();
      mfrc522.PCD_StopCrypto1();
    }
  }
}