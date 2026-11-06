#include "../firmware/MegaControlador/CardStore.h"
#include <cassert>
#include <cstring>
#include <cstdio>
#include <initializer_list>
#include <stdexcept>
struct Memory {
  uint8_t data[4096]; int budget = -1;
  Memory() { memset(data, 0xff, sizeof data); }
  uint8_t read(uint16_t a) { assert(a < sizeof data); return data[a]; }
  void update(uint16_t a, uint8_t v) {
    assert(a < sizeof data);
    if (data[a] == v) return;
    if (budget == 0) throw std::runtime_error("power loss");
    if (budget > 0) --budget;
    data[a] = v;
  }
};
int main() {
  using namespace CardStore;
  // Layout: depois do contador de boot (3134 + 14), 100 slots de 9 bytes, dentro de 4096.
  static_assert(kBase == BootCounter::kRequired, "área de cartões deve começar depois do contador");
  static_assert(kBase == 3148 && kRequired == 4048 && kRequired <= 4096, "layout da EEPROM");
  static_assert(kSlot == 9 && kMaxUid == 7, "tamanho do slot");
  const uint8_t dez[4] = {0xde, 0xad, 0xbe, 0xef};
  const uint8_t sete[7] = {1, 2, 3, 4, 5, 6, 7};
  Memory base;
  Tag got = {}, a = {4, {0xde, 0xad, 0xbe, 0xef, 0, 0, 0}}, b = {7, {1, 2, 3, 4, 5, 6, 7}};
  // Vazio = sem cartão, para todos os ids.
  for (uint8_t id = 1; id <= kUsers; ++id) assert(!read(base, id, got));
  assert(!read(base, 0, got) && !read(base, 101, got));
  // Gravação e leitura; o byte de tamanho e o UID ficam no endereço do slot.
  assert(write(base, 1, a));
  assert(read(base, 1, got) && got.size == 4 && !memcmp(got.uid, a.uid, kMaxUid));
  assert(base.data[kBase] == 4 && !memcmp(base.data + kBase + 1, dez, 4) && base.data[kBase + 5] == 0);
  assert(base.data[kBase + 8] == checksum(1, base.data + kBase));
  // Último slot (id 100) com 7 bytes.
  assert(write(base, 100, b));
  assert(base.data[slotAddress(100)] == 7 && slotAddress(100) == kBase + 99 * kSlot);
  assert(read(base, 100, got) && got.size == 7 && !memcmp(got.uid, sete, 7));
  // O checksum inclui o id: copiar o slot do id 1 para o id 2 não dá cartão.
  memcpy(base.data + slotAddress(2), base.data + slotAddress(1), kSlot);
  assert(!read(base, 2, got));
  // Corrupção de um byte do UID ou do checksum vira "sem cartão".
  Memory corrupt = base;
  corrupt.data[slotAddress(100) + 3] ^= 1;
  assert(!read(corrupt, 100, got));
  corrupt = base; corrupt.data[slotAddress(100) + 8] ^= 0x80;
  assert(!read(corrupt, 100, got));
  // Tamanho inválido (0, 8, 0xFF) vira "sem cartão", mesmo com dados que pareçam íntegros.
  const uint8_t tamanhos[3] = {0, 8, 0xff};
  for (uint8_t s : tamanhos) {
    corrupt = base; corrupt.data[slotAddress(1)] = s;
    assert(!read(corrupt, 1, got));
  }
  // Busca: mesmo tamanho e mesmos bytes; tamanho diferente não casa.
  assert(find(base, dez, 4) == 1);
  assert(find(base, dez, 7) == 0);
  assert(find(base, sete, 7) == 100);
  assert(find(base, dez, 0) == 0 && find(base, dez, 8) == 0);
  const uint8_t outro[4] = {0xde, 0xad, 0xbe, 0x00};
  assert(find(base, outro, 4) == 0);
  // Gravar de novo o mesmo cartão para o mesmo usuário é aceito; trocar substitui.
  assert(write(base, 1, a) && find(base, dez, 4) == 1);
  Tag c = {5, {9, 9, 9, 9, 9, 0, 0}};
  assert(write(base, 1, c) && find(base, dez, 4) == 0 && find(base, c.uid, 5) == 1);
  assert(write(base, 1, a));
  // Limpar tira o cartão; id fora da faixa não grava nem limpa.
  assert(clear(base, 1) && !read(base, 1, got) && find(base, dez, 4) == 0);
  Tag invalido = {0, {}}, grande = {8, {}};
  assert(!write(base, 3, invalido) && !write(base, 3, grande));
  assert(!write(base, 0, a) && !write(base, 101, a) && !clear(base, 0) && !clear(base, 101));
  assert(!read(base, 3, got));
  // Gravar cartões não altera a área de usuários nem o contador de boot.
  Memory before;
  for (uint16_t i = 0; i < kBase; ++i) before.data[i] = uint8_t(i * 7 + 3);
  Memory after = before;
  for (uint8_t id = 1; id <= kUsers; ++id) {
    Tag t = {7, {uint8_t(id), 2, 3, 4, 5, 6, uint8_t(id ^ 0x5a)}};
    assert(write(after, id, t));
  }
  assert(!memcmp(before.data, after.data, kBase));
  for (uint8_t id = 1; id <= kUsers; ++id) {
    assert(read(after, id, got) && got.uid[0] == id && got.uid[6] == uint8_t(id ^ 0x5a));
  }
  assert(find(after, sete, 7) == 0 && find(after, after.data + slotAddress(42) + 1, 7) == 42);
  // Queda de energia em qualquer ponto da troca de cartão: o slot tem o cartão antigo, o novo, ou nenhum.
  for (int cut = 0; cut < 40; ++cut) {
    Memory mem = base; mem.budget = cut;
    try { write(mem, 1, c); } catch (const std::runtime_error &) {}
    mem.budget = -1;
    Tag r = {};
    if (read(mem, 1, r)) {
      const bool antigo = r.size == 4 && !memcmp(r.uid, dez, 4);
      const bool novo = r.size == 5 && !memcmp(r.uid, c.uid, 5);
      assert(antigo || novo);
    }
    assert(read(mem, 100, r) && r.size == 7);
  }
  puts("card store: layout, checksum, empty/corrupt slots, uniqueness and power-cut checks passed");
}
