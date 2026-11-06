#pragma once
#include <stdint.h>
#include <string.h>
#include "BootCounter.h"

// Cartões RFID (UID de 1 a 7 bytes). Área própria da EEPROM, depois do contador de boot.
// Um slot por usuário, sem sal: o UID não é segredo e a busca compara bytes direto.
// Slot de 9 bytes: [0] tamanho do UID (1..7; 0 ou 0xFF = sem cartão), [1..7] UID com
// zeros à direita, [8] CRC-8 que cobre o id e os bytes 0..7. Slot vazio, com tamanho
// inválido ou com CRC errado conta como sem cartão.
// O CRC é de 8 bits porque 16 bits não cabem: 100 slots de 10 bytes não cabem após o
// contador de boot nos 4096 bytes do ATmega2560.
namespace CardStore {
constexpr uint8_t kUsers = 100, kMaxUid = 7, kSlot = 9;
constexpr uint16_t kBase = BootCounter::kRequired;
constexpr uint16_t kRequired = kBase + uint16_t(kUsers) * kSlot;
static_assert(kRequired <= 4096, "EEPROM overflow: área de cartões passa de 4096 bytes");
struct Tag { uint8_t size; uint8_t uid[kMaxUid]; };

inline uint8_t crc8(const uint8_t *data, uint8_t len, uint8_t value = 0) {
  while (len--) {
    value ^= *data++;
    for (uint8_t bit = 0; bit < 8; ++bit)
      value = value & 0x80 ? uint8_t((value << 1) ^ 0x07) : uint8_t(value << 1);
  }
  return value;
}
inline uint8_t checksum(uint8_t id, const uint8_t *slot) {
  return crc8(slot, kSlot - 1, crc8(&id, 1));
}
inline uint16_t slotAddress(uint8_t id) { return kBase + uint16_t(id - 1) * kSlot; }
inline bool validSize(uint8_t size) { return size >= 1 && size <= kMaxUid; }

// true só se o slot tem um cartão íntegro. Vazio ou corrompido devolve false.
template <class E> bool read(E &e, uint8_t id, Tag &tag) {
  if (id < 1 || id > kUsers) return false;
  const uint16_t base = slotAddress(id);
  uint8_t slot[kSlot];
  for (uint8_t i = 0; i < kSlot; ++i) slot[i] = e.read(base + i);
  if (!validSize(slot[0]) || slot[kSlot - 1] != checksum(id, slot)) return false;
  tag.size = slot[0];
  memcpy(tag.uid, slot + 1, kMaxUid);
  return true;
}
// Grava o cartão do id e confere a releitura. Falha em qualquer ponto deixa o slot sem cartão.
template <class E> bool write(E &e, uint8_t id, const Tag &tag) {
  if (id < 1 || id > kUsers || !validSize(tag.size)) return false;
  uint8_t slot[kSlot] = {};
  slot[0] = tag.size;
  memcpy(slot + 1, tag.uid, tag.size);
  slot[kSlot - 1] = checksum(id, slot);
  const uint16_t base = slotAddress(id);
  // Invalida antes; o tamanho é o último byte gravado. Queda de energia no meio = sem cartão.
  e.update(base, 0xff);
  for (uint8_t i = 1; i < kSlot; ++i) e.update(base + i, slot[i]);
  e.update(base, slot[0]);
  Tag check;
  return read(e, id, check) && check.size == tag.size && !memcmp(check.uid, tag.uid, tag.size);
}
// Remove o cartão do id (volta a 0xFF no tamanho). Usado para desfazer um cadastro que falhou.
template <class E> bool clear(E &e, uint8_t id) {
  if (id < 1 || id > kUsers) return false;
  e.update(slotAddress(id), 0xff);
  return true;
}
// Id do dono do UID, ou 0 se nenhum slot íntegro tem esse UID (mesmo tamanho e mesmos bytes).
template <class E> uint8_t find(E &e, const uint8_t *uid, uint8_t size) {
  if (!validSize(size)) return 0;
  for (uint8_t id = 1; id <= kUsers; ++id) {
    Tag tag;
    if (read(e, id, tag) && tag.size == size && !memcmp(tag.uid, uid, size)) return id;
  }
  return 0;
}
} // namespace CardStore
