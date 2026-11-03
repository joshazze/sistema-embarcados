W,H=1400,900
o=[];a=o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#fff"/>')
a('<text x="20" y="36" font-size="23" font-weight="bold">Gravar a ESP32-CAM usando o Mega como adaptador (Mega em RESET)</text>')
for i,t in enumerate(["1) Tudo desligado ao montar. PL2303 fora. Chave da fonte YwRobot desligada.",
"2) Antes de ligar o fio laranja (coluna 43 -> U0R): plugar a USB do Mega e medir coluna 43 -> GND. 002 = ok; 001 = tirar os 3 primeiros resistores; 003+ = parar.",
"3) Depois de gravar: tirar o jumper RESET-GND do Mega e o jumper IO0-GND da CAM."]):
  a(f'<text x="20" y="{70+i*24}" font-size="15">{t}</text>')
def dot(x,y,c): a(f'<circle cx="{x}" cy="{y}" r="6" fill="{c}" stroke="#fff" stroke-width="1.5"/>')
def path(d,c,p1,p2,w=5): a(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>'); dot(*p1,c); dot(*p2,c)
# Mega
mx,my=30,190
a(f'<rect x="{mx}" y="{my}" width="270" height="400" rx="10" fill="#1d4f91"/>')
a(f'<text x="{mx+135}" y="{my+380}" font-size="18" fill="#fff" text-anchor="middle" font-weight="bold">Arduino Mega</text>')
a(f'<rect x="{mx-20}" y="{my+300}" width="60" height="40" fill="#bbb"/><text x="{mx+10}" y="{my+325}" font-size="11" text-anchor="middle">USB Mac</text>')
mp={}
pins=[('RESET',my+40),('GND (a)',my+80),('5V',my+120),('GND (b)',my+160),('pino 0 (RX0)',my+220),('pino 1 (TX0)',my+260)]
for n,y in pins:
  a(f'<rect x="{mx+230}" y="{y-9}" width="40" height="18" fill="#000"/><text x="{mx+222}" y="{y+5}" font-size="14" fill="#fff" text-anchor="end">{n}</text>'); mp[n]=(mx+270,y)
a(f'<text x="{mx+150}" y="{my+20}" font-size="11" fill="#cfe" text-anchor="middle">(texto da placa pode estar trocado: siga o NUMERO)</text>')
# RESET-GND jumper
path(f"M {mp['RESET'][0]} {mp['RESET'][1]} C {mp['RESET'][0]+40} {mp['RESET'][1]}, {mp['GND (a)'][0]+40} {mp['GND (a)'][1]}, {mp['GND (a)'][0]} {mp['GND (a)'][1]}","#7a3fd0",mp['RESET'],mp['GND (a)'])
a(f'<text x="{mp["RESET"][0]+50}" y="{mp["RESET"][1]+25}" font-size="13" fill="#7a3fd0" font-weight="bold">RESET -> GND</text>')
# breadboard bottom-half strip cols 40..49
bx,by=420,560
def cxx(n): return bx+(n-38)*50
a(f'<rect x="{bx-10}" y="{by-60}" width="{cxx(50)-bx+20}" height="150" rx="8" fill="#f3f1ea" stroke="#999"/>')
a(f'<text x="{bx}" y="{by-70}" font-size="13" fill="#555">protoboard, metade de BAIXO (fileiras f a j), colunas 40 a 49 livres</text>')
for n in range(39,50):
  x=cxx(n)
  for k in range(5): a(f'<rect x="{x-3}" y="{by-40+k*22}" width="6" height="6" fill="#999"/>')
  a(f'<text x="{x}" y="{by+80}" font-size="12" text-anchor="middle" fill="#444">{n}</text>')
yr=by-15
def res(n1,n2,lab):
  x1,x2=cxx(n1),cxx(n2)
  a(f'<line x1="{x1}" y1="{yr}" x2="{x2}" y2="{yr}" stroke="#888" stroke-width="2"/>')
  m=(x1+x2)/2
  a(f'<rect x="{m-16}" y="{yr-7}" width="32" height="14" rx="6" fill="#e7cf9a" stroke="#8a7"/>')
  for i,c in enumerate(['#f28c00','#f28c00','#6b3e1e']): a(f'<rect x="{m-10+i*7}" y="{yr-7}" width="3" height="14" fill="{c}"/>')
for n in range(40,49): res(n,n+1,'330')
a(f'<text x="{(cxx(40)+cxx(43))/2}" y="{yr-14}" font-size="12" text-anchor="middle" font-weight="bold">3 x 330 (~1k)</text>')
a(f'<text x="{(cxx(43)+cxx(49))/2}" y="{yr-14}" font-size="12" text-anchor="middle" font-weight="bold">6 x 330 (~2k)</text>')
yb=by+40
path(f"M {mp['pino 0 (RX0)'][0]} {mp['pino 0 (RX0)'][1]} C 360 {mp['pino 0 (RX0)'][1]}, {cxx(40)} {yb+60}, {cxx(40)} {yb}","#2a9d3a",mp['pino 0 (RX0)'],(cxx(40),yb))
a(f'<text x="{cxx(40)-110}" y="{yb+70}" font-size="13" fill="#2a9d3a" font-weight="bold">pino 0 -> coluna 40</text>')
path(f"M {mp['GND (b)'][0]} {mp['GND (b)'][1]} C 380 {mp['GND (b)'][1]+300}, {cxx(49)} {yb+140}, {cxx(49)} {yb}","#111",mp['GND (b)'],(cxx(49),yb))
a(f'<text x="{cxx(49)-40}" y="{yb+70}" font-size="13" fill="#111" font-weight="bold">coluna 49 -> GND</text>')
# CAM
cx0,cy0=1000,160; cw,ch=270,360
a(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="10" fill="#1e2a4a"/>')
a(f'<circle cx="{cx0+cw/2}" cy="{cy0+70}" r="34" fill="#333" stroke="#888" stroke-width="3"/>')
a(f'<text x="{cx0+cw/2}" y="{cy0+130}" font-size="17" fill="#fff" text-anchor="middle" font-weight="bold">ESP32-CAM</text>')
L=['5V','GND','IO12','IO13','IO15','IO14','IO2','IO4']; R=['3V3','IO16','IO0','GND','VCC','U0R','U0T','GND']
pl={};pr={}
for i,(l,r) in enumerate(zip(L,R)):
  y=cy0+160+i*24
  a(f'<circle cx="{cx0+16}" cy="{y}" r="6" fill="#ddd"/><text x="{cx0+30}" y="{y+5}" font-size="13" fill="#fff">{l}</text>')
  a(f'<circle cx="{cx0+cw-16}" cy="{y}" r="6" fill="#ddd"/><text x="{cx0+cw-30}" y="{y+5}" font-size="13" fill="#fff" text-anchor="end">{r}</text>')
  pl[l]=(cx0+16,y); pr[(r,i)]=(cx0+cw-16,y)
IO0=pr[('IO0',2)];G=pr[('GND',3)];U0R=pr[('U0R',5)];U0T=pr[('U0T',6)]
path(f"M {IO0[0]} {IO0[1]} C {IO0[0]+40} {IO0[1]}, {G[0]+40} {G[1]}, {G[0]} {G[1]}","#7a3fd0",IO0,G)
a(f'<text x="{IO0[0]-150}" y="{IO0[1]-12}" font-size="12" fill="#c9a8ff" font-weight="bold">IO0-GND (gravar)</text>')
path(f"M {mp['5V'][0]} {mp['5V'][1]} C 600 {mp['5V'][1]-120}, 900 {pl['5V'][1]}, {pl['5V'][0]} {pl['5V'][1]}","#d81e1e",mp['5V'],pl['5V'])
path(f"M {mp['GND (b)'][0]} {mp['GND (b)'][1]} C 620 {mp['GND (b)'][1]-100}, 900 {pl['GND'][1]}, {pl['GND'][0]} {pl['GND'][1]}","#111",mp['GND (b)'],pl['GND'])
a(f'<text x="640" y="{mp["5V"][1]-60}" font-size="13" fill="#d81e1e" font-weight="bold">5V do Mega -> 5V da CAM</text>')
a(f'<text x="640" y="{mp["GND (b)"][1]-30}" font-size="13" fill="#111" font-weight="bold">GND do Mega -> GND da CAM</text>')
path(f"M {cxx(43)} {yb} C {cxx(43)} {yb+100}, 1340 {yb+60}, 1340 {U0R[1]} L {U0R[0]} {U0R[1]}","#e07b00",(cxx(43),yb),U0R)
a(f'<text x="{cxx(43)+20}" y="{yb+110}" font-size="13" fill="#e07b00" font-weight="bold">coluna 43 -> U0R (so depois da medicao)</text>')
path(f"M {U0T[0]} {U0T[1]} C 1380 {U0T[1]}, 1380 860, 700 860 S {mp['pino 1 (TX0)'][0]+60} {mp['pino 1 (TX0)'][1]}, {mp['pino 1 (TX0)'][0]} {mp['pino 1 (TX0)'][1]}","#e0b000",U0T,mp['pino 1 (TX0)'])
a(f'<text x="560" y="852" font-size="13" fill="#a07a00" font-weight="bold">U0T da CAM -> pino 1 do Mega (direto)</text>')
a('</svg>')
open('cam-ponte-mega.svg','w').write('\n'.join(o))
