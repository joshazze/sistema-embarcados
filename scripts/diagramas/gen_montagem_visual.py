#!/usr/bin/env python3
"""Desenho de montagem (visual) da montagem de uso verificada em 04/11/2026.

Grava 06-montagem-visual.svg na pasta corrente. Só biblioteca padrão.
Regras do desenho: peças perto dos pinos que usam; fios em ângulo reto;
etiqueta de destino nas duas pontas quando o cruzamento seria inevitável.
Ao final, confere que nenhum fio cruza outro (sai com erro se cruzar).
As colunas da protoboard são uma sugestão para a remontagem; vale a ligação.
"""
import sys

W, H = 1840, 1560
out = []
WIRES = []          # (id, [pontos]) para a checagem de cruzamentos


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def add(s):
    out.append(s)


def text(x, y, s, size=12, color="#222", weight="normal", anchor="start", halo=False):
    st = ' style="paint-order:stroke;stroke:#fff;stroke-width:4px;stroke-linejoin:round"' if halo else ""
    add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
        f'text-anchor="{anchor}"{st}>{esc(s)}</text>')


def rect(x, y, w, h, fill, stroke="none", sw=1, rx=0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw}"{d}/>')


def line(x1, y1, x2, y2, color, sw=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d} '
        f'stroke-linecap="round"/>')


def circle(x, y, r, fill, stroke="none", sw=1):
    add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def wire(wid, pts, color, w=3.4):
    """Fio em ângulo reto: pts é a lista de cantos (cada trecho horizontal ou vertical)."""
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        assert x1 == x2 or y1 == y2, (wid, pts)
    WIRES.append((wid, pts))
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    add(f'<path d="{d}" fill="none" stroke="#000" stroke-opacity="0.35" stroke-width="{w + 1.6}" '
        f'stroke-linejoin="round" stroke-linecap="round"/>')
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round" '
        f'stroke-linecap="round"/>')
    for x, y in (pts[0], pts[-1]):
        circle(x, y, 3.2, color, "#000", 0.8)


def tag(wid, p, direction, label, color, fg="#fff", length=16, size=9):
    """Etiqueta de destino: toco de fio curto e caixa com o texto."""
    x, y = p
    dx, dy = {"l": (-1, 0), "r": (1, 0), "u": (0, -1), "d": (0, 1)}[direction]
    end = (x + dx * length, y + dy * length)
    wire(wid, [p, end], color, 3)
    w = len(label) * size * 0.58 + 10
    h = size + 8
    ex, ey = end
    if direction == "l":
        bx, by = ex - w, ey - h / 2
    elif direction == "r":
        bx, by = ex, ey - h / 2
    elif direction == "u":
        bx, by = ex - w / 2, ey - h
    else:
        bx, by = ex - w / 2, ey
    rect(bx, by, w, h, color, "#000", 0.8, 4)
    text(bx + w / 2, by + h - 5, label, size, fg, "bold", "middle")
    WIRES.append((wid + ":box", [(bx, by), (bx + w, by), (bx + w, by + h), (bx, by + h), (bx, by)]))


# ---------------------------------------------------------------- protoboard
X1, P = 420, 15
ROWS = {r: 290 + i * P for i, r in enumerate("abcde")}
ROWS.update({r: 380 + i * P for i, r in enumerate("fghij")})
RAIL = {"top+": 248, "top-": 263, "bot+": 467, "bot-": 482}
NCOL = 60


def hx(c):
    return X1 + (c - 1) * P


def hole(c, r):
    return (hx(c), RAIL[r] if r in RAIL else ROWS[r])


BANDS = {
    "330": ["#f28c28", "#f28c28", "#7b4a1e"],
    "1k": ["#7b4a1e", "#111", "#d62828"],
    "10k": ["#7b4a1e", "#111", "#f28c28"],
    "220": ["#d62828", "#d62828", "#7b4a1e"],
}


def res_body(x1, y1, x2, y2, val, label=True, vertical=False):
    line(x1, y1, x2, y2, "#888", 2)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if vertical:
        rect(mx - 5, my - 14, 10, 28, "#e8cf9a", "#8a6d3b", 1, 4)
        for i, b in enumerate(BANDS[val]):
            rect(mx - 5, my - 9 + i * 6, 10, 3, b)
        if label:
            text(mx + 9, my + 4, val + " Ω", 9, "#333", "bold", "start", halo=True)
    else:
        rect(mx - 14, my - 5, 28, 10, "#e8cf9a", "#8a6d3b", 1, 4)
        for i, b in enumerate(BANDS[val]):
            rect(mx - 9 + i * 6, my - 5, 3, 10, b)
        if label:
            text(mx, my - 8, val + " Ω", 9, "#333", "bold", "middle", halo=True)


def resistor(c1, r1, c2, r2, val, label=True):
    (x1, y1), (x2, y2) = hole(c1, r1), hole(c2, r2)
    res_body(x1, y1, x2, y2, val, label)


