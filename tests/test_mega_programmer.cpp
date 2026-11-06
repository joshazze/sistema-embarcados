// Testa MegaProgrammer.h contra um bootloader STK500v2 simulado (ATmega2560, flash de 256 KiB).
#include "../firmware/Esp32CamRede/MegaProgrammer.h"
#include <cassert>
#include <cstring>
#include <deque>
#include <vector>

using namespace MegaProgrammer;

// Bootloader simulado: mesmo quadro, seq ecoado, checksum XOR e endereço estendido
// (endereço de palavra << 1 em 32 bits, como o stk500boot.c com RAMPZ).
struct SimBootloader {
  std::vector<uint8_t> flash = std::vector<uint8_t>(256 * 1024, 0xA5);  // programa antigo
  bool progmode = false;
  uint32_t address = 0;
  // Estado do parser de entrada.
  std::vector<uint8_t> in;
  // Falhas injetáveis.
  uint32_t readyAfterMs = 0;      // bootloader só escuta depois deste tempo após soltar o reset
  int corruptProgramAt = -1;      // endereço de página cuja primeira gravação sai corrompida
  int badChecksumOnReply = -1;    // índice (global) da resposta com checksum errado; -2 = todas
  int silentAfterCommands = -1;   // para de responder depois de N comandos
  bool wrongSeqOnce = false;      // primeira resposta pós sign-on sai com seq trocado
  // Contadores.
  unsigned commands = 0, replies = 0, signOns = 0, programs = 0, loadAddresses = 0, resetPulses = 0;
  bool sawExtendedBit = true;
  std::vector<uint32_t> programmedAddresses;
};

struct SimPort : Port {
  SimBootloader &boot;
  uint32_t now = 0, releasedAt = 0;
  bool inReset = false;
  std::deque<uint8_t> rx;
  std::vector<unsigned> failedAttempts;
  std::vector<Stage> failedStages;
  unsigned pagesDone = 0;
  explicit SimPort(SimBootloader &b) : boot(b) {}

  void write(const uint8_t *data, size_t size) override {
    for (size_t i = 0; i < size; ++i) feed(data[i]);
  }
  int read(uint32_t timeoutMs) override {
    if (rx.empty()) { now += timeoutMs; return -1; }
    int c = rx.front(); rx.pop_front(); return c;
  }
  void flushInput() override { rx.clear(); }
  uint32_t millis() override { return now; }
  void delayMs(uint32_t ms) override { now += ms; }
  void setReset(bool active) override {
    if (active && !inReset) ++boot.resetPulses;
    if (!active && inReset) { releasedAt = now; boot.progmode = false; boot.in.clear(); }
    inReset = active;
  }
  void attemptFailed(uint8_t attempt, Stage stage, const char *, uint32_t) override {
    failedAttempts.push_back(attempt); failedStages.push_back(stage);
  }
  void pageDone(uint32_t) override { ++pagesDone; }

  void feed(uint8_t c) {
    if (inReset || uint32_t(now - releasedAt) < boot.readyAfterMs) return;  // ainda dormindo
    std::vector<uint8_t> &in = boot.in;
    if (in.empty() && c != kMessageStart) return;
    in.push_back(c);
    if (in.size() < 5) return;
    assert(in[4] == kToken);
    size_t n = (size_t(in[2]) << 8) | in[3];
    assert(n >= 1 && n <= 275);  // buffer do bootloader real: 285 bytes
    if (in.size() < 5 + n + 1) return;
    uint8_t sum = 0;
    for (size_t i = 0; i < 5 + n; ++i) sum ^= in[i];
    assert(sum == in[5 + n]);  // o programador sempre manda checksum certo
    std::vector<uint8_t> body(in.begin() + 5, in.begin() + 5 + n);
    uint8_t seq = in[1];
    in.clear();
    handle(seq, body);
  }

