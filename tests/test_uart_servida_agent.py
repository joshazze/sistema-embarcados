"""UART servida durante a escrita de senha/registro e expiração da senha parcial no sketch Mega.

A varredura de senhas (ownerOfPin) foi removida: a senha é comparada só com o registro do ID.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from test_mega_logic import PREFIX as LOGIC_PREFIX

MEGA = Path(__file__).resolve().parents[1] / 'firmware/MegaControlador'
PREFIX = LOGIC_PREFIX.replace('void linkTick(bool) {}\n', '')  # o linkTick real vem do trecho do enlace
for _old, _new in [
    ('#include <string>', '#include <string>\n#include <vector>'),
    ('#include "BuzzerLogic.h"', '#include "BuzzerLogic.h"\n#include "CardStore.h"\n#include "MessageProtocol.h"\n#include "SerialFrame.h"'),
    ('void queueEvent(const char *,uint16_t,const char *,const char *) {}', 'void queueEvent(const char *,uint16_t,const char *,const char *);'),
    ('void doorTick() {', 'void doorTick();\nvoid doorTickBase() {'),
    ('String(const std::string &s):std::string(s) {}', 'String(const std::string &s):std::string(s) {} String substring(size_t a,size_t b) const { return String(substr(a,b-a)); }'),
]:
    assert PREFIX.count(_old) == 1, _old
    PREFIX = PREFIX.replace(_old, _new)
PREFIX += r'''
struct SerialPort {
 std::vector<uint8_t> input,output; size_t pos=0;
 int available() { return int(input.size()-pos); }
 int availableForWrite() { return 1; }
 uint8_t read() { return input[pos++]; }
 void write(uint8_t b) { output.push_back(b); }
} Serial2;
uint32_t eventSequence=0, droppedEvents=0;
// Gancho chamado a cada doorTick: simula chegada de UART durante a busca ou reentrada.
void (*hook)() = nullptr;
void doorTick() { if (hook) hook(); doorTickBase(); }
'''
SHARED = r'''
struct Sink { std::vector<uint8_t> data; void write(uint8_t b) { data.push_back(b); } };
void frameTo(std::vector<uint8_t> &out, const uint8_t *b, size_t n) { Sink s; assert(SerialFrame::send(s,b,n)); out.insert(out.end(),s.data.begin(),s.data.end()); }
void pushInput(const std::vector<uint8_t> &f) { Serial2.input.insert(Serial2.input.end(),f.begin(),f.end()); }
std::vector<uint8_t> ackFrame(uint32_t id, uint32_t boot) { using namespace MessageProtocol; uint8_t b[10]={kVersion,Ack}; put32(b+2,id); put32(b+6,boot); std::vector<uint8_t> f; frameTo(f,b,sizeof b); return f; }
std::vector<uint8_t> clockFrame(uint32_t epoch) { using namespace MessageProtocol; uint8_t b[10]={kVersion,Clock}; put32(b+6,epoch); std::vector<uint8_t> f; frameTo(f,b,sizeof b); return f; }
std::vector<uint8_t> resetFrame(uint32_t cmd, const char *pin, uint64_t token) { using namespace MessageProtocol; uint8_t b[21]={kVersion,Reset}; put32(b+2,cmd); b[6]=1; memcpy(b+7,pin,6); for(int i=0;i<8;++i) b[13+i]=uint8_t(token>>(8*i)); std::vector<uint8_t> f; frameTo(f,b,sizeof b); return f; }
unsigned scanTicks=0, emptyAt=0, nestedCalls=0;
long nestedDelta=-1; uint32_t nestedEpoch=0;
void createUser1() {
 door.begin(true,now); resetUi();
 pendingId=1; firstPin="123456"; entry="123456"; confirmEnrollment();
 assert(exists(1) && matches(1,"123456")); entry="";
}
'''
# LCD simulado para displayTick: conta caracteres escritos.
DISPLAY_MOCKS = r'''
#define F(s) s
#define LCD_SERIAL_MIRROR 1
struct SerialLcdMock { std::string log; void print(const char *s) { log += s; } void print(const std::string &s) { log += s; } void println(const std::string &s) { log += s + "\n"; } } Serial;
struct FakeLCD { int writes=0; void begin(int,int) {} void print(const char *) {} void setCursor(int,int) {} void write(uint8_t) { ++writes; } } lcd;
'''
MAIN_REENTRY = r'''
int main() {
 door.begin(true,now); resetUi();
 pushInput(clockFrame(1700000000UL));
 // Dentro do enlace (linkTick externo), uma chamada aninhada só copia a UART para linkStash, sem parsear.
 hook=[]() {
   static bool done = false;
   if (done) return;
   done = true;
   const size_t before = Serial2.pos;
   linkTick(true);
   nestedDelta = long(Serial2.pos) - long(before);
   nestedEpoch = syncEpoch;
   ++nestedCalls;
 };
 linkTick(false);
 hook=nullptr;
 assert(nestedCalls==1 && nestedDelta==long(Serial2.input.size()) && nestedEpoch==0);
 // A chamada externa processa o quadro guardado, na mesma ordem, e esvazia o stash.
 assert(syncEpoch==1700000000UL && linkStashLen==0);
 return 0;
}
'''
# Um ACK chega durante saveRecord (ServicedEeprom::update): deve ser processado antes do fim da gravação.
MAIN_SAVE_ACK = r'''
int main() {
 door.begin(true,now); resetUi();
 queueEvent("access_granted",1,"password",""); linkTick(false);
 assert(count==1 && !linkTx.pending());
 UserRecord record = {}; record.active=1;
 for (int i=0;i<4;++i) record.salt[i]=uint8_t(i+1);
 digest("123456",record.salt,record.hash);
 scanTicks=0;
 hook=[]() { if (++scanTicks==3) pushInput(ackFrame(outbound[head].messageId,bootNumber)); };
 assert(saveRecord(1,record));
 hook=nullptr;
 assert(scanTicks>=3 && count==0 && Serial2.pos==Serial2.input.size());
 assert(matches(1,"123456"));
 return 0;
}
'''
# Um ACK chega durante o desenho do LCD (displayTick): deve ser processado durante o desenho.
MAIN_DISPLAY_ACK = r'''
int main() {
 door.begin(true,now); resetUi(); noticeDuration=0;
 queueEvent("access_granted",1,"password",""); linkTick(false);
 assert(count==1 && !linkTx.pending());
 lcd.writes=0; scanTicks=0; now+=1000;
 hook=[]() { if (++scanTicks==5) pushInput(ackFrame(outbound[head].messageId,bootNumber)); };
 displayTick();
 hook=nullptr;
 assert(lcd.writes==32 && scanTicks>=5);
 assert(count==0 && Serial2.pos==Serial2.input.size());
 return 0;
}
'''
# Bytes chegam durante um reset executado dentro do enlace: vão para linkStash e são processados
# na chamada seguinte, na ordem (ACK do evento 1 antes do ACK do evento 2).
MAIN_STASH = r'''
bool pushed=false; uint32_t firstId=0, secondId=0;
int main() {
 createUser1();
 count=0; head=0;
 queueEvent("access_granted",1,"password",""); queueEvent("access_granted",1,"password","");
 firstId=outbound[0].messageId; secondId=outbound[1].messageId;
 pushInput(resetFrame(7,"654321",42));
 // O reset roda com replyCount==1 e linkBusy ativo: empurrar os ACKs no meio da busca.
 scanTicks=0;
 hook=[]() {
   if (!pushed && linkBusy && replyCount==1 && ++scanTicks==3) {
     pushInput(ackFrame(firstId,bootNumber)); pushInput(ackFrame(secondId,bootNumber)); pushed=true;
   }
 };
 linkTick(false);
 hook=nullptr;
 assert(pushed && matches(1,"654321") && !matches(1,"123456"));
 // Fila antes do reset: 2 eventos de teste + password_reset gerado pelo próprio reset.
 assert(Serial2.pos==Serial2.input.size() && linkStashLen>0 && count==3);
 linkTick(false);
 // Os dois ACKs saíram do stash em ordem; só o password_reset continua pendente.
 assert(count==1 && linkStashLen==0 && outbound[head].kind==MessageProtocol::PasswordReset);
 return 0;
}
'''
# Reset chega no meio da gravação de um cadastro (ServicedEeprom::update): fica adiado (deferredReset),
# não troca a senha antes do fim da gravação e é executado na chamada seguinte, com ResetResult ok.
MAIN_RESET_SAVE = r'''
int main() {
 createUser1();
 UserRecord record = {}; record.active=1;
 for (int i=0;i<4;++i) record.salt[i]=uint8_t(i+7);
 digest("222222",record.salt,record.hash);
 Serial2.output.clear();
 scanTicks=0;
 hook=[]() { if (++scanTicks==5) pushInput(resetFrame(42,"654321",42)); };
 assert(saveRecord(2,record));
 hook=nullptr;
 assert(scanTicks>=5 && Serial2.pos==Serial2.input.size());
 assert(exists(2) && matches(1,"123456") && !matches(1,"654321"));
 assert(replyCount==1 && linkReplies[replyHead].deferredReset);
 for (int i=0;i<20;++i) linkTick(false);
 assert(replyCount==0 && matches(1,"654321") && !matches(1,"123456"));
 // ACK: ResetResult com o cmd 42, resultado ok (1) e motivo 0 (ok).
 SerialFrame::Parser leitor; int achados=0;
 for (uint8_t b : Serial2.output) {
   if (!leitor.feed(b, 0)) continue;
   const uint8_t *p = leitor.data();
   if (leitor.size() == 8 && p[1] == MessageProtocol::ResetResult) {
     ++achados;
     assert(MessageProtocol::get32(p+2) == 42 && p[6] == 1 && p[7] == 0);
   }
 }
 assert(achados == 1);
 return 0;
}
'''
MAIN_EXPIRY = r'''
int main() {
 resetUi(); noticeDuration=0; entry=""; noticeLine1="";
 now=10000; handleKey('1'); assert(entry=="1" && entryTouched==10000);
 now=39999; expireEntry(); assert(entry=="1");
 now=40000; expireEntry(); assert(entry=="");
 assert(noticeLine1=="" && noticeDuration==0 && count==0);
 now=50000; handleKey('3');
 now=60000; handleKey('4'); assert(entry=="34");
 now=89999; expireEntry(); assert(entry=="34");
 now=90000; expireEntry(); assert(entry=="");
 ui=Ui::Menu; entry="5"; now=200000; expireEntry(); assert(entry=="5");
 return 0;
}
'''


class UartServidaTests(unittest.TestCase):
    def _run(self, main_code, extra=''):
        sketch = (MEGA / 'MegaControlador.ino').read_text()
        logic = sketch[sketch.index('enum class Ui'):sketch.index('void handleKey(')]
        handle = sketch[sketch.index('void handleKey('):sketch.index('void fingerprintTick()')]
        link = sketch[sketch.index('MessageProtocol::EventData outbound'):sketch.index('void serialTick()')]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'test.cpp'
            binary = Path(directory) / 'test'
            source.write_text(PREFIX + logic + handle + link + SHARED + extra + main_code)
            cmd = [os.environ.get('CXX', 'c++'), '-std=c++11', '-I', str(MEGA)]
            sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
            if sys.platform == 'darwin' and sdk.exists(): cmd += ['-isysroot', str(sdk)]
            result = subprocess.run(cmd + [str(source), '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_link_tick_is_not_reentered(self):
        self._run(MAIN_REENTRY)

    def test_ack_processed_during_save_record(self):
        self._run(MAIN_SAVE_ACK)

    def test_ack_processed_during_display_draw(self):
        sketch = (MEGA / 'MegaControlador.ino').read_text()
        display = sketch[sketch.index('void displayTick()'):sketch.index('// Lista circular')]
        self._run(MAIN_DISPLAY_ACK, DISPLAY_MOCKS + display)

    def test_bytes_during_link_reset_are_stashed_in_order(self):
        self._run(MAIN_STASH)

    def test_reset_during_cadastro_write_is_deferred(self):
        self._run(MAIN_RESET_SAVE)

    def test_partial_pin_expires_after_30s_without_key(self):
        self._run(MAIN_EXPIRY)


if __name__ == '__main__':
    unittest.main()
