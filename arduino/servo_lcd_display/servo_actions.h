#ifndef SERVO_ACTIONS_H
#define SERVO_ACTIONS_H

#include "config.h" // Include our main configuration

// --- Function Prototypes (Declarations) ---
void executeGoTo(int angle);
void executeSpin(int times);
void executeSweep(int repetitions);
void executeNod(int times);
void executeShake(int times);

#endif // SERVO_ACTIONS_H