def jumper(wid, c1, r1, c2, r2, color):
    wire(wid, [hole(c1, r1), hole(c2, r2)], color, 3)


def lbl(c, r, s=None, dx=0, dy=-7, color="#c1121f"):
    x, y = hole(c, r)
    text(x + dx, y + dy, s or f"{r}{c}", 8, color, "bold", "middle", halo=True)


add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
    f'font-family="Helvetica, Arial, sans-serif">')
rect(0, 0, W, H, "#ffffff")

# ---------------------------------------------------------------- cabeçalho
text(24, 34, "Montagem de uso: Mega 1 + YwRobot + CAM + DY50 + teclado + LCD 4 bits + buzzer (verificada em 04/11/2026)",
     20, "#111", "bold")
notas = [
    "1) Vale a LIGAÇÃO. As colunas da protoboard são sugestão para a remontagem. Tudo desligado enquanto monta (USB do Mega fora, chave da YwRobot em OFF).",
    "2) Fio desenhado = ligação física. Etiqueta colorida = a ponta do fio; a outra ponta tem a etiqueta correspondente (ex.: \"D36 -> a11\" no Mega e \"a11 <- D36\" na protoboard).",
    "3) Bandeiras de energia: \"+5V cima\" = trilha vermelha de cima (jumper 5V); \"+3,3V baixo\" = trilha vermelha de baixo (jumper 3.3); \"GND\" = trilha azul; \"5V Mega\" = pino 5V do Mega.",
    "4) O 5V do Mega NUNCA entra nas trilhas da YwRobot: ele alimenta só o LCD, o potenciômetro e o 220 Ω. Nunca 5 V em GPIO da ESP32-CAM. DY50 só em 3,3 V.",
    "5) Fechadura (TRANCA) desconectada, D35 sem fio, LOCK_MODE=0. Furos da mesma coluna (a-e, ou f-j) já são ligados por dentro.",
]
for i, s in enumerate(notas):
    text(24, 58 + i * 18, s, 12, "#333")

# ---------------------------------------------------------------- YwRobot + protoboard
rect(400, 230, 925, 270, "#f4f1ea", "#bbb", 1.5, 8)
rect(326, 222, 80, 286, "#151515", "#000", 1, 6)
text(366, 330, "fonte", 12, "#fff", "bold", "middle")
text(366, 346, "YwRobot", 12, "#fff", "bold", "middle")
text(366, 362, "MB102", 11, "#ccc", "normal", "middle")
text(366, 384, "DC-in 7 V", 10, "#ccc", "normal", "middle")
rect(340, 232, 52, 20, "#f5c400", "#000", 1, 3)
text(366, 247, "5V", 12, "#000", "bold", "middle")
rect(340, 476, 52, 20, "#f5c400", "#000", 1, 3)
text(366, 491, "3.3", 12, "#000", "bold", "middle")
text(366, 272, "jumper de cima", 8, "#f5c400", "normal", "middle")
text(366, 470, "jumper de baixo", 8, "#f5c400", "normal", "middle")
rect(296, 380, 32, 22, "#333", "#000", 1, 4)
text(292, 395, "7 V", 10, "#333", "bold", "end")
for y, col in ((RAIL["top+"] - 7, "#d62828"), (RAIL["top-"] + 7, "#1d4ed8"),
               (RAIL["bot+"] - 7, "#d62828"), (RAIL["bot-"] + 7, "#1d4ed8")):
    line(X1 - 10, y, hx(NCOL) + 10, y, col, 1.5)
for c in range(1, NCOL + 1):
    for r in "abcdefghij":
        x, y = hole(c, r)
        rect(x - 2.5, y - 2.5, 5, 5, "#555", rx=1)
    for key in RAIL:
        x, y = hole(c, key)
        rect(x - 2.5, y - 2.5, 5, 5, "#555", rx=1)
    if c == 1 or c % 5 == 0:
        text(hx(c), 280, str(c), 8, "#777", "normal", "middle")
        text(hx(c), 372, str(c), 8, "#777", "normal", "middle")
for r in "abcdefghij":
    text(X1 - 12, ROWS[r] + 3, r, 8, "#777", "normal", "middle")
rect(X1 - 8, 360, hx(NCOL) - X1 + 16, 4, "#e2ddd0")
text(hx(NCOL) + 8, 244, "+5V", 9, "#d62828", "bold")
text(hx(NCOL) + 8, 268, "GND", 9, "#1d4ed8", "bold")
text(860, 241, "cima: vermelha = +5V YwRobot (CAM e buzzer); azul = GND. Nenhum fio do 5V do Mega aqui.", 9,
     "#d62828", "bold", "middle")
text(hx(2), 498, "baixo: vermelha = +3,3V (só DY50); azul = GND", 9, "#d62828", "bold", "start")

