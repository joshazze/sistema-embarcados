"""Exercita a religação do DY50 (falha de UART) e o boot do LCD 4 bits no sketch Mega."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_mega_logic import PREFIX

MEGA = Path(__file__).resolve().parents[1] / 'firmware/MegaControlador'
PREFIX = PREFIX.replace('String(const std::string &s):std::string(s) {}',
                        'String(const std::string &s):std::string(s) {} String substring(size_t a,size_t b) const { return String(substr(a,b-a)); }')
PREFIX = PREFIX.replace('uint8_t deleteModel(uint16_t id) { deleted=id; return 0; }',
                        'uint8_t deleteModel(uint16_t id) { deleted=id; return 0; }'
                        ' bool verifyOk=false; int verifyCalls=0; uint16_t capacity=200;'
                        ' bool verifyPassword() { ++verifyCalls; return verifyOk; }'
                        ' uint8_t getParameters() { return FINGERPRINT_OK; }')
MOCKS = r'''
#define F(s) s
#define LCD_SERIAL_MIRROR 1
struct SerialLcdMock { std::string log; void print(const char *s) { log += s; } void print(const std::string &s) { log += s; } void println(const std::string &s) { log += s + "\n"; } } Serial;
struct FakeLCD {
 int begins=0, writes=0, cursors=0, prints=0; std::string last;
 void begin(int,int) { ++begins; }
 void print(const char *s) { ++prints; last = s; }
 void setCursor(int,int) { ++cursors; }
 void write(uint8_t) { ++writes; }
} lcd;
'''
# Trecho com as funções de religação do DY50, lcdBoot e displayTick (todas ficam entre doorTick e a lista de UART).
RECOVERY_SLICE = ('// Religa o DY50', '// Lista circular')


class ReinicioPerifericosTests(unittest.TestCase):
    def _compile_and_run(self, body, cases):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'test.cpp'
            binary = Path(directory) / 'test'
            source.write_text(PREFIX + MOCKS + body + cases)
            cmd = [os.environ.get('CXX', 'c++'), '-std=c++11', '-I', str(MEGA)]
            sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk')
            if sys.platform == 'darwin' and sdk.exists(): cmd += ['-isysroot', str(sdk)]
            result = subprocess.run(cmd + [str(source), '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def _sketch_body(self):
        sketch = (MEGA / 'MegaControlador.ino').read_text()
        logic = sketch[sketch.index('enum class Ui'):sketch.index('void handleKey(')]
        recovery = sketch[sketch.index(RECOVERY_SLICE[0]):sketch.index(RECOVERY_SLICE[1])]
        return logic + recovery

    def test_boot_inicializa_lcd_4bits(self):
        cases = r'''
int main() {
 door.begin(true,now); resetUi(); noticeDuration=0;
 lcdBoot();
 assert(lcd.begins==1 && lcd.prints==1 && lcd.last=="Iniciando...");
 return 0;
}
'''
        self._compile_and_run(self._sketch_body(), cases)

    def test_dy50_volta_quando_verifypassword_responde(self):
        cases = r'''
int main() {
 door.begin(true,now); resetUi(); noticeDuration=0;
 fingerprintReady=false; finger.verifyOk=false;
 // Dentro de 10 s nenhuma tentativa
 fingerprintRecoveryTick(); assert(!fingerprintReady && finger.verifyCalls==0);
 // 10 s depois, sensor ainda mudo: tentativa falha
 now+=10000; fingerprintRecoveryTick(); assert(!fingerprintReady && finger.verifyCalls==1);
 // Sensor responde, mas a janela de 10 s ainda não passou
 now+=2000; finger.verifyOk=true; fingerprintRecoveryTick(); assert(!fingerprintReady && finger.verifyCalls==1);
 // Após 10 s, a mesma expressão do setup confirma o DY50
 now+=8000; fingerprintRecoveryTick(); assert(fingerprintReady && finger.verifyCalls==2);
 // Com o DY50 já ativo, não há novas tentativas
 now+=20000; fingerprintRecoveryTick(); assert(fingerprintReady && finger.verifyCalls==2);
 // Fora da tela de acesso não tenta (cadastro em andamento)
 fingerprintReady=false; ui=Ui::Menu; now+=20000; fingerprintRecoveryTick();
 assert(!fingerprintReady && finger.verifyCalls==2);
 ui=Ui::Access; now+=20000; fingerprintRecoveryTick(); assert(fingerprintReady && finger.verifyCalls==3);
 return 0;
}
'''
        self._compile_and_run(self._sketch_body(), cases)

    def test_recuperacao_dy50_respeita_guardas(self):
        cases = r'''
// Cada caso: com a condição ativa nenhuma tentativa; sem ela, a mesma chamada tenta (controle).
void limpa() {
 door.begin(true,now); resetUi(); noticeDuration=0; buzzer.reset();
 entry=""; fingerprintReady=false; finger.verifyOk=false; now+=30000;
}
void bloqueado(const char *caso) {
 fprintf(stderr,"%s\n",caso);
 const int v=finger.verifyCalls;
 fingerprintRecoveryTick();
 assert(finger.verifyCalls==v);
}
void liberado() {
 const int v=finger.verifyCalls;
 fingerprintRecoveryTick();
 assert(finger.verifyCalls==v+1);
}
int main() {
 limpa(); door.authorize(1,now); assert(door.state==DoorState::AwaitOpen);
 bloqueado("porta em AwaitOpen"); door.begin(true,now); liberado();
 limpa(); door.authorize(1,now); door.tick(false,now,1000,1000); assert(door.state==DoorState::Open);
 bloqueado("porta aberta"); door.begin(true,now); liberado();
 limpa(); notice("Aviso","",false,5000); assert(noticeActive());
 bloqueado("notice ativo"); noticeDuration=0; liberado();
 limpa(); entry="1";
 bloqueado("entry nao vazio"); entry=""; liberado();
 limpa(); ui=Ui::Menu;
 bloqueado("tela fora de Access"); resetUi(); liberado();
 // Buzzer ativo não bloqueia o DY50 (só o aviso de buzzer, sem relação com o LCD)
 limpa(); buzzer.onEvent(DoorEvent::EntryExpired,now); assert(buzzer.isOn(now));
 fprintf(stderr,"buzzer ativo (DY50 nao depende do buzzer)\n");
 { const int v=finger.verifyCalls; fingerprintRecoveryTick(); assert(finger.verifyCalls==v+1); }
 return 0;
}
'''
        self._compile_and_run(self._sketch_body(), cases)


if __name__ == '__main__':
    unittest.main()
