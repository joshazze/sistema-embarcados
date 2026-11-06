"""Conversor Intel HEX, Digest, HMAC, envio, compilação e recusa de senha do scripts/gravar-mega-pela-cam.py."""
import contextlib
import hashlib
import hmac
import http.server
import importlib.util
import io
import json
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/gravar-mega-pela-cam.py'
_spec = importlib.util.spec_from_file_location('gravar_mega_pela_cam', SCRIPT)
gravar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gravar)


def registro(endereco, tipo, dados):
    corpo = bytes([len(dados), endereco >> 8, endereco & 0xFF, tipo]) + bytes(dados)
    return ':' + (corpo + bytes([(-sum(corpo)) & 0xFF])).hex().upper()


FIM = ':00000001FF'


class HexTests(unittest.TestCase):
    def test_dados_simples_e_lacuna_com_ff(self):
        texto = '\n'.join([registro(0, 0, [1, 2, 3]), registro(6, 0, [9]), FIM])
        self.assertEqual(gravar.hex_para_binario(texto), bytes([1, 2, 3, 0xFF, 0xFF, 0xFF, 9]))

    def test_registro_real_do_avr_gcc(self):
        # Linha no formato do avr-objcopy (vetor de reset jmp), checksum conferido à mão.
        texto = ':100000000C9472000C949A000C949A000C949A0030\n' + FIM
        self.assertEqual(gravar.hex_para_binario(texto)[:4], bytes.fromhex('0C947200'))

    def test_endereco_estendido_tipo_02_e_04(self):
        texto = '\n'.join([
            registro(0, 0, [0xAA]),
            registro(0, 2, [0x10, 0x00]),      # segmento 0x1000 -> base 0x10000
            registro(0x0010, 0, [0xBB, 0xCC]),
            registro(0, 4, [0x00, 0x02]),      # linear 0x0002 -> base 0x20000
            registro(0x0001, 0, [0xDD]),
            FIM])
        imagem = gravar.hex_para_binario(texto)
        self.assertEqual(len(imagem), 0x20002)
        self.assertEqual(imagem[0], 0xAA)
        self.assertEqual(imagem[0x10010:0x10012], bytes([0xBB, 0xCC]))
        self.assertEqual(imagem[0x20001], 0xDD)
        self.assertEqual(imagem[1:0x10010], b'\xff' * (0x10010 - 1))

    def test_checksum_errado(self):
        linha = registro(0, 0, [1, 2])
        ruim = linha[:-2] + ('00' if linha[-2:] != '00' else '01')
        with self.assertRaisesRegex(gravar.ErroHex, 'checksum'):
            gravar.hex_para_binario(ruim + '\n' + FIM)

    def test_recusas(self):
        casos = {
            'fim': registro(0, 0, [1]),
            'tipo de registro 03': registro(0, 3, [0, 0, 0, 0]) + '\n' + FIM,
            'tamanho inconsistente': ':0300000001FC\n' + FIM,
            'sem dados': FIM,
            'duas vezes': '\n'.join([registro(0, 0, [1]), registro(0, 0, [2]), FIM]),
            'limite': '\n'.join([registro(0, 4, [0, 3]), registro(0xE000, 0, [1]), FIM]),
            'falta ":"': '0000000' + '\n' + FIM,
        }
        for motivo, texto in casos.items():
            with self.subTest(motivo=motivo), self.assertRaisesRegex(gravar.ErroHex, motivo):
                gravar.hex_para_binario(texto)

    def test_limite_exato_aceito(self):
        ultimo = gravar.MAX_IMAGEM - 1  # 0x3DFFF
        texto = '\n'.join([registro(0, 4, [0, ultimo >> 16]), registro(ultimo & 0xFFFF, 0, [7]), FIM])
        imagem = gravar.hex_para_binario(texto)
        self.assertEqual(len(imagem), gravar.MAX_IMAGEM)
        self.assertEqual(imagem[-1], 7)


class DigestTests(unittest.TestCase):
    def test_exemplo_da_rfc_2617(self):
        resposta = gravar.resposta_digest('Mufasa', 'Circle Of Life', 'testrealm@host.com',
                                          'dcd98b7102dd2f0e8b11d0f600bfb0c093', 'GET', '/dir/index.html',
                                          '00000001', '0a4f113b')
        self.assertEqual(resposta, '6629fae49393a05397450978507c4ef1')

    def test_cabecalho_tem_campos_que_a_cam_exige(self):
        desafio = gravar._parametros_digest('Digest realm="controle-cam", qop="auth", nonce="abc", opaque="def"')
        cabecalho = gravar.cabecalho_digest('admin', 'segredo-teste', desafio)
        for campo in ('username="admin"', 'realm="controle-cam"', 'nonce="abc"', 'uri="/mega"',
                      'qop=auth', 'nc=00000001,', 'opaque="def"', 'response="'):
            self.assertIn(campo, cabecalho)
        self.assertNotIn('segredo-teste', cabecalho)


