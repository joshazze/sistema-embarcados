W,H=1650,1260
o=[];a=o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">')
a(f'<rect width="{W}" height="{H}" fill="#fff"/>')
a('<text x="20" y="36" font-size="24" font-weight="bold" fill="#111">Protoboard completa: fonte YwRobot na ponta do 0 + buzzer + DY50</text>')
notes=["1) USB do Mega desconectado enquanto monta. Cada perna num furo proprio (rotulos vermelhos = coluna + letra).",
"2) Furos da mesma coluna (a ate e) ja sao ligados por dentro da protoboard.",
"3) Conferencia em ohms (desligado): coluna 18 ate trilha azul ~3k; coluna 21 ate trilha azul ~2k.",
"4) Cores dos fios do DY50 sao ilustracao: usem o mapa que voces fizeram. 3V3 do DY50 vai na trilha vermelha DE BAIXO (3,3 V da fonte).","5) As trilhas de cima sao CORTADAS no meio (perto da coluna 30): use so a metade esquerda (colunas 1 a 29).","6) Ordem: (a) fonte encaixada com chave desligada; (b) chave ligada: vermelha->azul de baixo = 003 e vermelha->azul de cima = 000; (c) chave ligada e depois USB do Mega."]
for i,t in enumerate(notes): a(f'<text x="20" y="{64+i*22}" font-size="15" fill="#111">{t}</text>')
bx,by,bw,bh=400,300,1120,460
a(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="#f3f1ea" stroke="#999"/>')
def cx(n): return bx+10+n*27
RM,RP=325,355
rows={'a':415,'b':440,'c':465,'d':490,'e':515}
a(f'<line x1="{bx+10}" y1="{RM-14}" x2="{bx+bw-10}" y2="{RM-14}" stroke="#1e5bd8" stroke-width="3"/>')
a(f'<line x1="{bx+10}" y1="{RP+14}" x2="{bx+bw-10}" y2="{RP+14}" stroke="#d81e1e" stroke-width="3"/>')
a(f'<text x="{cx(30)+30}" y="{RM-40}" font-size="14" fill="#1e5bd8" font-weight="bold">trilha azul (metade esquerda) = GND do Mega</text>')
a(f'<text x="{cx(30)+30}" y="{RM-22}" font-size="14" fill="#d81e1e" font-weight="bold">trilha vermelha (metade esquerda) = 5V do Mega</text>')
gx=(cx(29)+cx(31))/2
a(f'<rect x="{gx-8}" y="{RM-22}" width="16" height="{RP-RM+44}" fill="#f3f1ea"/>')
a(f'<text x="{gx}" y="{rows["e"]+60}" font-size="12" fill="#b00" text-anchor="middle" font-weight="bold">trilhas CORTADAS aqui</text>')
a(f'<text x="{gx+20}" y="{RP+34}" font-size="12" fill="#b00">metade direita: NAO usar</text>')
for n in range(1,41):
  for y in (RM,RP): a(f'<rect x="{cx(n)-3}" y="{y-3}" width="6" height="6" fill="#555"/>')
  a(f'<text x="{cx(n)}" y="{rows["a"]-14}" font-size="10" text-anchor="middle" fill="#444">{n}</text>')
  for r,y in rows.items(): a(f'<rect x="{cx(n)-3}" y="{y-3}" width="6" height="6" fill="#999"/>')
for r,y in rows.items(): a(f'<text x="{bx+6}" y="{y+4}" font-size="11" fill="#666">{r}</text>')
def dot(x,y,col): a(f'<circle cx="{x}" cy="{y}" r="5" fill="{col}" stroke="#fff"/>')
def wire(x1,y1,x2,y2,col,w=5):
  a(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'); dot(x1,y1,col); dot(x2,y2,col)
def path(d,col,p1,p2):
  a(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="5" stroke-linecap="round"/>'); dot(*p1,col); dot(*p2,col)
def res(x1,y1,x2,y2,label,bands):
  a(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#888" stroke-width="2"/>')
  mx,my=(x1+x2)/2,(y1+y2)/2
  a(f'<rect x="{mx-20}" y="{my-8}" width="40" height="16" rx="7" fill="#e7cf9a" stroke="#8a7"/>')
  for i,c in enumerate(bands): a(f'<rect x="{mx-12+i*8}" y="{my-8}" width="4" height="16" fill="{c}"/>')
  a(f'<text x="{mx}" y="{my-12}" font-size="12" text-anchor="middle" font-weight="bold">{label}</text>')
  for x,y in ((x1,y1),(x2,y2)): a(f'<circle cx="{x}" cy="{y}" r="3" fill="#666"/>')
def hole(t,n,r): a(f'<text x="{cx(n)+6}" y="{rows[r]+14}" font-size="10" fill="#b00">{t}</text>')
rows2={'f':560,'g':585,'h':610,'i':635,'j':660}
BM,BP=700,730
a(f'<rect x="{bx+10}" y="532" width="{bw-20}" height="12" fill="#ddd"/>')
for n in range(1,41):
  for y in rows2.values(): a(f'<rect x="{cx(n)-3}" y="{y-3}" width="6" height="6" fill="#bbb"/>')
  for y in (BM,BP): a(f'<rect x="{cx(n)-3}" y="{y-3}" width="6" height="6" fill="#555"/>')
for r,y in rows2.items(): a(f'<text x="{bx+6}" y="{y+4}" font-size="11" fill="#999">{r}</text>')
a(f'<line x1="{bx+10}" y1="{BM-14}" x2="{bx+bw-10}" y2="{BM-14}" stroke="#1e5bd8" stroke-width="3"/>')
a(f'<line x1="{bx+10}" y1="{BP+14}" x2="{bx+bw-10}" y2="{BP+14}" stroke="#d81e1e" stroke-width="3"/>')
a(f'<rect x="{gx-8}" y="{BM-22}" width="16" height="{BP-BM+44}" fill="#f3f1ea"/>')
a(f'<text x="{cx(8)}" y="{BM-18}" font-size="14" fill="#1e5bd8" font-weight="bold">azul de baixo (metade esquerda) = GND</text>')
a(f'<text x="{cx(8)}" y="{BP+34}" font-size="14" fill="#d81e1e" font-weight="bold">vermelha de baixo (metade esquerda) = 3,3 V da fonte</text>')
a(f'<text x="{cx(31)}" y="{BM-20}" font-size="13" fill="#999">metade direita de baixo: nao usar</text>')

a(f'<text x="{cx(5)}" y="620" font-size="13" fill="#999">fileiras f a j: nao usadas</text>')
K1=['#6b3e1e','#000','#d81e1e']; K10=['#6b3e1e','#000','#f28c00']; K330=['#f28c00','#f28c00','#6b3e1e']
# ---------- BUZZER ----------
C,B,E=cx(10),cx(11),cx(12); ye=rows['e']
a(f'<path d="M {C-12} {ye+8} L {E+12} {ye+8} L {E+12} {ye+18} A 26 20 0 0 1 {C-12} {ye+18} Z" fill="#222"/>')
for x,l in ((C,'C'),(B,'B'),(E,'E')):
  a(f'<line x1="{x}" y1="{ye}" x2="{x}" y2="{ye+8}" stroke="#aaa" stroke-width="3"/>')
  a(f'<text x="{x}" y="{ye+36}" font-size="11" font-weight="bold" text-anchor="middle" fill="#fff">{l}</text>')
a(f'<text x="{B}" y="{ye+62}" font-size="12" text-anchor="middle" fill="#111">BC546 (face escrita para voce)</text>')
for t,n in (('10e',10),('11e',11),('12e',12)): pass
res(B,rows['c'],cx(7),rows['c'],'10k',K10); hole('11c',11,'c'); hole('7c',7,'c')
wire(cx(7),rows['a'],cx(7),RM,'#111'); hole('7a',7,'a')
res(B,rows['b'],cx(15),rows['b'],'330',K330); hole('11b',11,'b'); hole('15b',15,'b')
wire(E,rows['a'],cx(13),RM,'#111'); hole('12a',12,'a')
bzx,bzy=cx(6),230
a(f'<circle cx="{bzx}" cy="{bzy}" r="26" fill="#111"/><circle cx="{bzx}" cy="{bzy}" r="4" fill="#444"/>')
a(f'<text x="{bzx-90}" y="{bzy-34}" font-size="13" font-weight="bold">buzzer ativo</text>')
a(f'<text x="{bzx-40}" y="{bzy+5}" font-size="15" fill="#d81e1e" font-weight="bold">+</text><text x="{bzx+32}" y="{bzy+5}" font-size="15" font-weight="bold">-</text>')
path(f"M {bzx-16} {bzy+20} Q {bzx-30} {RP-40} {cx(4)} {RP}","#d81e1e",(bzx-16,bzy+20),(cx(4),RP))
path(f"M {bzx+16} {bzy+20} Q {C+10} 300 {C} {rows['a']}","#777",(bzx+16,bzy+20),(C,rows['a'])); hole('10a',10,'a')
hole('15e',15,'e')
# ---------- DIVISOR DY50 ----------
c30,c33,c36,c39=cx(18),cx(21),cx(24),cx(27)
res(c30,rows['c'],c33,rows['c'],'1k',K1); hole('18c',18,'c'); hole('21c',21,'c')
res(c33,rows['b'],c36,rows['b'],'1k',K1); hole('21b',21,'b'); hole('24b',24,'b')
res(c36,rows['c'],c39,rows['c'],'1k',K1); hole('24c',24,'c'); hole('27c',27,'c')
wire(c39,rows['a'],c39,RM,'#111'); hole('27a',27,'a')
hole('18e',18,'e'); hole('21e',21,'e')
a(f'<rect x="{c30-14}" y="{rows["a"]-30}" width="{c39-c30+40}" height="{rows["e"]-rows["a"]+50}" fill="none" stroke="#e07b00" stroke-dasharray="6,4"/>')
a(f'<text x="{c30}" y="{rows["e"]+46}" font-size="13" fill="#e07b00" font-weight="bold">divisor do DY50 (D18 -> RX)</text>')
a(f'<rect x="{cx(6)-14}" y="{rows["a"]-30}" width="{cx(15)-cx(6)+40}" height="{rows["e"]-rows["a"]+50}" fill="none" stroke="#777" stroke-dasharray="6,4"/>')
# ---------- MB102 (ponta do 0) ----------
mx0=bx-38
a(f'<rect x="{mx0}" y="{RM-46}" width="76" height="{BP-RM+92}" rx="8" fill="#111" opacity="0.93"/>')
for i,t in enumerate(['fonte','Yw','Robot']): a(f'<text x="{mx0+38}" y="{(RM+BP)/2-20+i*20}" font-size="14" fill="#fff" text-anchor="middle" font-weight="bold">{t}</text>')
a(f'<text x="{mx0+38}" y="{(RM+BP)/2+50}" font-size="11" fill="#ccc" text-anchor="middle">DC-in 7 V</text>')
a(f'<rect x="{mx0+6}" y="{RM-40}" width="64" height="22" fill="#f2c200"/><text x="{mx0+38}" y="{RM-24}" font-size="14" text-anchor="middle" font-weight="bold">OFF</text>')
a(f'<rect x="{mx0+6}" y="{BP+18}" width="64" height="22" fill="#f2c200"/><text x="{mx0+38}" y="{BP+34}" font-size="14" text-anchor="middle" font-weight="bold">3.3</text>')
for y,c in ((RM,'#1e5bd8'),(RP,'#d81e1e'),(BM,'#1e5bd8'),(BP,'#d81e1e')): a(f'<circle cx="{mx0+60}" cy="{y}" r="6" fill="{c}" stroke="#fff"/>')
a(f'<text x="{mx0-120}" y="{RM-56}" font-size="13" fill="#b00" font-weight="bold">jumper de CIMA em OFF (obrigatorio)</text>')
a(f'<text x="{mx0-60}" y="{BP+62}" font-size="13" fill="#b00" font-weight="bold">jumper de BAIXO em 3.3</text>')
# ---------- MEGA ----------
a('<rect x="20" y="300" width="210" height="420" rx="8" fill="#1d4f91"/>')
a('<text x="115" y="700" font-size="17" fill="#fff" text-anchor="middle" font-weight="bold">Arduino Mega</text>')
pins={'GND':RM,'5V':RP,'D36':560,'D18 (TX1)':610,'D19 (RX1)':650}
for p,y in pins.items(): a(f'<rect x="190" y="{y-9}" width="40" height="18" fill="#000"/><text x="182" y="{y+5}" font-size="14" fill="#fff" text-anchor="end">{p}</text>')
path(f"M 230 {RM} C 250 {RM-70}, {cx(3)} {RM-60}, {cx(3)} {RM}",'#111',(230,RM),(cx(3),RM)); path(f"M 230 {RP} C 250 {RP-120}, {cx(4)+10} {RP-110}, {cx(4)+10} {RP}",'#d81e1e',(230,RP),(cx(4)+10,RP))
path(f"M 230 560 C 330 800, {cx(15)+40} 800, {cx(15)} {rows['e']}","#e0b000",(230,560),(cx(15),rows['e']))
a(f'<text x="{cx(15)+10}" y="790" font-size="13" fill="#a07a00" font-weight="bold">D36 (fio do buzzer)</text>')
path(f"M 230 610 C 500 840, {c30+40} 820, {c30} {rows['e']}","#2a9d3a",(230,610),(c30,rows['e']))
a(f'<text x="{c30-250}" y="850" font-size="13" fill="#2a9d3a" font-weight="bold">D18 em 18e</text>')
# ---------- DY50 ----------
dx,dy=1190,900
a(f'<rect x="{dx}" y="{dy}" width="340" height="200" rx="10" fill="#222"/>')
a(f'<text x="{dx+170}" y="{dy+30}" font-size="18" fill="#fff" text-anchor="middle" font-weight="bold">DY50 (cabo cortado)</text>')
px={}
for i,l in enumerate(['GND','RX','TX','3V3','T_OUT','T_3V3']):
  x=dx+30+i*56; y=dy+70
  a(f'<rect x="{x-6}" y="{y-6}" width="12" height="12" fill="#ccc"/><text x="{x}" y="{y+26}" font-size="12" fill="#fff" text-anchor="middle">{l}</text>'); px[l]=(x,y)
a(f'<text x="{dx+170}" y="{dy+130}" font-size="13" fill="#ffcc66" text-anchor="middle">3V3 na trilha vermelha de baixo (3,3 V)</text>')
a(f'<text x="{dx+170}" y="{dy+155}" font-size="13" fill="#ffcc66" text-anchor="middle">T_OUT e T_3V3: isolados com fita</text>')
a(f'<text x="{dx+170}" y="{dy+180}" font-size="13" fill="#ff8080" text-anchor="middle">nunca ligar o 3V3 no 5V</text>')
g=px['GND']; path(f"M {g[0]} {g[1]} C {g[0]} 800, {cx(29)} 820, {cx(29)} 780 L {cx(29)} {RM}","#111",g,(cx(29),RM))
r=px['RX']; path(f"M {r[0]} {r[1]} C {r[0]} 820, {c33+30} 800, {c33} {rows['e']}","#e07b00",r,(c33,rows['e']))
a(f'<text x="{c33+12}" y="880" font-size="13" fill="#e07b00" font-weight="bold">RX do DY50 em 21e</text>')
v=px['3V3']; path(f"M {v[0]} {v[1]} C {v[0]} 1080, {cx(6)} 1000, {cx(6)} {BP}","#e05d9b",v,(cx(6),BP))
a(f'<text x="{cx(6)+14}" y="800" font-size="13" fill="#e05d9b" font-weight="bold">3V3 do DY50 na vermelha de baixo</text>')
t=px['TX']; path(f"M {t[0]} {t[1]} C {t[0]} 1250, 400 1230, 230 650","#7a3fd0",t,(230,650))
a('<text x="420" y="1190" font-size="14" fill="#7a3fd0" font-weight="bold">TX do DY50 direto no D19</text>')
a('</svg>')
open('protoboard-completa.svg','w').write('\n'.join(o))
