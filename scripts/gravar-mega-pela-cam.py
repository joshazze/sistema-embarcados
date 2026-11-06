#!/usr/bin/env python3
"""Grava o firmware do Arduino Mega pela ESP32-CAM (rota POST /mega, Digest auth).

Uso (sempre com python3 -I):
  python3 -I scripts/gravar-mega-pela-cam.py --hex caminho/MegaControlador.ino.hex
  python3 -I scripts/gravar-mega-pela-cam.py --compilar [--host controle-cam.local] [--porta 8081]

A senha é a OTA_PASSWORD da CAM e é pedida por getpass; nunca é aceita por argumento
nem impressa. Só usa a biblioteca padrão.

Protocolo com a CAM (firmware/Esp32CamRede/Esp32CamRede.ino):
  1. POST vazio sem Authorization -> 401 com desafio Digest.
  2. Sonda: POST vazio autenticado -> 400 com JSON etapa "sonda" (senha ok, nada gravado);
     401 aqui é senha errada e a imagem não é enviada; 409 é OTA da CAM em andamento.
  3. POST da imagem com X-Image-SHA256 e X-Image-MAC = HMAC-SHA256(senha, sha256 hex minúsculo).
     401 aqui (nonce renovado por outro cliente) leva a uma nova tentativa com o desafio novo.
Falha final da gravação (502): o Mega fica com a flash parcial rodando; regravar recupera.
"""
import argparse
import getpass
import hashlib
import hmac
import http.client
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MAX_IMAGEM = 253952  # 256 KiB de flash menos 8 KiB do bootloader
PORTA_PADRAO = 8081
USUARIO = 'admin'
URI = '/mega'
ARDUINO_CLI_IDE = '/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli'
OPCOES_DE_SENHA = ('--senha', '--password', '--pass', '--pwd', '-p')


class ErroHex(ValueError):
    pass


def hex_para_binario(texto, limite=MAX_IMAGEM):
    """Converte Intel HEX (tipos 00/01/02/04) em binário a partir do endereço 0; lacunas viram 0xFF."""
    memoria = {}
    base = 0
    fim = False
    for numero, linha in enumerate(texto.splitlines(), 1):
        linha = linha.strip()
        if not linha:
            continue
        if fim:
            raise ErroHex(f'linha {numero}: dados depois do registro de fim')
        if not linha.startswith(':'):
            raise ErroHex(f'linha {numero}: falta ":"')
        try:
            dados = bytes.fromhex(linha[1:])
        except ValueError:
            raise ErroHex(f'linha {numero}: hexadecimal inválido') from None
        if len(dados) < 5 or len(dados) != dados[0] + 5:
            raise ErroHex(f'linha {numero}: tamanho inconsistente')
        if sum(dados) & 0xFF:
            raise ErroHex(f'linha {numero}: checksum errado')
        tamanho, endereco, tipo, carga = dados[0], (dados[1] << 8) | dados[2], dados[3], dados[4:-1]
        if tipo == 0x00:
            for i, byte in enumerate(carga):
                posicao = base + endereco + i
                if posicao in memoria and memoria[posicao] != byte:
                    raise ErroHex(f'linha {numero}: endereço 0x{posicao:05x} gravado duas vezes')
                memoria[posicao] = byte
        elif tipo == 0x01:
            fim = True
        elif tipo == 0x02:
            if tamanho != 2:
                raise ErroHex(f'linha {numero}: registro 02 deve ter 2 bytes')
            base = ((carga[0] << 8) | carga[1]) << 4
        elif tipo == 0x04:
            if tamanho != 2:
                raise ErroHex(f'linha {numero}: registro 04 deve ter 2 bytes')
            base = ((carga[0] << 8) | carga[1]) << 16
        else:
            raise ErroHex(f'linha {numero}: tipo de registro {tipo:02x} não suportado')
    if not fim:
        raise ErroHex('falta o registro de fim (tipo 01)')
    if not memoria:
        raise ErroHex('arquivo sem dados')
    tamanho_total = max(memoria) + 1
    if tamanho_total > limite:
        raise ErroHex(f'imagem de {tamanho_total} bytes passa do limite de {limite} bytes')
    imagem = bytearray(b'\xff' * tamanho_total)
    for posicao, byte in memoria.items():
        imagem[posicao] = byte
    return bytes(imagem)


def _md5(texto):
    return hashlib.md5(texto.encode('utf-8')).hexdigest()


