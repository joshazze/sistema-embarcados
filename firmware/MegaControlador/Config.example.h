#pragma once
#include <Arduino.h>
// Exemplo para compilação. Copie para Config.h ignorado e altere a senha.
constexpr char ADMIN_PIN[] = "0000000000";
constexpr uint8_t LOCK_MODE = 0, LOCK_PIN = 35, LOCK_ON = HIGH;
constexpr uint32_t LOCK_PULSE_MS = 200;
constexpr uint8_t BUZZER_PIN = 36;
// LCD 1602 em modo 4 bits (sem I2C). Pinos padrão RS=D37 E=D38 D4=D39 D5=D40 D6=D41 D7=D42; para mudar, use #define LCD_PIN_RS 43 etc. (não constexpr). RW do LCD vai no GND.
constexpr uint8_t BUTTON_1 = 30, BUTTON_2 = 31, LED_R = 32, LED_G = 33, LED_B = 34;
constexpr bool RGB_COMMON_ANODE = false;
const byte ROW_PINS[4] = {22,23,24,25}, COL_PINS[4] = {26,27,28,29};
constexpr uint8_t MAX_USERS = 100;
constexpr uint32_t ENTRY_MS = 60000, OPEN_MS = 300000, UI_TIMEOUT_MS = 60000;
// Espelho do LCD na serial USB: imprime "LCD| <linha1> | <linha2>" quando o texto muda (ativo por padrão, mesmo sem LCD).
// #define LCD_SERIAL_MIRROR 0  // desliga o espelho do LCD na serial USB
// Bancada: descomente para o espelho "LCD| ..." da serial mostrar a senha digitada (o LCD continua com *). Não cole esses logs em chats.
// #define SHOW_TYPED_DIGITS 1
