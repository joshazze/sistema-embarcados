#pragma once
// Gravação do Arduino Mega 2560 pelo bootloader STK500v2 ("wiring", 115200 baud).
// Sem dependência do Arduino: a UART, o relógio e o pino de reset entram pela
// interface Port, o que permite testar tudo no host com um bootloader simulado.
//
// Quadro (igual ao avrdude, stk500v2.c): 0x1B, seq, tamanho u16 big-endian, 0x0E,
// corpo, checksum = XOR de todos os bytes anteriores. A resposta repete o seq;
// corpo[0] = comando, corpo[1] = status (0x00 = OK).
#include <stddef.h>
#include <stdint.h>
#include <string.h>

namespace MegaProgrammer {

constexpr uint32_t kMaxImage = 253952;  // 256 KiB de flash menos 8 KiB do bootloader
constexpr uint16_t kPage = 256;         // página do ATmega2560 em bytes
constexpr uint8_t kMessageStart = 0x1B, kToken = 0x0E;
constexpr uint8_t kCmdSignOn = 0x01, kCmdLoadAddress = 0x06, kCmdEnterProgmode = 0x10,
                  kCmdLeaveProgmode = 0x11, kCmdProgramFlash = 0x13, kCmdReadFlash = 0x14;
constexpr uint8_t kStatusOk = 0x00;

enum class Stage : uint8_t { None, Image, SignOn, EnterProgmode, LoadAddress, ProgramFlash, ReadFlash, Verify, LeaveProgmode, Done };

inline const char *stageName(Stage s) {
  switch (s) {
    case Stage::None: return "nenhuma";
    case Stage::Image: return "imagem";
    case Stage::SignOn: return "sign_on";
    case Stage::EnterProgmode: return "enter_progmode";
    case Stage::LoadAddress: return "load_address";
    case Stage::ProgramFlash: return "program_flash";
    case Stage::ReadFlash: return "read_flash";
    case Stage::Verify: return "verificacao";
    case Stage::LeaveProgmode: return "leave_progmode";
    case Stage::Done: return "concluida";
  }
  return "?";
}

// Comparação sem saída antecipada (tempo independe de onde os dados diferem), para MAC.
inline bool constantTimeEqual(const char *a, const char *b, size_t size) {
  uint8_t diff = 0;
  for (size_t i = 0; i < size; ++i) diff |= uint8_t(a[i] ^ b[i]);
  return diff == 0;
}

// Tudo o que depende do hardware. read() devolve 0..255 ou -1 se o tempo acabar.
struct Port {
  virtual ~Port() {}
  virtual void write(const uint8_t *data, size_t size) = 0;
  virtual int read(uint32_t timeoutMs) = 0;
  virtual void flushInput() = 0;          // descarta bytes pendentes (lixo do programa antigo)
  virtual uint32_t millis() = 0;
  virtual void delayMs(uint32_t ms) = 0;
  virtual void setReset(bool active) = 0; // true = Mega em reset
  // Ganchos opcionais: log de tentativa falha e fim de cada página (ponto para ceder CPU).
  virtual void attemptFailed(uint8_t, Stage, const char *, uint32_t) {}
  virtual void pageDone(uint32_t) {}
};

struct Options {
  // Tentativas completas (reset, sign-on, gravação, verificação). Se todas falharem, program()
  // ainda dá o pulso de reset: o Mega fica com a flash parcial rodando e só regravar recupera.
  uint8_t attempts = 3;
  uint16_t resetPulseMs = 50;      // tempo com o Mega em reset
  uint32_t signOnWindowMs = 1500;  // janela para o bootloader responder ao sign-on após o reset
  uint32_t signOnReplyMs = 120;    // espera por resposta de cada sign-on dentro da janela
  uint32_t replyMs = 1000;         // espera pelos demais comandos
};

struct Result {
  bool ok;
  uint8_t attempts;     // tentativas usadas (0 se a imagem foi recusada antes do reset)
  Stage stage;          // etapa da falha (Done se ok)
  const char *reason;   // motivo da falha ("" se ok)
  uint32_t bytes;       // tamanho da imagem recebida
  uint32_t address;     // endereço de byte onde a última falha ocorreu
};

class Programmer {
 public:
  explicit Programmer(Port &port, const Options &options = Options()) : port_(port), opt_(options) {}

