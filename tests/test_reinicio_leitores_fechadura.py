"""Ruído da fechadura (bancada 06/11/2026): reinício dos leitores e filtro dos sensores de porta.

(1) 1 s depois que a saída da fechadura volta a LOW, e de novo 3 s depois disso, o
    RC522 (PCD_Init) e o DY50 (UART + handshake) são reiniciados, sem travar o loop.
(2) Ruído de 50 ms nos sensores D30/D31 não gera door_opened, door_closed nem forced_open.
(3) Abertura e fechamento reais (estáveis por 200 ms) ainda geram os eventos.

Funções reais recortadas do .ino (doorTick, outputsTick, rfidReinit, fingerprintHandshake,
readerResetTick) com dublês de hardware. Config.h nunca é lido: usa-se Config.example.h.
"""
import unittest

from test_mega_tst02 import AJUDANTES_HW, PREFIXO_HW, _executar, _ler_ino, _pecas_hw, _trecho

# Dublês do RC522, do DY50, das seriais e do link da CAM, com a ordem das chamadas.
DUBLES = r'''
#define F(s) s
constexpr int FINGERPRINT_OK = 0;
bool fingerprintReady = false;
std::vector<std::string> ordem;
int linkTicks = 0;
void linkTick(bool) { ++linkTicks; ordem.push_back("link"); }
struct MFRC522 {
 enum PCD_Register { VersionReg = 0x37 << 1 };
 int inits = 0; uint8_t version = 0x82;
 void PCD_Init() { ++inits; ordem.push_back("rfid"); }
 uint8_t PCD_ReadRegister(PCD_Register) { return version; }
} rfid;
struct Finger {
 int verifyCalls = 0; bool verifyOk = true; uint16_t capacity = 200;
 bool verifyPassword() { ++verifyCalls; ordem.push_back("dy50"); return verifyOk; }
 uint8_t getParameters() { return FINGERPRINT_OK; }
} finger;
struct SerialMock {
 std::string log;
 void print(const char *s) { log += s; }
 void println(const char *s) { log += s; log += "\n"; }
} Serial;
struct Serial1Mock { int begins = 0; void begin(uint32_t) { ++begins; ordem.push_back("uart"); } } Serial1;
'''

# Um passo do loop real (ordem do loop()): porta, saídas e o agendador de reinício.
LOOP = r'''
static void ciclo(uint32_t t) { now = t; doorTick(); outputsTick(); readerResetTick(); }
static void ate(uint32_t t) { while (now < t) ciclo(now + 5 > t ? t : now + 5); }
static int resets() { return rfid.inits; }
'''


def _pecas_reinicio(src):
    return (_trecho(src, 'bool fingerprintHandshake()', 'void fingerprintRecoveryTick()')
            + _trecho(src, 'bool rfidVersionOk()', '// Religa o RC522')
            + src[src.index('// Reinício dos leitores após a fechadura (bancada'):])


def _fonte(main):
    src = _ler_ino()
    return PREFIXO_HW + DUBLES + _pecas_hw(src) + _pecas_reinicio(src) + AJUDANTES_HW + LOOP + main


# ---------------------------------------------------------------- (1) reinício dos leitores
MAIN_REINICIO = r'''
int main() {
 fecha(true);
 rawClosed = stableClosed = true; rawSince = 0; door.begin(true, 0); resetUi(); noticeDuration = 0;
 const int MODO = LOCK_MODE;
 ate(1000); assert(resets() == 0 && readerResetStage == 0);
 door.authorize(7, 1000); authorizationAt = 1000; accessMethod = "password"; buzzer.reset();
 if (MODO == 0) {
  // Simulação: a saída nunca energiza, nada é agendado.
  ate(70000); assert(resets() == 0 && finger.verifyCalls == 0 && Serial1.begins == 0);
  return 0;
 }
 // Modo 1: a saída cai no fim do pulso (1000 + LOCK_PULSE_MS). Modo 2: cai quando a porta abre
 // (borda dos sensores em 3000 + 200 ms de debounce = 3200).
 if (MODO == 2) { ate(3000); assert(trava() == 1 && readerResetStage == 0); fecha(false); ciclo(now); }
 const uint32_t solta = MODO == 1 ? 1000 + LOCK_PULSE_MS : 3200;
 ate(solta - 5); assert(trava() == 1 && readerResetStage == 0);
 ate(solta); assert(trava() == 0 && readerResetStage == 1 && lockReleasedAt == solta);
 // Até 1 s depois, o loop segue sem tocar nos leitores (nada bloqueia).
 ate(solta + 995); assert(resets() == 0 && finger.verifyCalls == 0 && linkTicks == 0);
 if (MODO == 2) assert(door.state == DoorState::Open && audits.back() == "door_opened|7|password|");
 // 1º reinício em solta + 1000: CAM atendida antes do RC522, depois UART e handshake do DY50.
 ate(solta + 1000);
 assert(resets() == 1 && finger.verifyCalls == 1 && Serial1.begins == 1 && readerResetStage == 2);
 assert(ordem.size() == 5 && ordem[0] == "link" && ordem[1] == "rfid" && ordem[2] == "link"
        && ordem[3] == "uart" && ordem[4] == "dy50");
 assert(rfidReady && fingerprintReady && lastRfidRecovery == solta + 1000 && lastFingerRecovery == solta + 1000);
 assert(Serial.log == "RFID reiniciado ok\nDY50 reiniciado ok\n");
 // 2º reinício 3 s depois do primeiro, e só ele.
 ate(solta + 3995); assert(resets() == 1 && finger.verifyCalls == 1);
 ate(solta + 4000); assert(resets() == 2 && finger.verifyCalls == 2 && Serial1.begins == 2 && readerResetStage == 0);
 ate(solta + 20000); assert(resets() == 2 && finger.verifyCalls == 2);
 // Leitor que não responde: estado indisponível e log de falha (a recuperação periódica segue).
 ordem.clear(); Serial.log.clear();
 readerResetStage = 1; lockReleasedAt = now; rfid.version = 0x00; finger.verifyOk = false;
 ate(now + 1000);
 assert(!rfidReady && !fingerprintReady && Serial.log == "RFID reiniciado sem resposta\nDY50 reiniciado sem resposta\n");
 // Modo 1, novo pulso com reinício vencido pendente: não roda com a fechadura energizada;
 // a nova queda reagenda o 1º reinício para 1 s depois dela.
 if (MODO == 1) {
  rfid.version = 0x82; finger.verifyOk = true; readerResetStage = 1; lockReleasedAt = now - 5000;
  door.begin(true, now); const uint32_t p = now; door.authorize(7, p); authorizationAt = p;
  const int antes = resets();
  ciclo(p); assert(lockEnergized && resets() == antes);
  ate(p + LOCK_PULSE_MS - 5); assert(resets() == antes);
  ate(p + LOCK_PULSE_MS); assert(!lockEnergized && lockReleasedAt == p + LOCK_PULSE_MS && readerResetStage == 1);
  ate(p + LOCK_PULSE_MS + 995); assert(resets() == antes);
  ate(p + LOCK_PULSE_MS + 1000); assert(resets() == antes + 1);
 }
 return 0;
}
'''