# ---------------------------------------------------------------- buzzer + BC546 (metade de cima, colunas 2 a 11)
bzx, bzy = 480, 196
circle(bzx, bzy, 17, "#1a1a1a", "#000")
circle(bzx, bzy, 4, "#555")
text(bzx - 24, bzy - 6, "+", 14, "#d62828", "bold", "middle")
text(bzx + 24, bzy - 6, "-", 14, "#333", "bold", "middle")
text(bzx, bzy - 24, "buzzer ativo", 10, "#111", "bold", "middle")
wire("bz+", [(bzx - 10, bzy + 12), (bzx - 10, 222), (hx(4), 222), hole(4, "top+")], "#d62828", 3)
wire("bz-", [(bzx + 10, bzy + 12), (bzx + 10, 222), (hx(6), 222), hole(6, "a")], "#666", 3)
add(f'<path d="M{hx(6) - 6},{ROWS["e"] + 4} L{hx(8) + 6},{ROWS["e"] + 4} A22,22 0 0 1 {hx(6) - 6},{ROWS["e"] + 4} Z" '
    f'fill="#111" stroke="#000"/>')
for c, s in ((6, "C"), (7, "B"), (8, "E")):
    text(hx(c), ROWS["e"] + 13, s, 8, "#fff", "bold", "middle")
for c in (6, 7, 8):
    line(hx(c), ROWS["e"], hx(c), ROWS["e"] + 4, "#999", 2)
text(hx(9) + 2, ROWS["e"] + 10, "BC546 (face escrita p/ você)", 8, "#111", "bold", "start", halo=True)
resistor(7, "c", 11, "c", "330")
resistor(7, "b", 3, "b", "1k")
text(hx(5), ROWS["b"] + 11, "1k (era 10k)", 7, "#555", "bold", "middle", halo=True)
jumper("j3t", 3, "a", 3, "top-", "#111")
jumper("j8t", 8, "a", 8, "top-", "#111")
tag("t-a11", hole(11, "a"), "r", "a11 <- D36", "#a16207", length=20)

# ---------------------------------------------------------------- divisor da CAM (metade de baixo, 30 -> 3)
resistor(30, "i", 26, "i", "1k")
resistor(26, "h", 22, "h", "1k")
resistor(22, "i", 18, "i", "1k")
jumper("j18b", 18, "j", 18, "bot-", "#111")
rect(hx(17) - 6, ROWS["f"] - 8, hx(31) - hx(17) + 12, 76, "none", "#7c3aed", 1.2, 4, "4,3")
text(hx(24), ROWS["f"] + 4, "divisor da CAM: 1 kΩ em cima, 2 x 1 kΩ embaixo", 8, "#6d28d9", "bold", "middle", halo=True)
text(hx(26), ROWS["g"] + 4, "coluna 26 = MEIO: medir ~3,3 V", 8, "#6d28d9", "bold", "middle", halo=True)
lbl(30, "j", dx=12, dy=4)
lbl(26, "j", dx=-12, dy=4)

# ---------------------------------------------------------------- divisor do DY50 (metade de baixo, 34 -> 44)
resistor(34, "i", 38, "i", "1k")
resistor(38, "h", 41, "h", "1k")
resistor(41, "i", 44, "i", "1k")
jumper("j44b", 44, "j", 44, "bot-", "#111")
rect(hx(33) - 6, ROWS["f"] - 8, hx(45) - hx(33) + 12, 76, "none", "#d97706", 1.2, 4, "4,3")
text(hx(39), ROWS["f"] + 4, "divisor do DY50 (3 x 1 kΩ)", 9, "#b45309", "bold", "middle", halo=True)
text(hx(39), ROWS["g"] + 4, "coluna 38 = RX do DY50", 8, "#b45309", "bold", "middle", halo=True)
lbl(34, "j", dx=-12, dy=4)
lbl(38, "j", dx=12, dy=4)

# ---------------------------------------------------------------- Arduino Mega 1
MX, MY, MW, MH = 470, 600, 640, 450
rect(MX, MY, MW, MH, "#1f4e9c", "#0d2c5e", 2, 12)
rect(MX - 18, MY + 300, 50, 60, "#b8b8b8", "#666", 1, 4)
text(MX + 40, MY + 336, "USB -> Mac", 10, "#fff", "bold")
text(MX + 230, MY + 150, "Arduino Mega 2560", 24, "#fff", "bold", "middle")
text(MX + 230, MY + 174, "(Mega 1)", 14, "#dce6ff", "normal", "middle")
text(MX + 230, MY + 198, "serigrafia do clone troca 18/19: medido, 18 = TX1", 10, "#ffd166", "normal", "middle")
COMM = {}
for i, n in enumerate(range(14, 22)):
    x = hx(26 + 2 * i)
    COMM[n] = (x, MY + 14)
    rect(x - 9, MY + 5, 18, 18, "#111", "#000", 1, 2)
    circle(x, MY + 14, 3.5, "#c9a227")
    text(x, MY + 38, str(n), 10, "#fff", "bold", "middle")
