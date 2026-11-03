W,H=1100,720
o=[];a=o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#fff"/>')
a('<text x="20" y="36" font-size="23" font-weight="bold">Gravar a ESP32-CAM so pelo PL2303 (CAM fora da protoboard)</text>')
for i,t in enumerate(["1) CAM sem nenhum fio para a protoboard (nem 5V, nem GND). Fonte YwRobot nao alimenta a CAM agora.",
"2) PL2303 fora da USB enquanto liga os fios. Depois pluga no Mac: a CAM liga em modo de gravacao.",
"3) Depois de gravar: tirar o PL2303 da USB e tirar o jumper IO0-GND."]): a(f'<text x="20" y="{70+i*24}" font-size="15">{t}</text>')
def dot(x,y,c): a(f'<circle cx="{x}" cy="{y}" r="6" fill="{c}" stroke="#fff" stroke-width="1.5"/>')
def path(d,c,p1,p2,w=5): a(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>'); dot(*p1,c); dot(*p2,c)
cx0,cy0=120,200; cw,ch=280,420
a(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="10" fill="#1e2a4a"/>')
a(f'<circle cx="{cx0+cw/2}" cy="{cy0+90}" r="40" fill="#333" stroke="#888" stroke-width="3"/><circle cx="{cx0+cw/2}" cy="{cy0+90}" r="15" fill="#123"/>')
a(f'<text x="{cx0+cw/2}" y="{cy0+165}" font-size="18" fill="#fff" text-anchor="middle" font-weight="bold">ESP32-CAM</text>')
a(f'<text x="{cx0+cw/2}" y="{cy0+185}" font-size="12" fill="#ccc" text-anchor="middle">(camera para cima)</text>')
L=['5V','GND','IO12','IO13','IO15','IO14','IO2','IO4']; R=['3V3','IO16','IO0','GND','VCC','U0R','U0T','GND']
pl={};pr={}
for i,(l,r) in enumerate(zip(L,R)):
  y=cy0+215+i*24
  a(f'<circle cx="{cx0+16}" cy="{y}" r="6" fill="#ddd"/><text x="{cx0+30}" y="{y+5}" font-size="13" fill="#fff">{l}</text>')
  a(f'<circle cx="{cx0+cw-16}" cy="{y}" r="6" fill="#ddd"/><text x="{cx0+cw-30}" y="{y+5}" font-size="13" fill="#fff" text-anchor="end">{r}</text>')
  pl[l]=(cx0+16,y); pr[(r,i)]=(cx0+cw-16,y)
IO0=pr[('IO0',2)]; G=pr[('GND',3)]; U0R=pr[('U0R',5)]; U0T=pr[('U0T',6)]
# IO0-GND jumper
a(f'<path d="M {IO0[0]} {IO0[1]} C {IO0[0]+40} {IO0[1]}, {G[0]+40} {G[1]}, {G[0]} {G[1]}" fill="none" stroke="#7a3fd0" stroke-width="5"/>'); dot(*IO0,'#7a3fd0'); dot(*G,'#7a3fd0')
a(f'<text x="{IO0[0]+50}" y="{IO0[1]+16}" font-size="13" fill="#7a3fd0" font-weight="bold">jumper IO0-GND (so para gravar)</text>')
px0,py0=760,300
a(f'<rect x="{px0}" y="{py0}" width="210" height="200" rx="8" fill="#b01e2a"/>')
a(f'<text x="{px0+105}" y="{py0+28}" font-size="16" fill="#fff" text-anchor="middle" font-weight="bold">adaptador PL2303</text>')
a(f'<rect x="{px0+210}" y="{py0+80}" width="70" height="40" fill="#bbb"/><text x="{px0+245}" y="{py0+105}" font-size="12" text-anchor="middle">USB Mac</text>')
pp={}
for i,n in enumerate(['3V3','TXD','RXD','GND','5V']):
  y=py0+55+i*30
  a(f'<circle cx="{px0+16}" cy="{y}" r="6" fill="#ddd"/><text x="{px0+30}" y="{y+5}" font-size="14" fill="#fff">{n}</text>'); pp[n]=(px0+16,y)
a(f'<text x="{px0+80}" y="{pp["3V3"][1]+5}" font-size="12" fill="#ffd">solto</text>')
path(f"M {pp['5V'][0]} {pp['5V'][1]} L 700 {pp['5V'][1]} L 700 650 L 60 650 L 60 {pl['5V'][1]} L {pl['5V'][0]} {pl['5V'][1]}","#d81e1e",pp['5V'],pl['5V'])
path(f"M {pp['GND'][0]} {pp['GND'][1]} L 720 {pp['GND'][1]} L 720 670 L 85 670 L 85 {pl['GND'][1]} L {pl['GND'][0]} {pl['GND'][1]}","#111",pp['GND'],pl['GND'])
path(f"M {U0R[0]} {U0R[1]} C 560 {U0R[1]}, 620 {pp['TXD'][1]}, {pp['TXD'][0]} {pp['TXD'][1]}","#2a9d3a",U0R,pp['TXD'])
path(f"M {U0T[0]} {U0T[1]} C 580 {U0T[1]}, 640 {pp['RXD'][1]}, {pp['RXD'][0]} {pp['RXD'][1]}","#e0b000",U0T,pp['RXD'])
a(f'<text x="560" y="{pp["TXD"][1]-12}" font-size="13" fill="#2a9d3a" font-weight="bold">U0R -> TXD</text>')
a(f'<text x="600" y="{U0T[1]+30}" font-size="13" fill="#a07a00" font-weight="bold">U0T -> RXD</text>')
a(f'<text x="430" y="640" font-size="13" fill="#d81e1e" font-weight="bold">5V do PL2303 -> 5V da CAM</text>')
a(f'<text x="430" y="700" font-size="13" fill="#111" font-weight="bold">GND do PL2303 -> GND da CAM (esquerda)</text>')
a('</svg>')
open('cam-gravacao-pl2303.svg','w').write('\n'.join(o))