  Result program(const uint8_t *image, uint32_t size) {
    Result r = {false, 0, Stage::Image, "", size, 0};
    if (!image || size == 0) { r.reason = "imagem vazia"; return r; }
    if (size > kMaxImage) { r.reason = "imagem grande demais"; return r; }
    uint8_t tries = opt_.attempts ? opt_.attempts : 1;
    for (uint8_t i = 1; i <= tries; ++i) {
      r.attempts = i;
      if (attempt(image, size, r)) {
        pulseReset();  // roda o programa novo
        r.ok = true; r.stage = Stage::Done; r.reason = ""; r.address = 0;
        return r;
      }
      port_.attemptFailed(i, r.stage, r.reason, r.address);
    }
    pulseReset();  // não deixa o Mega preso no bootloader; roda a flash parcial (regravar para recuperar)
    return r;
  }

 private:
  Port &port_;
  Options opt_;
  uint8_t seq_ = 0;
  uint8_t rx_[kPage + 16];
  uint16_t rxSize_ = 0;
  uint8_t page_[kPage];
  uint8_t tx_[10 + kPage];

  void pulseReset() {
    port_.setReset(true);
    port_.delayMs(opt_.resetPulseMs);
    port_.setReset(false);
  }

  bool fail(Result &r, Stage stage, const char *reason, uint32_t address) {
    r.stage = stage; r.reason = reason; r.address = address;
    return false;
  }

  bool attempt(const uint8_t *image, uint32_t size, Result &r) {
    pulseReset();
    // Sign-on repetido dentro da janela do bootloader (ele demora a acordar após o reset).
    uint32_t start = port_.millis();
    const uint8_t signOn[1] = {kCmdSignOn};
    for (;;) {
      port_.flushInput();
      uint32_t sent = port_.millis();
      const char *err = exchange(signOn, sizeof signOn, opt_.signOnReplyMs);
      if (!err) break;
      // Falha rápida (checksum, quadro torto): espera o resto do intervalo antes de insistir.
      uint32_t spent = port_.millis() - sent;
      if (spent < opt_.signOnReplyMs) port_.delayMs(opt_.signOnReplyMs - spent);
      if (uint32_t(port_.millis() - start) >= opt_.signOnWindowMs) return fail(r, Stage::SignOn, err, 0);
    }
    // Parâmetros padrão do avrdude para o m2560: timeout 200, stabdelay 100, cmdexedelay 25,
    // synchloops 32, bytedelay 0, pollvalue 0x53, pollindex 3, pgm_enable AC 53 00 00.
    const uint8_t enter[12] = {kCmdEnterProgmode, 200, 100, 25, 32, 0, 0x53, 3, 0xAC, 0x53, 0x00, 0x00};
    if (const char *err = exchange(enter, sizeof enter, opt_.replyMs)) return fail(r, Stage::EnterProgmode, err, 0);
    for (uint32_t address = 0; address < size; address += kPage) {
      uint32_t n = size - address < kPage ? size - address : kPage;
      memcpy(page_, image + address, n);
      memset(page_ + n, 0xFF, kPage - n);  // última página parcial: completa com flash apagada
      if (const char *err = loadAddress(address)) return fail(r, Stage::LoadAddress, err, address);
      // mode 0xC1 (página, grava), delay 10, cmd1 0x40, cmd2 0x4C, cmd3 0x20, poll 0x00 0x00.
      const uint8_t head[10] = {kCmdProgramFlash, uint8_t(kPage >> 8), uint8_t(kPage & 0xFF), 0xC1, 10, 0x40, 0x4C, 0x20, 0x00, 0x00};
      memcpy(tx_, head, sizeof head);
      memcpy(tx_ + sizeof head, page_, kPage);
      if (const char *err = exchange(tx_, sizeof tx_, opt_.replyMs)) return fail(r, Stage::ProgramFlash, err, address);
      if (const char *err = loadAddress(address)) return fail(r, Stage::LoadAddress, err, address);
      const uint8_t read[4] = {kCmdReadFlash, uint8_t(kPage >> 8), uint8_t(kPage & 0xFF), 0x20};
      if (const char *err = exchange(read, sizeof read, opt_.replyMs)) return fail(r, Stage::ReadFlash, err, address);
      // Resposta: 0x14, status, dados[256], status final.
      if (rxSize_ != kPage + 3 || rx_[kPage + 2] != kStatusOk) return fail(r, Stage::ReadFlash, "resposta de leitura invalida", address);
      for (uint16_t i = 0; i < kPage; ++i)
        if (rx_[2 + i] != page_[i]) return fail(r, Stage::Verify, "dados diferem", address + i);
      port_.pageDone(address + n);
    }
    const uint8_t leave[3] = {kCmdLeaveProgmode, 1, 1};
    if (const char *err = exchange(leave, sizeof leave, opt_.replyMs)) return fail(r, Stage::LeaveProgmode, err, 0);
    return true;
  }