for i, s in enumerate(["TX3", "RX3", "TX2", "RX2", "TX1", "RX1", "SDA", "SCL"]):
    text(hx(26 + 2 * i), MY + 50, s, 8, "#dce6ff", "normal", "middle")
EVX, ODX = MX + MW - 66, MX + MW - 40
ROWY0, RP = MY + 80, 26
DBL = {}
rows = [("5V", "5V")] + [(str(a), str(a + 1)) for a in range(22, 44, 2)] + [("GND", "GND")]
for i, (ev, od) in enumerate(rows):
    y = ROWY0 + i * RP
    for x, name in ((EVX, ev), (ODX, od)):
        rect(x - 7, y - 7, 14, 14, "#111", "#000", 1, 2)
        circle(x, y, 3.2, "#c9a227")
        DBL.setdefault(name, []).append((x, y))
    text(EVX - 12, y + 4, ev, 9, "#fff", "bold", "end") if False else None
    text(ODX + 14, y + 4, od, 9, "#fff", "bold", "start") if False else None
text(EVX, ROWY0 - 18, "par", 8, "#dce6ff", "normal", "middle")
text(ODX, ROWY0 - 18, "ímpar", 8, "#dce6ff", "normal", "middle")


def mpin(name):
    if name in ("5V", "GND"):
        return DBL[name][0]
    n = int(name)
    return COMM[n] if n in COMM else DBL[str(n)][0]


# rótulos dos pinos do header duplo dentro da placa (à esquerda) para os que não têm etiqueta
for i, (ev, od) in enumerate(rows):
    y = ROWY0 + i * RP
    text(EVX - 140 if ev in ("22", "24", "26", "28", "36", "5V", "GND") else EVX - 12, y + 4,
         "" if ev in ("22", "24", "26", "28", "32", "36", "5V", "GND") else ev, 9, "#fff", "bold", "end")

# ---------------------------------------------------------------- ESP32-CAM (à esquerda, perto do D16/D17)
CX, CY = 110, 600
rect(CX, CY, 180, 250, "#111", "#000", 1.5, 8)
circle(CX + 95, CY + 70, 26, "#333", "#777", 2)
circle(CX + 95, CY + 70, 12, "#0b1a3a", "#555", 1)
rect(CX + 70, CY + 6, 50, 14, "#c9a227", rx=2)
text(CX + 95, CY + 130, "ESP32-CAM", 13, "#fff", "bold", "middle")
text(CX + 95, CY + 146, "(AI-Thinker)", 10, "#bbb", "normal", "middle")
CAM = {}
left = ["5V", "GND", "IO12", "IO13", "IO15", "IO14", "IO2", "IO4"]
right = ["3V3", "IO16", "IO0", "GND", "VCC", "U0R", "U0T", "GND"]
for i, (a, b) in enumerate(zip(left, right)):
    y = CY + 52 + i * 24
    rect(CX + 4, y - 6, 12, 12, "#ddd", "#888", 1, 2)
    text(CX + 22, y + 4, a, 10, "#7dd3fc" if a in ("IO13", "IO14", "5V", "GND") else "#fff", "bold")
    CAM[a] = (CX + 4, y)
    rect(CX + 164, y - 6, 12, 12, "#ddd", "#888", 1, 2)
    text(CX + 158, y + 4, b, 10, "#fff", "bold", "end")
text(CX + 90, CY + 268, "IO0 solto (GND só para gravar)", 9, "#333", "normal", "middle")
text(CX + 90, CY + 281, "U0R/U0T sem fio na montagem de uso", 9, "#333", "normal", "middle")
text(CX + 90, CY - 10, "nunca 5 V em GPIO da CAM", 10, "#c1121f", "bold", "middle")

# ---------------------------------------------------------------- DY50 (à direita, perto do D18/D19)
DX, DY = 1440, 440
rect(DX, DY, 200, 200, "#1b1b1b", "#000", 1.5, 8)
text(DX + 110, DY + 90, "DY50", 16, "#fff", "bold", "middle")
text(DX + 110, DY + 108, "leitor de digital", 10, "#bbb", "normal", "middle")
text(DX + 110, DY + 124, "cabo cortado:", 9, "#bbb", "normal", "middle")
text(DX + 110, DY + 136, "siga o mapa de vocês", 9, "#bbb", "normal", "middle")
DYP = {}
for nm, y in (("3V3", 467), ("GND", 482), ("RX", 530), ("TX", 575)):
    rect(DX - 6, y - 6, 12, 12, "#ddd", "#888", 1, 2)
    text(DX + 12, y + 4, nm, 10, "#fff", "bold")
    DYP[nm] = (DX - 6, y)
text(DX + 110, DY + 160, "T_OUT e T_3V3: isolados com fita", 8, "#fca", "normal", "middle")
text(DX + 110, DY + 174, "ordem dos fios no desenho: só ilustração", 8, "#fca", "normal", "middle")