class MacTests(unittest.TestCase):
    def test_vetor_rfc_4231_caso_2(self):
        # HMAC-SHA256(key="Jefe", "what do ya want for nothing?").
        esperado = '5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843'
        self.assertEqual(gravar.mac_da_imagem('Jefe', 'what do ya want for nothing?'), esperado)

    def test_mensagem_e_sha_hex_minusculo(self):
        sha = hashlib.sha256(b'imagem').hexdigest()
        esperado = hmac.new(b'senha-teste', sha.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(gravar.mac_da_imagem('senha-teste', sha.upper()), esperado)


SENHA_TESTE = 'senha-do-teste'


class CamFalsa(http.server.BaseHTTPRequestHandler):
    """Imita a rota /mega da CAM: Digest do WebServer, sonda vazia e um nonce renovado no meio."""
    estado = None

    def log_message(self, *args):
        pass

    def _responder(self, status, corpo=None, desafio=False):
        self.send_response(status)
        if desafio:
            self.estado['nonce'] = secrets.token_hex(16)
            self.send_header('WWW-Authenticate', f'Digest realm="controle-cam", qop="auth", '
                                                 f'nonce="{self.estado["nonce"]}", opaque="op"')
        dados = json.dumps(corpo or {}).encode()
        self.send_header('Content-Length', str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_POST(self):
        tamanho = int(self.headers.get('Content-Length', 0))
        corpo = self.rfile.read(tamanho)
        e = self.estado
        e['pedidos'].append((tamanho, dict(self.headers)))
        autorizacao = self.headers.get('Authorization')
        if not autorizacao:
            return self._responder(401, desafio=True)
        p = gravar._parametros_digest(autorizacao)
        certo = gravar.resposta_digest(p['username'], e['senha'], p['realm'], p['nonce'], 'POST',
                                       p['uri'], p['nc'], p['cnonce'])
        if p['nonce'] != e['nonce'] or p['response'] != certo:
            return self._responder(401, desafio=True)
        if tamanho == 0:
            return self._responder(400, {'ok': False, 'etapa': 'sonda', 'motivo': 'senha ok; corpo vazio'})
        if e['renovar_nonce']:
            e['renovar_nonce'] = False  # outro cliente pediu desafio no meio
            return self._responder(401, desafio=True)
        sha = hashlib.sha256(corpo).hexdigest()
        if self.headers.get('X-Image-SHA256') != sha:
            return self._responder(400, {'ok': False, 'motivo': 'sha256 diferente'})
        mac = hmac.new(e['senha'].encode(), sha.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(self.headers.get('X-Image-MAC', ''), mac):
            return self._responder(403, {'ok': False, 'motivo': 'X-Image-MAC errado'})
        e['gravado'] = corpo
        self._responder(200, {'ok': True, 'tentativas': 1, 'bytes': len(corpo)})


class EnviarTests(unittest.TestCase):
    def _servidor(self, senha=SENHA_TESTE, renovar_nonce=True):
        estado = {'senha': senha, 'nonce': None, 'renovar_nonce': renovar_nonce, 'pedidos': [], 'gravado': None}
        manipulador = type('Cam', (CamFalsa,), {'estado': estado})
        servidor = http.server.ThreadingHTTPServer(('127.0.0.1', 0), manipulador)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        self.addCleanup(servidor.server_close)
        self.addCleanup(servidor.shutdown)
        return servidor.server_address[1], estado

    def test_sonda_nonce_renovado_e_gravacao(self):
        porta, estado = self._servidor()
        imagem = bytes(range(256)) * 3
        status, corpo = gravar.enviar('127.0.0.1', porta, imagem, SENHA_TESTE, 10)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(corpo)['ok'])
        self.assertEqual(estado['gravado'], imagem)
        # desafio, sonda, imagem com nonce velho (401), imagem com nonce novo.
        self.assertEqual([t for t, _ in estado['pedidos']], [0, 0, len(imagem), len(imagem)])
        sha = hashlib.sha256(imagem).hexdigest()
        cabecalhos = estado['pedidos'][-1][1]
        self.assertEqual(cabecalhos['X-Image-SHA256'], sha)
        self.assertEqual(cabecalhos['X-Image-MAC'], hmac.new(SENHA_TESTE.encode(), sha.encode(), hashlib.sha256).hexdigest())
        self.assertNotIn(SENHA_TESTE, json.dumps(estado['pedidos']))

    def test_senha_errada_para_na_sonda_sem_enviar_imagem(self):
        porta, estado = self._servidor()
        with self.assertRaisesRegex(gravar.SenhaErrada, '401'):
            gravar.enviar('127.0.0.1', porta, b'\x01' * 512, 'senha-errada', 10)
        self.assertEqual([t for t, _ in estado['pedidos']], [0, 0])
        self.assertIsNone(estado['gravado'])


class CompilarTests(unittest.TestCase):
    def _compilar(self, codigo, saida=''):
        chamadas = []

        def run_falso(comando, **kwargs):
            chamadas.append(comando)
            if codigo == 0:
                destino = Path(comando[comando.index('--output-dir') + 1])
                destino.mkdir(parents=True, exist_ok=True)
                (destino / 'MegaControlador.ino.hex').write_text(':0100000007F8\n:00000001FF\n')
            return subprocess.CompletedProcess(comando, codigo, stdout=saida, stderr='')

        erro = io.StringIO()
        with mock.patch.object(gravar.subprocess, 'run', run_falso), contextlib.redirect_stderr(erro):
            try:
                resultado = gravar.compilar('arduino-cli-falso')
            except RuntimeError as excecao:
                resultado = excecao
        comando = chamadas[0]
        build = Path(comando[comando.index('--build-path') + 1])
        saida_dir = Path(comando[comando.index('--output-dir') + 1])
        return resultado, build, saida_dir, erro.getvalue()

    def test_sucesso_apaga_temporario_e_build_dentro_dele(self):
        resultado, build, saida_dir, _ = self._compilar(0)
        self.assertEqual(resultado, bytes([7]))
        self.assertEqual(build.parent, saida_dir.parent)
        self.assertTrue(build.parent.name.startswith('mega-hex-'))
        self.assertFalse(build.parent.exists())

    def test_falha_apaga_temporario_e_so_mostra_linhas_de_erro(self):
        log = 'const char WIFI_PASSWORD[] = "segredo-do-config";\n' + '\n'.join(
            f'x.ino:{i}: error: algo {i}' for i in range(30))
        resultado, build, saida_dir, erro = self._compilar(1, log)
        self.assertIsInstance(resultado, RuntimeError)
        self.assertFalse(build.parent.exists())
        self.assertEqual(build.parent, saida_dir.parent)
        self.assertNotIn('segredo-do-config', erro)
        self.assertEqual(len(erro.splitlines()), 20)
        self.assertTrue(all('error' in linha for linha in erro.splitlines()))


class SenhaPorArgumentoTests(unittest.TestCase):
    def _rodar(self, *argumentos):
        return subprocess.run([sys.executable, '-I', str(SCRIPT), *argumentos],
                              capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30)

    def test_recusa_senha_por_argumento_sem_ecoar(self):
        for argumentos in (['--hex', 'x.hex', '--senha', 'segredo123'], ['--hex', 'x.hex', '--password=segredo123'],
                           ['--compilar', '-p', 'segredo123'], ['--hex', 'x.hex', '--ota-pass', 'segredo123']):
            with self.subTest(argumentos=argumentos):
                resultado = self._rodar(*argumentos)
                self.assertEqual(resultado.returncode, 2)
                self.assertIn('getpass', resultado.stderr)
                self.assertNotIn('segredo123', resultado.stdout + resultado.stderr)

    def test_argumento_desconhecido_nao_ecoa_valor(self):
        resultado = self._rodar('--hex', 'x.hex', '--chave', 'segredo123')
        self.assertEqual(resultado.returncode, 2)
        self.assertIn('--chave', resultado.stderr)
        self.assertNotIn('segredo123', resultado.stdout + resultado.stderr)

    def test_sem_parametro_de_senha_no_parser(self):
        texto = SCRIPT.read_text(encoding='utf-8')
        self.assertIn('getpass.getpass(', texto)
        self.assertNotIn("add_argument('--senha'", texto)


if __name__ == '__main__':
    unittest.main()
