#include "../firmware/shared/MessageProtocol.h"
#include <cassert>
#include <cstdio>
int main() {
  using namespace MessageProtocol;
  EventData e = {0x12345678, 42, 0xffffffffUL, 0, AccessGranted, 100, Fingerprint, 1, 0, 1};
  uint8_t bytes[kEventLength];
  assert(encodeEvent(e, bytes, sizeof bytes));
  assert(bytes[2] == 0x78 && bytes[3] == 0x56 && bytes[4] == 0x34 && bytes[5] == 0x12);
  EventData decoded = {};
  assert(decodeEvent(bytes, sizeof bytes, decoded));
  assert(decoded.messageId == e.messageId && decoded.boot == e.boot && decoded.uptime == e.uptime);
  assert(decoded.kind == AccessGranted && decoded.user == 100 && decoded.method == Fingerprint && decoded.epoch == 0);
  assert(!decodeEvent(bytes, sizeof bytes - 1, decoded));
  bytes[19] = 101; assert(!decodeEvent(bytes, sizeof bytes, decoded));
  e.epoch = 1; assert(!encodeEvent(e, bytes, sizeof bytes));
  e.epoch = 1700000000UL; assert(encodeEvent(e, bytes, sizeof bytes));
  // Valores novos (cartão RFID) ficam no fim das enumerações: CardLinked = 17, Card = 9.
  assert(CardLinked == 17 && KeypadLocked == 18 && Card == 9 && Web == 8 && EnrollFailed == 16);
  EventData card = {0x01020304, 7, 1000, 0, CardLinked, 2, Admin, 1, 0, 0};
  uint8_t cardBytes[kEventLength];
  assert(encodeEvent(card, cardBytes, sizeof cardBytes) && cardBytes[18] == 17);
  EventData cardBack = {};
  assert(decodeEvent(cardBytes, sizeof cardBytes, cardBack) && cardBack.kind == CardLinked);
  card.method = Card; card.kind = AccessDenied; card.reason = 17;
  assert(encodeEvent(card, cardBytes, sizeof cardBytes) && cardBytes[20] == 9);
  assert(decodeEvent(cardBytes, sizeof cardBytes, cardBack) && cardBack.method == Card);
  card.method = Card + 1; assert(!encodeEvent(card, cardBytes, sizeof cardBytes));
  card.method = Card; card.kind = KeypadLocked + 1; assert(!encodeEvent(card, cardBytes, sizeof cardBytes));
  // keypad_locked (B4) fica logo após card_linked: índice 18, método teclado (4), motivo invalid_pin (2).
  EventData locked = {0x01020304, 7, 1000, 0, KeypadLocked, 0, Keypad, 0, 2, 0};
  assert(encodeEvent(locked, cardBytes, sizeof cardBytes) && cardBytes[18] == 18 && cardBytes[20] == 4);
  EventData lockedBack = {};
  assert(decodeEvent(cardBytes, sizeof cardBytes, lockedBack) && lockedBack.kind == KeypadLocked);
  card.kind = 0; assert(!encodeEvent(card, cardBytes, sizeof cardBytes));
  puts("message protocol: encoding and validation passed");
}