# ---------------------------------------------------------------- teclado 4x4 (ao lado do header, etiquetas)
KX, KY = 1400, 730
rect(KX, KY, 210, 250, "#111", "#000", 2, 10)
keys = ["1", "2", "3", "A", "4", "5", "6", "B", "7", "8", "9", "C", "*", "0", "#", "D"]
for i, k in enumerate(keys):
    r, c = divmod(i, 4)
    x, y = KX + 18 + c * 47, KY + 52 + r * 47
    rect(x, y, 38, 38, "#f8b4b4" if k in "ABCD" else "#fafafa", "#999", 1, 5)
    text(x + 19, y + 26, k, 16, "#111", "bold", "middle")
KP = {}
kmap = ["C1", "C2", "C3", "C4", "R1", "R2", "R3", "R4"]
for i, nm in enumerate(kmap):
    x = KX + 35 + i * 20
    rect(x - 7, KY + 4, 14, 14, "#ccc", "#666", 1, 2)
    text(x, KY + 32, str(i + 1), 9, "#fff", "bold", "middle")
    text(x, KY + 44, nm, 8, "#fca", "bold", "middle")
    KP[i + 1] = (x, KY + 4)
text(KX + 105, KY + 266, "pinos 1 a 4 = C1 a C4; 5 a 8 = R1 a R4", 10, "#111", "bold", "middle")
text(KX + 105, KY + 280, "(o desenho antigo da Mesa tinha essa ordem trocada)", 9, "#c1121f", "normal", "middle")

# ---------------------------------------------------------------- LCD 1602, visto por trás (lado dos pinos)
LX, LY, LW = 1170, 1140, 450
rect(LX, LY, LW, 140, "#1f7a3a", "#0e3d1c", 2, 8)
rect(LX + 120, LY + 50, 210, 70, "#2f8f4a", "#145a2a", 1, 30)
text(LX + LW / 2, LY + 88, "verso do LCD", 13, "#cfe", "bold", "middle")
LCDP = {}
names = ["VSS", "VDD", "V0", "RS", "RW", "E", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "A", "K"]
for i, nm in enumerate(names):
    n = i + 1
    x = LX + 30 + (16 - n) * 26
    rect(x - 7, LY + 6, 14, 14, "#111", "#000", 1, 2)
    circle(x, LY + 13, 3, "#c9a227")
    text(x, LY + 32, str(n), 9, "#fff", "bold", "middle")
    text(x, LY + 44, nm, 8, "#cfe", "normal", "middle")
    LCDP[n] = (x, LY + 6)
text(LX + LW / 2, LY + 112, "LCD 1602 em 4 bits, visto POR TRÁS: pino 1 fica à direita", 9, "#fff", "bold", "middle")
text(LX + LW / 2, LY + 126, "Pinos 7 a 10 sem fio. Pino 5 (RW) SEM FIO.", 9, "#ffd0d0", "bold", "middle")
for n in (7, 8, 9, 10):
    x, y = LCDP[n]
    line(x - 4, y + 3, x + 4, y + 11, "#999", 1.5)
    line(x - 4, y + 11, x + 4, y + 3, "#999", 1.5)
xrw, yrw = LCDP[5]
line(xrw - 6, yrw + 1, xrw + 6, yrw + 13, "#c1121f", 3)
line(xrw - 6, yrw + 13, xrw + 6, yrw + 1, "#c1121f", 3)

# ---------------------------------------------------------------- fios: CAM e DY50 (header de comunicação)
wire("D16", [COMM[16], hole(30, "j")], "#a855f7")
wire("IO13", [hole(26, "j"), (hx(26), 525), (320, 525), (320, 900), (30, 900), (30, CAM["IO13"][1]), CAM["IO13"]],
     "#7c3aed")
wire("C5V", [CAM["5V"], (75, CAM["5V"][1]), (75, 225), (hx(1), 225), hole(1, "top+")], "#d62828")
wire("CGND", [CAM["GND"], (60, CAM["GND"][1]), (60, 205), (hx(2), 205), hole(2, "top-")], "#111")
text(200, 219, "5V da CAM -> trilha vermelha de CIMA (+5V YwRobot)", 9, "#d62828", "bold", "middle", halo=True)
text(200, 199, "GND da CAM -> trilha azul de CIMA (junto do 5V)", 9, "#111", "bold", "middle", halo=True)
wire("DY33", [hole(60, "bot+"), DYP["3V3"]], "#ea580c")
wire("DYG", [hole(60, "bot-"), DYP["GND"]], "#111")
text(1372, 461, "+3,3V -> 3V3 do DY50", 8, "#c2410c", "bold", "middle", halo=True)
text(1372, 497, "GND -> GND do DY50", 8, "#111", "bold", "middle", halo=True)
text(560, 519, "meio (j26) -> IO13 da CAM", 9, "#6d28d9", "bold", "middle", halo=True)
tag("t-D17", COMM[17], "u", "<- IO14", "#0891b2", length=12, size=8)
tag("t-IO14", CAM["IO14"], "l", "IO14 -> D17", "#0891b2", length=8, size=8)
wire("D18", [COMM[18], hole(34, "j")], "#16a34a")
wire("RX", [hole(38, "j"), (hx(38), 530), DYP["RX"]], "#f77f00")
text(1250, 524, "j38 -> RX do DY50", 9, "#c2410c", "bold", "middle", halo=True)
wire("D19", [COMM[19], (COMM[19][0], 575), DYP["TX"]], "#db2777")
text(1250, 569, "TX do DY50 -> D19 (RX1)", 9, "#be185d", "bold", "middle", halo=True)