  void reply(uint8_t seq, const std::vector<uint8_t> &body) {
    unsigned index = boot.replies++;
    if (boot.wrongSeqOnce && boot.signOns && body[0] != kCmdSignOn) { boot.wrongSeqOnce = false; seq ^= 0x40; }
    std::vector<uint8_t> f = {kMessageStart, seq, uint8_t(body.size() >> 8), uint8_t(body.size()), kToken};
    f.insert(f.end(), body.begin(), body.end());
    uint8_t sum = 0;
    for (uint8_t b : f) sum ^= b;
    if (boot.badChecksumOnReply == -2 || int(index) == boot.badChecksumOnReply) sum ^= 0xFF;
    f.push_back(sum);
    rx.push_back('x');  // lixo antes do quadro deve ser ignorado
    rx.insert(rx.end(), f.begin(), f.end());
  }

  void handle(uint8_t seq, const std::vector<uint8_t> &b) {
    ++boot.commands;
    if (boot.silentAfterCommands >= 0 && boot.commands > unsigned(boot.silentAfterCommands)) return;
    switch (b[0]) {
      case kCmdSignOn:
        ++boot.signOns;
        reply(seq, {kCmdSignOn, kStatusOk, 8, 'A', 'V', 'R', 'I', 'S', 'P', '_', '2'});
        break;
      case kCmdEnterProgmode:
        assert(b.size() == 12 && b[8] == 0xAC && b[9] == 0x53);
        boot.progmode = true;
        reply(seq, {kCmdEnterProgmode, kStatusOk});
        break;
      case kCmdLoadAddress: {
        assert(b.size() == 5);
        ++boot.loadAddresses;
        if (!(b[1] & 0x80)) boot.sawExtendedBit = false;
        uint32_t word = (uint32_t(b[1]) << 24) | (uint32_t(b[2]) << 16) | (uint32_t(b[3]) << 8) | b[4];
        boot.address = word << 1;  // o bit 31 cai fora no deslocamento, como no bootloader
        reply(seq, {kCmdLoadAddress, kStatusOk});
        break;
      }
      case kCmdProgramFlash: {
        size_t n = (size_t(b[1]) << 8) | b[2];
        assert(b.size() == 10 + n && n == kPage && b[3] == 0xC1);
        if (!boot.progmode) { reply(seq, {kCmdProgramFlash, 0xC0}); break; }
        assert(boot.address % kPage == 0 && boot.address + n <= kMaxImage);
        ++boot.programs; boot.programmedAddresses.push_back(boot.address);
        memcpy(&boot.flash[boot.address], &b[10], n);
        if (int(boot.address) == boot.corruptProgramAt) { boot.flash[boot.address + 7] ^= 0x10; boot.corruptProgramAt = -1; }
        boot.address += n;
        reply(seq, {kCmdProgramFlash, kStatusOk});
        break;
      }
      case kCmdReadFlash: {
        size_t n = (size_t(b[1]) << 8) | b[2];
        assert(b.size() == 4 && n == kPage);
        std::vector<uint8_t> out = {kCmdReadFlash, kStatusOk};
        out.insert(out.end(), boot.flash.begin() + boot.address, boot.flash.begin() + boot.address + n);
        out.push_back(kStatusOk);
        boot.address += n;
        reply(seq, out);
        break;
      }
      case kCmdLeaveProgmode:
        boot.progmode = false;
        reply(seq, {kCmdLeaveProgmode, kStatusOk});
        break;
      default:
        reply(seq, {b[0], 0xC9});  // STATUS_CMD_UNKNOWN
    }
  }
};

std::vector<uint8_t> makeImage(uint32_t size) {
  std::vector<uint8_t> image(size);
  for (uint32_t i = 0; i < size; ++i) image[i] = uint8_t((i * 131u) ^ (i >> 8) ^ ((i >> 16) * 29u));
  return image;
}

