#ifndef RFID_FUNCTIONS_H
#define RFID_FUNCTIONS_H

#include "config.h" // Include main configuration for access to states, timers, etc.

/**
 * @brief Checks for a new RFID card and handles the detection event.
 * 
 * This function should be called repeatedly in the main loop. If a new card
 * is detected, it updates the system state, displays the UID on the LCD,
 * triggers a physical feedback action (nod), and halts the card to prevent
 * immediate re-scans.
 */
void handleRfid();

#endif // RFID_FUNCTIONS_H