def resposta_digest(usuario, senha, realm, nonce, metodo, uri, nc, cnonce, qop='auth'):
    """Resposta Digest MD5 (RFC 2617, qop=auth)."""
    ha1 = _md5(f'{usuario}:{realm}:{senha}')
    ha2 = _md5(f'{metodo}:{uri}')
    return _md5(f'{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}')


def mac_da_imagem(senha, sha_hex):
    """X-Image-MAC: HMAC-SHA256 com a senha como chave sobre o sha256 hex em minúsculas."""
    return hmac.new(senha.encode('utf-8'), sha_hex.lower().encode('ascii'), hashlib.sha256).hexdigest()


def _parametros_digest(cabecalho):
    if not cabecalho or not cabecalho.lower().startswith('digest '):
        raise RuntimeError('a CAM não pediu Digest auth (rota /mega ausente? OTA_PASSWORD definida?)')
    parametros = {}
    for parte in cabecalho[7:].split(','):
        if '=' in parte:
            chave, valor = parte.strip().split('=', 1)
            parametros[chave.strip().lower()] = valor.strip().strip('"')
    for chave in ('realm', 'nonce', 'opaque'):
        if chave not in parametros:
            raise RuntimeError(f'desafio Digest sem "{chave}"')
    return parametros


def cabecalho_digest(usuario, senha, desafio, metodo='POST', uri=URI):
    nc = '00000001'
    cnonce = secrets.token_hex(8)
    resposta = resposta_digest(usuario, senha, desafio['realm'], desafio['nonce'], metodo, uri, nc, cnonce)
    # nc no meio: o WebServer da CAM lê "nc=" até a próxima vírgula.
    return (f'Digest username="{usuario}", realm="{desafio["realm"]}", nonce="{desafio["nonce"]}", '
            f'uri="{uri}", algorithm=MD5, qop=auth, nc={nc}, cnonce="{cnonce}", '
            f'response="{resposta}", opaque="{desafio["opaque"]}"')


def _post(host, porta, timeout, corpo, cabecalhos):
    conexao = http.client.HTTPConnection(host, porta, timeout=timeout)
    try:
        cabecalhos = dict(cabecalhos, **{'Content-Type': 'application/octet-stream',
                                         'Content-Length': str(len(corpo))})
        conexao.request('POST', URI, body=corpo, headers=cabecalhos)
        resposta = conexao.getresponse()
        return resposta.status, resposta.getheader('WWW-Authenticate'), resposta.read()
    finally:
        conexao.close()


class SenhaErrada(RuntimeError):
    pass


def _json(corpo):
    try:
        return json.loads(corpo)
    except ValueError:
        return {}


def enviar(host, porta, imagem, senha, timeout):
    """Pede o desafio, confere a senha com uma sonda vazia e só então envia a imagem."""
    sha = hashlib.sha256(imagem).hexdigest()
    mac = mac_da_imagem(senha, sha)
    status, desafio, _ = _post(host, porta, 15, b'', {})
    if status != 401:
        raise RuntimeError(f'esperava 401 com desafio Digest, veio HTTP {status}')
    parametros = _parametros_digest(desafio)
    status, _, corpo = _post(host, porta, 15, b'', {'Authorization': cabecalho_digest(USUARIO, senha, parametros)})
    if status == 401:
        raise SenhaErrada('senha recusada pela CAM (HTTP 401); a imagem não foi enviada')
    resposta = _json(corpo)
    if status == 409:
        raise RuntimeError(f'CAM ocupada (HTTP 409): {resposta.get("motivo", "")}')
    if status != 400 or resposta.get('etapa') != 'sonda':
        raise RuntimeError(f'sonda da senha: resposta inesperada HTTP {status}')
    for tentativa in range(2):  # outro cliente pode ter renovado o nonce no meio
        cabecalhos = {'Authorization': cabecalho_digest(USUARIO, senha, parametros),
                      'X-Image-SHA256': sha, 'X-Image-MAC': mac}
        status, desafio, corpo = _post(host, porta, timeout, imagem, cabecalhos)
        if status != 401:
            return status, corpo
        parametros = _parametros_digest(desafio)
    raise RuntimeError('senha recusada pela CAM (HTTP 401)')


def _linhas_de_erro(texto, limite=20):
    """Só linhas com "error" (o log bruto do build pode trazer valores do Config.h)."""
    return [linha for linha in texto.splitlines() if 'error' in linha.lower()][:limite]