# ---------------------------------------------------------------- header duplo: etiquetas à esquerda (pinos pares)
for name, label, color in (("22", "D22 -> teclado 5 (R1)", "#1d4ed8"),
                           ("24", "D24 -> teclado 7 (R3)", "#16a34a"),
                           ("26", "D26 -> teclado 1 (C1)", "#dc2626"),
                           ("28", "D28 -> teclado 3 (C3)", "#92400e"),
                           ("36", "D36 -> a11 (buzzer)", "#a16207"),
                           ("GND", "GND -> trilhas azuis", "#111")):
    tag("h-" + name, mpin(name), "l", label, color, length=10, size=8)
# pares que vão para a direita sobem até o vão entre linhas
for name in ("30", "38", "40", "42"):
    pass
# etiquetas à direita (pinos ímpares) para o teclado
for name, label, color in (("23", "D23 -> teclado 6 (R2)", "#0891b2"),
                           ("25", "D25 -> teclado 8 (R4)", "#65a30d"),
                           ("27", "D27 -> teclado 2 (C2)", "#ea580c"),
                           ("29", "D29 -> teclado 4 (C4)", "#c026d3")):
    tag("h-" + name, DBL[name][0], "r", label, color, length=10, size=8)
for k, (lab, color) in {1: ("D26", "#dc2626"), 2: ("D27", "#ea580c"), 3: ("D28", "#92400e"), 4: ("D29", "#c026d3"),
                        5: ("D22", "#1d4ed8"), 6: ("D23", "#0891b2"), 7: ("D24", "#16a34a"),
                        8: ("D25", "#65a30d")}.items():
    x, y = KP[k]
    wire(f"k{k}", [(x, y), (x, y - 14 - (k % 2) * 18)], color, 3)
    rect(x - 13, y - 30 - (k % 2) * 18, 26, 14, color, "#000", 0.8, 3)
    text(x, y - 20 - (k % 2) * 18, lab, 8, "#fff", "bold", "middle")

# D35 e LED RGB
x35, y35 = DBL["35"][0]
line(x35 - 6, y35 - 6, x35 + 6, y35 + 6, "#ff6b6b", 2.5)
line(x35 - 6, y35 + 6, x35 + 6, y35 - 6, "#ff6b6b", 2.5)
text(x35 + 14, y35 + 4, "D35 TRANCA: NÃO LIGAR", 9, "#c1121f", "bold", "start", halo=True)
for n in ("32", "33", "34"):
    x, y = DBL[n][0]
    circle(x, y, 6, "none", "#aaa", 1.5)
text(EVX - 12, DBL["32"][0][1] + 4, "D32-D34: LED RGB ausente", 8, "#cbd5e1", "normal", "end")

# botões da porta D30 (par) e D31 (ímpar)
gapy = DBL["30"][0][1] - RP / 2
x30, y30 = DBL["30"][0]
x31, y31 = DBL["31"][0]
for wid, sx, pts, yy in (("D30", 1190, [(x30, y30), (x30 + 13, y30), (x30 + 13, gapy), (1190, gapy)], gapy),
                         ("D31", 1280, [(x31, y31), (1280, y31)], y31)):
    wire(wid, pts, "#64748b", 2.8)
    line(sx, yy, sx + 24, yy - 10, "#111", 2.5)
    circle(sx, yy, 3, "#111")
    circle(sx + 28, yy, 3, "#111")
    tag(wid + "g", (sx + 28, yy), "r", "GND", "#111", length=10, size=8)
text(1235, y31 + 22, "D30 e D31: contatos da porta", 9, "#334155", "bold", "middle", halo=True)

# ---------------------------------------------------------------- LCD: fios do header (direita -> baixo -> direita)
lcd_sig = [("37", 4, "#0ea5e9"), ("38", 6, "#14b8a6"), ("39", 11, "#8b5cf6"), ("40", 12, "#f97316"),
           ("41", 13, "#84cc16"), ("42", 14, "#ec4899")]
for i, (pin, lp, color) in enumerate(lcd_sig):
    px, py = DBL[pin][0]
    lane = 1160 - i * 10
    yh = 1080 + i * 9
    tx, ty = LCDP[lp]
    if int(pin) % 2 == 0:       # par: sobe para o vão acima e passa entre os pinos ímpares
        gy = py - RP / 2
        pts = [(px, py), (px + 13, py), (px + 13, gy), (lane, gy), (lane, yh), (tx, yh), (tx, ty)]
    else:
        pts = [(px, py), (lane, py), (lane, yh), (tx, yh), (tx, ty)]
    wire("L" + pin, pts, color, 3)
