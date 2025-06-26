#include "rfid_functions.h"
#include "servo_actions.h"

/**
 * The implementation of the RFID handling logic.
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