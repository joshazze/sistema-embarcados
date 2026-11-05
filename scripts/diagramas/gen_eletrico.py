#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o ESQUEMA ELETRICO (SVG) do controle de acesso.

Nao e desenho de protoboard: sao ligacoes logicas, com redes nomeadas.
Fonte da verdade: registros da montagem de uso verificada em 04/11/2026.

Uso (a saida vai para a pasta corrente):
    cd docs/diagramas && python3 ../../scripts/diagramas/gen_eletrico.py

Somente biblioteca padrao do Python 3.
"""
from pathlib import Path

W, H = 1800, 1250
SAIDA = "05-esquema-eletrico.svg"

RED = "#d81e1e"       # 5 V
ORA = "#f28c00"       # 3,3 V (linha)
ORA_TXT = "#b35900"   # 3,3 V (texto, mais legivel sobre branco)
BLK = "#000000"       # GND
BLU = "#1e5bd8"       # sinais
GRY = "#9a9a9a"       # nao ligado / ausente
CONF = "#d35400"      # CONFERIR
TXT = "#111111"
RES_FILL = "#f4e3b5"
RES_EDGE = "#7a5c1e"

out = []


def a(s):
    out.append(s)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, t, size=12, color=TXT, anchor="start", bold=False):
    b = ' font-weight="bold"' if bold else ""
    a(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
      f'text-anchor="{anchor}"{b}>{esc(t)}</text>')


def poly(pts, color=BLU, w=2.2, dash=None):
    d = " ".join(f"{x},{y}" for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
      f'stroke-linejoin="round" stroke-linecap="round"{da}/>')


def dot(x, y, color=TXT):
    a(f'<circle cx="{x}" cy="{y}" r="3.6" fill="{color}"/>')


def box(x, y, w, h, fill="#fff", stroke="#333", sw=1.5, rx=0, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
      f'stroke="{stroke}" stroke-width="{sw}"{da}/>')


def net(x, y, t, color=BLK, mode="C"):
    """Rotulo de rede. mode: L = caixa comeca em x; R = caixa termina em x;
    C = caixa centrada em x. y e o centro vertical."""
    w = len(t) * 6.6 + 14
    if mode == "L":
        x0 = x
    elif mode == "R":
        x0 = x - w
    else:
        x0 = x - w / 2
    box(round(x0, 1), y - 9, round(w, 1), 18, fill="#fff", stroke=color, sw=1.3, rx=4)
    tc = ORA_TXT if color == ORA else color
    txt(round(x0 + w / 2, 1), y + 4, t, 11, tc, "middle", bold=True)


def res_h(x1, x2, y, label=None, above=True):
    """Resistor horizontal: so o corpo; o fio deve ser desenhado antes com poly()."""
    box(x1 + 8, y - 6, (x2 - x1) - 16, 12, fill=RES_FILL, stroke=RES_EDGE, sw=1.2, rx=2)
    if label:
        ty = y - 10 if above else y + 18
        txt((x1 + x2) / 2, ty, label, 10, TXT, "middle")


def res_v(x, y1, y2, label=None, color=TXT, side="right"):
    """Resistor vertical centrado entre y1 e y2; o fio deve ser desenhado antes."""
    yc = (y1 + y2) / 2
    box(x - 6, yc - 12, 12, 24, fill=RES_FILL, stroke=RES_EDGE, sw=1.2, rx=2)
    if label:
        if side == "right":
            txt(x + 10, yc + 4, label, 10, color, "start", bold=(color == CONF))
        else:
            txt(x - 10, yc + 4, label, 10, color, "end", bold=(color == CONF))


def pin_mega_left(y, name, color=TXT):
    txt(788, y + 4, name, 11, color, "start")


def pin_mega_right(y, name, color=TXT):
    txt(1012, y + 4, name, 11, color, "end")


# ---------------------------------------------------------------- cabecalho
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
  f'viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">')
box(0, 0, W, H, fill="#ffffff", stroke="none", sw=0)
txt(20, 34, "Esquema elétrico - controle de acesso (montagem de uso, "
            "verificada em 04/11/2026)", 22, TXT, "start", True)
txt(20, 58, "Não é protoboard: ligações lógicas com rótulos de rede. "
            "Itens em laranja CONFERIR não estão confirmados nos registros.",
    13, "#444")

# ---------------------------------------------------------------- fonte YwRobot
box(1200, 80, 580, 100, fill="#fffbe6", stroke="#8a6d00", sw=1.5, rx=6)
txt(1212, 98, "Fonte de protoboard YwRobot MB102 (P4 <- fonte de parede 7 V)", 12, TXT, "start", True)
txt(1212, 116, "Jumper de CIMA em 5V: trilha de cima = +5V YwRobot (cima) (CAM e buzzer).", 11)
txt(1212, 132, "Nenhum fio do 5V do Mega nesta trilha.", 11, RED, "start", True)
txt(1212, 148, "Jumper de BAIXO em 3.3: trilha de baixo = +3,3V YwRobot (baixo) (só DY50).", 11)
txt(1212, 164, "GND comum: Mega, YwRobot (os dois lados), CAM, DY50, LCD, buzzer, botões.", 11)

# ---------------------------------------------------------------- Mega 2560
MX0, MY0, MW, MH = 780, 190, 240, 810
box(MX0, MY0, MW, MH, fill="#eef3fb", stroke="#1e3a8a", sw=2.5, rx=8)
txt(900, 212, "ARDUINO MEGA 2560 (Mega 1)", 13, TXT, "middle", True)
txt(900, 229, "alimentado pelo USB do Mac", 10, "#444", "middle")

# pinos da esquerda (texto dentro da caixa)
pin_mega_left(250, "D18 TX1")
pin_mega_left(276, "D19 RX1")
pin_mega_left(302, "D16 TX2")
pin_mega_left(328, "D17 RX2")
pin_mega_left(540, "D30 botão 1")
pin_mega_left(566, "D31 botão 2")
pin_mega_left(592, "D36 buzzer")
pin_mega_left(618, "D35 TRANCA", GRY)
pin_mega_left(644, "D32 RGB", GRY)
pin_mega_left(670, "D33 RGB", GRY)
pin_mega_left(696, "D34 RGB", GRY)

# pinos da direita: teclado e LCD
for y, nm in [(250, "D22 R1"), (274, "D23 R2"), (298, "D24 R3"), (322, "D25 R4"),
              (346, "D26 C1"), (370, "D27 C2"), (394, "D28 C3"), (418, "D29 C4"),
              (462, "D37 RS"), (486, "D38 E"), (510, "D39 D4"), (534, "D40 D5"),
              (558, "D41 D6"), (582, "D42 D7")]:
    pin_mega_right(y, nm)

notas = ["D0/D1: USB (não usar)", "D20/D21: livres",
         "Serigrafia do clone troca 18/19:", "medido: pino 18 = TX1"]
for i, t in enumerate(notas):
    txt(788, 760 + i * 17, t, 10, "#444")

# pinos de alimentacao (rotulos de rede)
poly([(840, 1000), (840, 1017)], RED)
net(840, 1026, "+5V Mega -> trilha solta", RED, "C")
poly([(1000, 1000), (1000, 1017)], BLK)
net(1000, 1026, "GND", BLK, "C")

# ---------------------------------------------------------------- LEITOR DY50
box(100, 190, 200, 100, fill="#f3fbf3", stroke="#2e7d32", sw=2, rx=6)
txt(110, 207, "Leitor DY50 (Serial1, 57600)", 12, TXT, "start", True)
txt(290, 254, "RX", 11, BLU, "end", True)
txt(290, 280, "TX", 11, BLU, "end", True)

# D18 (TX1) -> resistor 1 k -> RX do DY50 (no 330 do divisor: no 250)
poly([(780, 250), (300, 250)], BLU)
res_h(600, 650, 250, "1 kΩ (TX1 -> RX)", above=True)
dot(330, 250)
# divisor do RX: 1 k + 1 k ate GND (CONFERIR)
poly([(330, 250), (330, 149)], BLU)
res_v(330, 236, 196, "1 kΩ", TXT, "right")
res_v(330, 196, 156, "1 kΩ", TXT, "right")
net(330, 140, "GND", BLK, "C")
txt(360, 200, "CONFERIR 1: medir até GND (esperado ~2 kΩ)", 11, CONF, "start", True)

# DY50 TX -> D19 (RX1), direto
poly([(300, 276), (780, 276)], BLU)

# alimentacao do DY50
poly([(150, 190), (150, 173)], ORA)
net(150, 164, "+3,3V YwRobot (baixo)", ORA, "C")
poly([(260, 190), (260, 173)], BLK)
net(260, 164, "GND", BLK, "C")

# ---------------------------------------------------------------- ESP32-CAM + divisor
# linha do D16 (TX2) ate o divisor: 3 x 330 ohms e 6 x 330 ohms em serie ate GND
poly([(780, 302), (252, 302), (252, 316)], BLU)
res_h(600, 680, 302, "1 kΩ", above=False)
for x1, x2 in [(440, 520), (300, 380)]:
    res_h(x1, x2, 302, "1 kΩ", above=False)
net(252, 324, "GND", BLK, "C")
txt(640, 290, "1 kΩ (D16 -> meio)", 10, "#222", "middle")
txt(410, 290, "2 x 1 kΩ em série até GND", 10, "#222", "middle")
dot(548, 302)
txt(556, 362, "nó meio: medir ~3,3 V (CONFERIR 2)", 10, ORA_TXT, "start", True)

# IO13 da CAM <- no do meio
poly([(548, 302), (548, 400), (320, 400)], BLU)
txt(420, 392, "IO13 (3,3 V)", 10, BLU, "middle")

# IO14 da CAM -> D17 (RX2), direto (3,3 V)
poly([(320, 430), (740, 430), (740, 328), (780, 328)], BLU)
txt(520, 448, "IO14 -> D17 (RX2)", 10, BLU, "middle")

box(120, 380, 200, 100, fill="#fff7e6", stroke="#8a5a00", sw=2, rx=6)
txt(132, 396, "ESP32-CAM (AI-Thinker)", 12, TXT, "start", True)
txt(312, 404, "IO13", 11, BLU, "end", True)
txt(312, 434, "IO14", 11, BLU, "end", True)
txt(132, 450, "IO0: solto (GND só para gravar)", 10, "#444")
txt(132, 466, "U0R/U0T: sem fio na montagem de uso", 10, "#444")
# alimentacao da CAM: rotulos de rede
poly([(150, 480), (150, 493)], RED)
net(150, 502, "+5V YwRobot (cima)", RED, "C")
poly([(290, 480), (290, 493)], BLK)
net(290, 502, "GND (azul de cima)", BLK, "C")

# ---------------------------------------------------------------- BOTOES DA PORTA
txt(486, 520, "Botões da porta: pull-up interno do Mega, sem resistor", 10, "#444", "end")
for y, nome in [(540, "botão 1"), (566, "botão 2")]:
    poly([(780, y), (616, y)], BLU)
    dot(616, y)
    dot(556, y)
    poly([(556, y), (600, y - 14)], TXT, 2)
    poly([(556, y), (512, y)], BLK)
    net(512, y, "GND", BLK, "R")

# ---------------------------------------------------------------- FECHADURA (NAO LIGAR)
poly([(780, 618), (730, 618)], GRY, 2, "4,3")
poly([(724, 612), (736, 624)], GRY, 2)
poly([(736, 612), (724, 624)], GRY, 2)

# ---------------------------------------------------------------- BUZZER + BC546
# D36 -> 330 ohms -> base do BC546
poly([(780, 592), (600, 592), (600, 700), (570, 700)], BLU)
res_h(530, 570, 700, "330 Ω", above=True)
poly([(530, 700), (470, 700)], BLU)
dot(510, 700)
# base -> 10 k -> GND (CONFERIR)
poly([(510, 700), (510, 752)], BLU)
res_v(510, 752, 800, "1 kΩ (era 10 kΩ)", TXT, "right")
poly([(510, 800), (510, 817)], BLK)
net(510, 826, "GND", BLK, "C")
# transistor NPN (C-B-E): seta no emissor apontando PARA FORA
poly([(470, 684), (470, 716)], "#222", 3)
poly([(470, 690), (500, 664), (500, 630)], BLU)
poly([(470, 710), (440, 732), (440, 817)], BLK)
a('<polygon points="453.5,722.1 463.4,720.4 458.1,713.2" fill="#000000"/>')
txt(508, 650, "C", 12, TXT, "start", True)
txt(460, 697, "B", 12, TXT, "end", True)
txt(430, 760, "E", 12, TXT, "end", True)
net(440, 826, "GND", BLK, "C")
txt(440, 862, "BC546 (NPN): pinos C-B-E", 10, "#444", "middle")
dot(500, 630)
# buzzer ativo: + na +5V YwRobot (cima), verificado em 04/11; - no coletor
poly([(364, 630), (344, 630), (344, 596)], RED)
poly([(396, 630), (500, 630)], BLU)
net(344, 586, "+5V YwRobot (cima)", RED, "C")
txt(420, 584, "verificado em 04/11 (documento antigo dizia 5V do Mega)", 9, "#666")
a('<circle cx="380" cy="630" r="16" fill="#ffffff" stroke="#333" stroke-width="1.5"/>')
txt(380, 633, "BZ", 9, TXT, "middle", True)
txt(352, 624, "+", 11, RED, "middle", True)
txt(408, 624, "-", 11, BLK, "middle", True)

# ---------------------------------------------------------------- TECLADO 4x4
box(1200, 232, 220, 200, fill="#f7f7f7", stroke="#444", sw=1.5, rx=6)
txt(1204, 224, "Teclado 4x4 (sem resistores)", 11, TXT, "start", True)
for y, nome, mega in [(250, "5 R1 (linha)", "D22"), (274, "6 R2 (linha)", "D23"),
                      (298, "7 R3 (linha)", "D24"), (322, "8 R4 (linha)", "D25"),
                      (346, "1 C1 (coluna)", "D26"), (370, "2 C2 (coluna)", "D27"),
                      (394, "3 C3 (coluna)", "D28"), (418, "4 C4 (coluna)", "D29")]:
    poly([(1020, y), (1200, y)], BLU)
    txt(1210, y + 4, nome, 11, TXT, "start")

# ---------------------------------------------------------------- LCD 1602 (4 bits)
box(1200, 452, 240, 226, fill="#eef8ff", stroke="#245", sw=1.5, rx=6)
txt(1200, 444, "LCD 1602 em 4 bits (sem I2C)", 11, TXT, "start", True)
for y, nome, mega in [(462, "4 RS", "D37"), (486, "6 E", "D38"),
                      (510, "11 D4", "D39"), (534, "12 D5", "D40"),
                      (558, "13 D6", "D41"), (582, "14 D7", "D42")]:
    poly([(1020, y), (1200, y)], BLU)
    txt(1210, y + 4, nome, 11, TXT, "start")
poly([(1200, 606), (1168, 606)], GRY, 3.5, "6,4")
txt(1210, 610, "5 RW: SEM FIO (deixar solto)", 11, RED, "start", True)
txt(1210, 632, "7 a 10 (D0 a D3): sem fio", 11, "#444")
txt(1210, 654, "Contraste (V0) e luz de fundo (A/K): ao lado", 10, "#444")
# pinos de alimentacao do LCD (lado direito)
for y, nome in [(470, "1 VSS"), (494, "2 VDD"), (540, "3 V0"), (566, "15 A"), (596, "16 K")]:
    txt(1430, y + 4, nome, 11, TXT, "end")
poly([(1440, 470), (1462, 470)], BLK)
net(1462, 470, "GND", BLK, "L")
poly([(1440, 494), (1462, 494)], RED)
net(1462, 494, "+5V Mega", RED, "L")
# potenciometro 10 k: resistor vertical com cursor (seta) no meio; o fio do V0 sai do cursor
poly([(1440, 540), (1614, 540)], BLU)
a('<polygon points="1624,540 1614,534.5 1614,545.5" fill="#1e5bd8"/>')
poly([(1440, 566), (1520, 566)], RED)
res_h(1462, 1500, 566, "220 Ω", above=True)
net(1520, 566, "+5V Mega", RED, "L")
poly([(1440, 596), (1462, 596)], BLK)
net(1462, 596, "GND", BLK, "L")
box(1624, 500, 16, 80, fill=RES_FILL, stroke=RES_EDGE, sw=1.2, rx=2)
txt(1648, 545, "10 kΩ", 10, TXT, "start")
poly([(1632, 500), (1632, 478)], RED)
net(1632, 469, "+5V Mega", RED, "C")
poly([(1632, 580), (1632, 612)], BLK)
net(1632, 621, "GND", BLK, "C")
txt(1452, 646, "No LCD: todo \"+5V Mega\" = trilha solta (+), do 5V do Mega;", 10, RED, "start", bold=True)
txt(1452, 660, "todo \"GND\" = trilha solta (-), de um GND do Mega.", 10, TXT, "start")
txt(1452, 674, "Potenciômetro ligado por cabos.", 10, TXT, "start")

# ---------------------------------------------------------------- LEGENDA
box(1455, 198, 325, 140, fill="#ffffff", stroke="#888", sw=1.2, rx=6)
txt(1467, 216, "Legenda", 12, TXT, "start", True)
leg = [(RED, None, "5 V (vermelho)"), (ORA, None, "3,3 V (laranja)"),
       (BLK, None, "GND (preto)"), (BLU, None, "sinais (azul)"),
       (GRY, "4,3", "não ligado / ausente (cinza tracejado)")]
for i, (cor, dash, rot) in enumerate(leg):
    y = 236 + i * 20
    poly([(1467, y), (1497, y)], cor, 3, dash)
    txt(1506, y + 4, rot, 11, TXT, "start")

# ---------------------------------------------------------------- CONFERIR / NAO LIGAR
box(1200, 692, 580, 166, fill="#fff8f0", stroke=CONF, sw=1.5, rx=6)
txt(1212, 712, "Itens CONFERIR (laranja) e não ligados (cinza)", 12, CONF, "start", True)
linhas_conf = [
    ("CONFERIR 1: divisor do RX do DY50 (1 kΩ + 1 kΩ até GND): medir.", CONF, True),
    ("   Esperado ~2 kΩ; leitura antiga deu 110 kΩ. Refazer a medição.", CONF, False),
    ("CONFERIR 2: divisor da CAM agora 1 kΩ + 2 x 1 kΩ (era 9 x 330 Ω).", CONF, True),
    ("   Ordem: 1 kΩ do D16 ao meio; 2 x 1 kΩ do meio ao GND. Medir ~3,3 V", CONF, False),
    ("   no meio, com o IO13 solto, antes de ligar a CAM.", CONF, False),
    ("Buzzer: base-GND do BC546 agora 1 kΩ (era 10 kΩ); funciona (análise).", "#666", False),
    ("Não ligados: fechadura (D35, NÃO LIGAR); LED RGB ausente (D32 a D34).", "#666", False),
    ("D0/D1 = USB (não usar). D20/D21 livres.", "#666", False),
]
for i, (t, cor, b) in enumerate(linhas_conf):
    txt(1212, 732 + i * 16, t, 11, cor, "start", b)

# ---------------------------------------------------------------- AVISOS
box(1200, 872, 580, 290, fill="#fff1f1", stroke=RED, sw=2, rx=6)
txt(1212, 894, "AVISOS", 14, RED, "start", True)
avisos = [
    "1. NUNCA 5 V em GPIO da ESP32-CAM (ela trabalha em 3,3 V).",
    "2. DY50 só em 3,3 V (ligado em +3,3V YwRobot (baixo)). Nunca 5 V.",
    "3. NENHUM fio do 5V do Mega na trilha de cima da YwRobot.",
    "4. GND comum entre tudo: Mega, YwRobot, CAM, DY50, LCD, buzzer e botões.",
    "5. Fechadura DESCONECTADA: D35 (TRANCA) NÃO LIGAR; LOCK_MODE=0.",
    "   Só ligar depois do ensaio da MONTAGEM, seção 6.",
    "6. Antes de energizar: conferir a continuidade de cada fio esticado,",
    "   com tudo desligado (USB do Mega e fonte da YwRobot).",
    "7. LCD pino 5 (RW): SEM FIO (solto). Só 4 bits: D4 a D7.",
]
for i, t in enumerate(avisos):
    txt(1212, 918 + i * 20, t, 12, TXT, "start")

txt(60, 1210, "Gerado por scripts/diagramas/gen_eletrico.py. Não substitui a conferência na bancada.",
    11, "#666")

a('</svg>')

Path(SAIDA).write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"Gravado: {Path(SAIDA).resolve()}")