# ---------------------------------------------------------------- (2)/(3) ruído e abertura real
MAIN_RUIDO = r'''
// Alterna a leitura bruta a cada 50 ms durante `ms`, com o loop rodando a cada 5 ms.
static void ruido(uint32_t ms) {
 const uint32_t fim = now + ms; bool aberta = true;
 while (now < fim) { fecha(!aberta); ate(now + 50 > fim ? fim : now + 50); aberta = !aberta; }
 fecha(true);
}
int main() {
 fecha(true);
 rawClosed = stableClosed = true; rawSince = 0; door.begin(true, 0); resetUi(); noticeDuration = 0;
 ate(1000);
 // (2a) porta fechada em repouso: 1 s de ruído de 50 ms não gera forced_open
 ruido(1000); ate(now + 500);
 assert(door.state == DoorState::Idle && stableClosed && audits.empty());
 // (2b) acesso liberado: o ruído não vira door_opened
 door.authorize(7, now); authorizationAt = now; accessMethod = "password"; buzzer.reset();
 ruido(1000); ate(now + 500);
 assert(door.state == DoorState::AwaitOpen && audits.empty());
 // (3a) abertura real: aceita exatamente 200 ms após a borda, com door_opened
 fecha(false); ciclo(now); const uint32_t a = now;  // borda lida neste ciclo
 ate(a + 195);
 assert(door.state == DoorState::AwaitOpen && audits.empty());
 ate(a + 200);
 assert(door.state == DoorState::Open && audits.size() == 1 && audits[0] == "door_opened|7|password|");
 // (2c) porta aberta: ruído para "fechada" de 50 ms não gera door_closed
 { const uint32_t fim = now + 1000; bool fechada = true;
   while (now < fim) { fecha(fechada); ate(now + 50); fechada = !fechada; } }
 fecha(false); ate(now + 500);
 assert(door.state == DoorState::Open && audits.size() == 1);
 // (3b) fechamento real gera door_closed em +200 ms
 fecha(true); ciclo(now); const uint32_t c = now; ate(c + 195); assert(door.state == DoorState::Open);
 ate(c + 200); assert(door.state == DoorState::Idle && audits.back() == "door_closed|7|password|");
 // (3c) abertura sem autorização mantida: forced_open em +200 ms
 audits.clear(); ate(now + 3000);
 fecha(false); ciclo(now); const uint32_t f = now; ate(f + 195); assert(audits.empty());
 ate(f + 200); assert(door.state == DoorState::Alarm && audits.size() == 1 && audits[0] == "forced_open|0|sensor|");
 return 0;
}
'''


class ReinicioLeitoresTests(unittest.TestCase):
    def test_reinicios_1s_e_3s_apos_a_fechadura_sem_bloquear(self):
        for modo in (0, 1, 2):
            with self.subTest(lock_mode=modo):
                _executar(_fonte(MAIN_REINICIO), lock_mode=modo)


class RuidoSensoresPortaTests(unittest.TestCase):
    def test_ruido_de_50_ms_nao_gera_eventos_e_abertura_real_gera(self):
        for modo in (1, 2):
            with self.subTest(lock_mode=modo):
                _executar(_fonte(MAIN_RUIDO), lock_mode=modo)


if __name__ == '__main__':
    unittest.main()