text(1060, 1075, "D37 RS, D38 E, D39-D42 = D4-D7", 9, "#111", "bold", "end", halo=True)

# LCD: energia pela trilha solta (barramento só do LCD). O 5V do Mega serve só ao LCD.
SY_M, SY_P = 1312, 1327                   # linha azul (-) em cima, vermelha (+) embaixo, como na peça
SX0, SX1 = 1100, 1810
rect(SX0 - 10, SY_M - 14, SX1 - SX0 + 20, 30, "#f4f1ea", "#bbb", 1.5, 4)
line(SX0, SY_M - 8, SX1, SY_M - 8, "#1d4ed8", 1.5)
line(SX0, SY_P + 8, SX1, SY_P + 8, "#d62828", 1.5)
for x in range(SX0, SX1 + 1, 15):
    rect(x - 2.5, SY_M - 2.5, 5, 5, "#555", rx=1)
    rect(x - 2.5, SY_P - 2.5, 5, 5, "#555", rx=1)
text(SX0 + 330, SY_P + 30, "trilha solta só do LCD: vermelha (+) = 5V do Mega; azul (-) = GND do Mega", 10, "#b91c1c",
     "bold", "middle")
text(SX0 + 330, SY_P + 44, "medir continuidade de ponta a ponta antes (pode ser cortada no meio)", 9, "#555",
     "normal", "middle")
x5, y5 = DBL["5V"][1]
xg, yg = DBL["GND"][1]
wire("V5", [(x5, y5), (1090, y5), (1090, 652), (1825, 652), (1825, SY_P), (1795, SY_P)], "#d62828")
text(1420, 646, "5V do Mega -> trilha solta (+)", 9, "#d62828", "bold", "middle", halo=True)
wire("MG", [(xg, yg), (1095, yg), (1095, SY_M), (1115, SY_M)], "#111")
text(1088, 1300, "GND do Mega -> trilha solta (-)", 9, "#111", "bold", "end", halo=True)
p1, p2, p3 = LCDP[1], LCDP[2], LCDP[3]
wire("V0", [p3, (p3[0], 1070), (1790, 1070), (1790, 1385), (1716, 1385)], "#2563eb", 3)
wire("VDD", [p2, (p2[0], 1085), (1775, 1085), (1775, SY_P)], "#d62828", 3)
wire("VSS", [p1, (p1[0], 1100), (1745, 1100), (1745, SY_M)], "#111", 3)
text(1700, 1064, "pino 3 (V0) -> meio do pot", 9, "#1d4ed8", "bold", "middle", halo=True)
text(1690, 1094, "pino 2 (VDD) -> +", 8, "#b91c1c", "bold", "middle", halo=True)
text(1690, 1116, "pino 1 (VSS) -> -", 8, "#111", "bold", "middle", halo=True)
potx, poty = 1700, 1385
rect(potx - 16, poty - 16, 32, 32, "#2b59c3", "#123", 1, 4)
circle(potx, poty, 9, "#ddd", "#555")
line(potx, poty, potx + 8, poty, "#333", 2)
wire("PG", [(potx - 8, poty - 16), (potx - 8, SY_M)], "#111", 3)
wire("PP", [(potx + 8, poty - 16), (potx + 8, SY_P)], "#d62828", 3)
text(potx - 22, poty + 4, "pot 10 kΩ", 9, "#123", "bold", "end", halo=True)
text(potx - 22, poty + 16, "(por cabos)", 8, "#555", "normal", "end", halo=True)
ax, ay = LCDP[15]
kx, ky = LCDP[16]
wire("A", [(ax, ay), (ax, 1130), (1120, 1130), (1120, SY_P)], "#d62828", 3)
res_body(1120, 1185, 1120, 1235, "220", vertical=False and True) if False else None
rect(1115, 1196, 10, 28, "#e8cf9a", "#8a6d3b", 1, 4)
for i, b in enumerate(BANDS["220"]):
    rect(1115, 1201 + i * 6, 10, 3, b)
text(1112, 1214, "220 Ω", 9, "#333", "bold", "end", halo=True)
text(1112, 1250, "pino 15 (A) -> 220 Ω -> +", 8, "#b91c1c", "bold", "end", halo=True)
wire("K", [(kx, ky), (kx, 1138), (1135, 1138), (1135, SY_M)], "#111", 3)
text(1141, 1270, "pino 16 (K) -> -", 8, "#111", "bold", "start", halo=True)