def compilar(arduino_cli):
    """Compila o MegaControlador num diretório temporário (tem segredos do Config.h) e apaga depois.

    --build-path também fica dentro do temporário, para nada sobrar em $TMPDIR/arduino/sketches.
    """
    temporario = tempfile.mkdtemp(prefix='mega-hex-')
    try:
        comando = [arduino_cli, 'compile', '--fqbn', 'arduino:avr:mega',
                   '--libraries', str(Path.home() / 'Library/Arduino15/libraries'),
                   '--build-path', str(Path(temporario) / 'build'),
                   '--output-dir', str(Path(temporario) / 'saida'), str(RAIZ / 'firmware/MegaControlador')]
        resultado = subprocess.run(comando, capture_output=True, text=True)
        if resultado.returncode != 0:
            linhas = _linhas_de_erro(resultado.stdout + '\n' + resultado.stderr)
            sys.stderr.write(''.join(linha + '\n' for linha in linhas))
            raise RuntimeError('a compilação do MegaControlador falhou')
        arquivo = Path(temporario) / 'saida' / 'MegaControlador.ino.hex'
        return hex_para_binario(arquivo.read_text())
    finally:
        shutil.rmtree(temporario, ignore_errors=True)


def _recusar_senha_em_argumento(argv):
    for argumento in argv:
        nome = argumento.split('=', 1)[0].lower()
        if nome in OPCOES_DE_SENHA or (nome.startswith('-') and ('senha' in nome or 'pass' in nome)):
            sys.stderr.write('erro: a senha não é aceita por argumento; ela é pedida no terminal (getpass).\n')
            raise SystemExit(2)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    _recusar_senha_em_argumento(argv)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    origem = parser.add_mutually_exclusive_group(required=True)
    origem.add_argument('--hex', type=Path, help='arquivo Intel HEX do Mega (sem bootloader)')
    origem.add_argument('--compilar', action='store_true', help='compila firmware/MegaControlador antes')
    parser.add_argument('--host', default='controle-cam.local')
    parser.add_argument('--porta', type=int, default=PORTA_PADRAO)
    parser.add_argument('--timeout', type=float, default=300, help='segundos de espera pela gravação (3 tentativas: ~4 min)')
    parser.add_argument('--arduino-cli', default=shutil.which('arduino-cli') or ARDUINO_CLI_IDE)
    argumentos, sobras = parser.parse_known_args(argv)
    if sobras:
        # Não ecoa valores desconhecidos: podem ser segredos digitados por engano.
        nomes = sorted({s.split('=', 1)[0] for s in sobras if s.startswith('-')}) or ['(valor solto)']
        parser.error('argumentos não reconhecidos: ' + ' '.join(nomes))
    try:
        imagem = compilar(argumentos.arduino_cli) if argumentos.compilar else hex_para_binario(argumentos.hex.read_text())
    except (OSError, ErroHex, RuntimeError) as erro:
        sys.stderr.write(f'erro: {erro}\n')
        return 1
    print(f'imagem: {len(imagem)} bytes, sha256 {hashlib.sha256(imagem).hexdigest()}')
    senha = getpass.getpass(f'Senha OTA da CAM ({USUARIO}@{argumentos.host}): ')
    if not senha:
        sys.stderr.write('erro: senha vazia\n')
        return 1
    print(f'enviando para http://{argumentos.host}:{argumentos.porta}{URI} (pode levar até ~4 min com 3 tentativas)...')
    try:
        status, corpo = enviar(argumentos.host, argumentos.porta, imagem, senha, argumentos.timeout)
    except (OSError, http.client.HTTPException, RuntimeError) as erro:
        sys.stderr.write(f'erro: {erro}\n')
        return 1
    finally:
        senha = None
    try:
        resultado = json.loads(corpo)
    except ValueError:
        sys.stderr.write(f'erro: HTTP {status}, resposta não é JSON: {corpo[:200]!r}\n')
        return 1
    print(f'HTTP {status}: ' + json.dumps(resultado, ensure_ascii=False))
    if resultado.get('ok'):
        print(f'gravado: {resultado.get("bytes")} bytes em {resultado.get("ms")} ms, '
              f'{resultado.get("tentativas")} tentativa(s)')
        return 0
    print(f'falhou na etapa {resultado.get("etapa")}: {resultado.get("motivo")}')
    if status == 502:
        print('o Mega ficou com a flash parcial rodando após o reset; regrave para recuperar')
    return 1


if __name__ == '__main__':
    sys.exit(main())