void checkFlash(const SimBootloader &boot, const std::vector<uint8_t> &image) {
  uint32_t size = uint32_t(image.size());
  assert(memcmp(boot.flash.data(), image.data(), size) == 0);
  uint32_t end = (size + kPage - 1) / kPage * kPage;
  for (uint32_t i = size; i < end; ++i) assert(boot.flash[i] == 0xFF);  // última página completada
  for (uint32_t i = end; i < boot.flash.size(); ++i) assert(boot.flash[i] == 0xA5);  // resto intocado
}

int main() {
  // 1. Gravação feliz cruzando 64 KiB e 128 KiB, com última página parcial (300 % 256 = 44 bytes).
  {
    SimBootloader boot; SimPort port(boot);
    std::vector<uint8_t> image = makeImage(128 * 1024 + 300);
    Result r = Programmer(port).program(image.data(), uint32_t(image.size()));
    assert(r.ok && r.attempts == 1 && r.stage == Stage::Done && !strcmp(r.reason, "") && r.bytes == image.size());
    checkFlash(boot, image);
    assert(boot.programs == 514 && port.pagesDone == 514);
    assert(boot.programmedAddresses[255] == 0xFF00 && boot.programmedAddresses[256] == 0x10000);
    assert(boot.programmedAddresses[512] == 0x20000 && boot.programmedAddresses[513] == 0x20100);
    assert(boot.sawExtendedBit && boot.loadAddresses == 2 * 514);
    assert(boot.resetPulses == 2 && !port.inReset);  // reset inicial e reset final
    assert(!boot.progmode);  // saiu do modo de programação
  }
  // 2. Imagem de tamanho máximo exato é aceita; um byte a mais é recusado sem tocar no Mega.
  {
    SimBootloader boot; SimPort port(boot);
    std::vector<uint8_t> image = makeImage(kMaxImage);
    Result r = Programmer(port).program(image.data(), kMaxImage);
    assert(r.ok && boot.programs == kMaxImage / kPage);
    checkFlash(boot, image);
    SimBootloader boot2; SimPort port2(boot2);
    std::vector<uint8_t> big(kMaxImage + 1, 0);
    r = Programmer(port2).program(big.data(), kMaxImage + 1);
    assert(!r.ok && r.attempts == 0 && r.stage == Stage::Image && !strcmp(r.reason, "imagem grande demais"));
    assert(boot2.resetPulses == 0 && boot2.commands == 0);
    r = Programmer(port2).program(big.data(), 0);
    assert(!r.ok && r.attempts == 0 && r.stage == Stage::Image && !strcmp(r.reason, "imagem vazia"));
  }
  // 3. Corrupção na gravação é pega na verificação; a segunda tentativa grava tudo certo.
  {
    SimBootloader boot; boot.corruptProgramAt = 0x10100; SimPort port(boot);
    std::vector<uint8_t> image = makeImage(70000);
    Result r = Programmer(port).program(image.data(), uint32_t(image.size()));
    assert(r.ok && r.attempts == 2);
    assert(port.failedAttempts.size() == 1 && port.failedStages[0] == Stage::Verify);
    checkFlash(boot, image);
  }
  // 3b. Corrupção persistente: falha na verificação com endereço do byte errado.
  {
    SimBootloader boot;
    std::vector<uint8_t> image = makeImage(1000);
    Options o; o.attempts = 2;
    // Reinjeta a corrupção a cada tentativa pelo gancho de falha.
    struct Reinject : SimPort {
      using SimPort::SimPort;
      void attemptFailed(uint8_t a, Stage s, const char *m, uint32_t ad) override { SimPort::attemptFailed(a, s, m, ad); boot.corruptProgramAt = 512; }
    } rp(boot);
    boot.corruptProgramAt = 512;
    Result r = Programmer(rp, o).program(image.data(), uint32_t(image.size()));
    assert(!r.ok && r.attempts == 2 && r.stage == Stage::Verify && !strcmp(r.reason, "dados diferem") && r.address == 512 + 7);
    assert(!rp.inReset);
  }
  // 4. Sign-on tardio: o bootloader só acorda 400 ms após o reset; o programador insiste dentro da janela.
  {
    SimBootloader boot; boot.readyAfterMs = 400; SimPort port(boot);
    std::vector<uint8_t> image = makeImage(512);
    Result r = Programmer(port).program(image.data(), 512);
    assert(r.ok && r.attempts == 1 && boot.signOns == 1);
    checkFlash(boot, image);
  }
  // 5. Bootloader mudo: timeout total, 3 tentativas, etapa sign-on; reset liberado no fim.
  {
    SimBootloader boot; boot.readyAfterMs = 100000; SimPort port(boot);
    std::vector<uint8_t> image = makeImage(512);
    Result r = Programmer(port).program(image.data(), 512);
    assert(!r.ok && r.attempts == 3 && r.stage == Stage::SignOn && !strcmp(r.reason, "sem resposta"));
    assert(port.failedAttempts.size() == 3 && boot.resetPulses == 4 && !port.inReset);
    assert(port.now >= 3 * 1500 && port.now < 3 * 1500 + 1000);  // a janela limita a espera
  }
  // 6. Bootloader para no meio da gravação: etapa e motivo reportados.
  {
    SimBootloader boot; boot.silentAfterCommands = 5; SimPort port(boot);
    std::vector<uint8_t> image = makeImage(2048);
    Result r = Programmer(port).program(image.data(), 2048);
    // comandos: sign-on, enter, load, program, load, read (6º, sem resposta); depois ele segue mudo.
    assert(!r.ok && r.attempts == 3 && !strcmp(r.reason, "sem resposta"));
    assert(port.failedStages.size() == 3 && port.failedStages[0] == Stage::ReadFlash && r.stage == Stage::SignOn);
    assert(!port.inReset);
  }
  // 7. Checksum errado na resposta: uma vez => nova tentativa resolve; sempre => falha com motivo.
  {
    SimBootloader boot; boot.badChecksumOnReply = 3; SimPort port(boot);  // resposta do 1º program
    std::vector<uint8_t> image = makeImage(1024);
    Result r = Programmer(port).program(image.data(), 1024);
    assert(r.ok && r.attempts == 2 && port.failedStages[0] == Stage::ProgramFlash);
    checkFlash(boot, image);
    SimBootloader boot2; boot2.badChecksumOnReply = -2; SimPort port2(boot2);
    r = Programmer(port2).program(image.data(), 1024);
    assert(!r.ok && r.attempts == 3 && r.stage == Stage::SignOn && !strcmp(r.reason, "checksum da resposta"));
  }
  // 8. Resposta com seq de outro comando é descartada; sem a resposta certa, vira "sequencia errada".
  {
    SimBootloader boot; boot.wrongSeqOnce = true; SimPort port(boot);
    std::vector<uint8_t> image = makeImage(256);
    Result r = Programmer(port).program(image.data(), 256);
    assert(r.ok && r.attempts == 2 && port.failedStages[0] == Stage::EnterProgmode);
    checkFlash(boot, image);
  }
  // 9. Nomes de etapa usados no JSON.
  assert(!strcmp(stageName(Stage::SignOn), "sign_on") && !strcmp(stageName(Stage::Verify), "verificacao"));
  // 10. Comparação do MAC: igual só se todos os bytes batem (diferença no início, meio ou fim).
  {
    const char a[] = "0123456789abcdef";
    assert(constantTimeEqual(a, "0123456789abcdef", 16));
    assert(!constantTimeEqual(a, "1123456789abcdef", 16));
    assert(!constantTimeEqual(a, "0123456789Abcdef", 16));
    assert(!constantTimeEqual(a, "0123456789abcdee", 16));
    assert(constantTimeEqual(a, "x", 0));
  }
  return 0;
}