  // Endereço de PALAVRA, com o bit 31 ligado (endereço estendido, como o avrdude faz no m2560).
  const char *loadAddress(uint32_t byteAddress) {
    uint32_t word = (byteAddress >> 1) | 0x80000000UL;
    const uint8_t body[5] = {kCmdLoadAddress, uint8_t(word >> 24), uint8_t(word >> 16), uint8_t(word >> 8), uint8_t(word)};
    return exchange(body, sizeof body, opt_.replyMs);
  }

  // Lê um byte respeitando o prazo; -1 se acabou.
  int readBefore(uint32_t deadline) {
    int32_t left = int32_t(deadline - port_.millis());
    if (left <= 0) return -1;
    return port_.read(uint32_t(left));
  }

  // Envia um comando e espera a resposta com o mesmo seq. nullptr = OK.
  const char *exchange(const uint8_t *body, uint16_t size, uint32_t timeoutMs) {
    const uint8_t seq = ++seq_;
    const uint8_t head[5] = {kMessageStart, seq, uint8_t(size >> 8), uint8_t(size & 0xFF), kToken};
    uint8_t sum = 0;
    for (uint8_t b : head) sum ^= b;
    for (uint16_t i = 0; i < size; ++i) sum ^= body[i];
    port_.write(head, sizeof head);
    port_.write(body, size);
    port_.write(&sum, 1);

    const uint32_t deadline = port_.millis() + timeoutMs;
    const char *pending = nullptr;  // erro de um quadro descartado (seq antigo, quadro torto)
    for (;;) {
      int c = readBefore(deadline);
      if (c < 0) return pending ? pending : "sem resposta";
      if (c != kMessageStart) continue;  // lixo antes do quadro (programa antigo, ruído)
      int rseq = readBefore(deadline), hi = readBefore(deadline), lo = readBefore(deadline), token = readBefore(deadline);
      if (rseq < 0 || hi < 0 || lo < 0 || token < 0) return "resposta incompleta";
      uint16_t n = uint16_t((hi << 8) | lo);
      if (token != kToken || n < 2 || n > sizeof rx_) { pending = "quadro invalido"; continue; }
      uint8_t check = uint8_t(kMessageStart ^ rseq ^ hi ^ lo ^ token);
      for (uint16_t i = 0; i < n; ++i) {
        int b = readBefore(deadline);
        if (b < 0) return "resposta incompleta";
        rx_[i] = uint8_t(b); check ^= uint8_t(b);
      }
      int cks = readBefore(deadline);
      if (cks < 0) return "resposta incompleta";
      if (uint8_t(cks) != check) return "checksum da resposta";
      if (uint8_t(rseq) != seq) { pending = "sequencia errada"; continue; }  // resposta atrasada de outro comando
      rxSize_ = n;
      if (rx_[0] != body[0]) return "resposta de outro comando";
      if (rx_[1] != kStatusOk) return "status de erro";
      return nullptr;
    }
  }
};

}  // namespace MegaProgrammer
