#ifndef DISPLAY_FUNCTIONS_H
#define DISPLAY_FUNCTIONS_H

#include "config.h" // Include our main configuration

// --- Function Prototypes (Declarations) ---
void displayWelcomeMessage();
void displayIdle();
void displayThinking();
void displayActionStatus(String line1, String line2);

#endif // DISPLAY_FUNCTIONS_H