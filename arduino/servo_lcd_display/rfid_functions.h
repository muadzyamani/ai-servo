#ifndef RFID_FUNCTIONS_H
#define RFID_FUNCTIONS_H

#include "config.h" 

/**
 * @brief Handles scanning for a card during the initial authentication phase.
 * If a card is found, its UID is printed to the Serial port for Python to read.
 */
void handleAuthenticationScan();

/**
 * @brief Checks for a new RFID card during normal operation.
 * Displays UID on LCD and performs a nod action.
 */
void handleRfid();

#endif // RFID_FUNCTIONS_H