# ---------------------------------------------------------------- caixas de texto
def box(x, y, w, h, title, lines, border, fill, tcolor):
    rect(x, y, w, h, fill, border, 1.5, 8)
    text(x + 12, y + 22, title, 13, tcolor, "bold")
    for i, (s, c, wgt) in enumerate(lines):
        text(x + 12, y + 42 + i * 16, s, 11, c, wgt)


box(30, 1080, 430, 230, "Ordem para religar (tudo desligado até o fim)", [
    ("1. YwRobot encaixada, chave OFF; jumpers: cima 5V, baixo 3.3.", "#222", "normal"),
    ("2. Na protoboard: divisores (CAM e DY50), buzzer e BC546.", "#222", "normal"),
    ("3. Mega: GND nas trilhas azuis; 5V só no LCD, pot e 220 Ω.", "#222", "normal"),
    ("4. CAM, DY50, LCD, teclado e botões pelos fios e etiquetas.", "#222", "normal"),
    ("5. Continuidade de cada fio esticado, ponta a ponta.", "#222", "normal"),
    ("6. Em ohms: coluna 26 até GND ~2 kΩ; coluna 38 até GND ~2 kΩ.", "#222", "normal"),
    ("7. Liga a YwRobot: trilha de baixo 3,3 V; trilha de cima 5 V.", "#222", "normal"),
    ("8. USB do Mega: coluna 26 ~3,3 V (IO13 solto); depois liga o IO13.", "#222", "normal"),
], "#2563eb", "#eff6ff", "#1d4ed8")

box(30, 1325, 560, 95, "CONFERIR (não confirmado nos registros)", [
    ("1. Divisor do DY50 (coluna 38 até GND): esperado ~2 kΩ; leitura antiga 110 kΩ.", "#b45309", "bold"),
    ("2. Divisor da CAM (1 kΩ + 2 x 1 kΩ): meio ~3,3 V antes de ligar o IO13.", "#b45309", "bold"),
    ("Cores dos fios são ilustração; vale o pino de cada ponta.", "#555", "normal"),
], "#d97706", "#fff7ed", "#b45309")

box(610, 1345, 470, 190, "AVISOS", [
    ("Nunca 5 V em GPIO da ESP32-CAM; o 5V dela vai só na trilha de cima.", "#c1121f", "bold"),
    ("DY50 só em 3,3 V (trilha vermelha de baixo).", "#c1121f", "bold"),
    ("O 5V do Mega não toca as trilhas da YwRobot.", "#c1121f", "bold"),
    ("GND comum: Mega nas trilhas azuis; tudo o mais no GND.", "#222", "normal"),
    ("Fechadura desconectada; D35 sem fio até a MONTAGEM, seção 6.", "#222", "normal"),
    ("CAM: IO0 solto; U0R/U0T sem fio. Mega 2 fora desta montagem.", "#222", "normal"),
    ("LCD: RW (pino 5) sem fio; pinos 7 a 10 sem fio.", "#222", "normal"),
    ("Gerado por scripts/diagramas/gen_montagem_visual.py.", "#777", "normal"),
], "#c1121f", "#fff1f2", "#c1121f")

box(1170, 1440, 640, 100, "Alimentação do LCD (o 5V do Mega serve só a ele)", [
    ("Mega 5V -> trilha solta (+): LCD pino 2, uma ponta do pot, 220 Ω do pino 15.", "#b91c1c", "bold"),
    ("Mega GND -> trilha solta (-): LCD pinos 1 e 16 e a outra ponta do pot.", "#222", "normal"),
    ("Cursor do pot -> LCD pino 3 (V0). CAM, DY50 e buzzer usam a YwRobot.", "#222", "normal"),
], "#d62828", "#fff5f5", "#b91c1c")

add("</svg>")


# ---------------------------------------------------------------- checagem de cruzamentos
def segs(pts):
    return list(zip(pts, pts[1:]))


def inter(s1, s2):
    (a, b), (c, d) = s1, s2

    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)

    def on(p, q, r):
        return min(p[0], r[0]) - 1e-9 <= q[0] <= max(p[0], r[0]) + 1e-9 and \
            min(p[1], r[1]) - 1e-9 <= q[1] <= max(p[1], r[1]) + 1e-9
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    return (o1 == 0 and on(a, c, b)) or (o2 == 0 and on(a, d, b)) or (o3 == 0 and on(c, a, d)) or \
        (o4 == 0 and on(c, b, d))


def base(w):
    return w.split(":")[0]


problems = []
for i in range(len(WIRES)):
    for j in range(i + 1, len(WIRES)):
        a, b = WIRES[i], WIRES[j]
        if base(a[0]) == base(b[0]):
            continue
        for s1 in segs(a[1]):
            for s2 in segs(b[1]):
                if inter(s1, s2):
                    problems.append((a[0], b[0], s1, s2))
with open("06-montagem-visual.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
if problems:
    for p in problems:
        print("CRUZA:", p)
    sys.exit(1)
print("ok 06-montagem-visual.svg; fios:", len([w for w in WIRES if ":" not in w[0]]), "; cruzamentos: 0")
