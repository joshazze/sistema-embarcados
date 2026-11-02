# Lista de materiais

## Materiais para a arquitetura Mega + ESP32-CAM

| Quantidade | Material | Conferir antes de ligar |
|---|---|---|
| 1 | Arduino Mega 2560 e cabo USB de dados | Placa e cabo compatíveis |
| 1 | ESP32-CAM Ai-Thinker com câmera | Variante e identificação dos pinos reais |
| 1 | Adaptador USB-serial PL2303 (pinos 3V3, TXD, RXD, GND, 5V) | Do dono, desde 31/10/2026. TX em nível de 3,3 V (medido). Gravação pelos fios da MONTAGEM seção 4. Substitui a base ESP32-CAM-MB |
| 1 | Leitor de digital DY50 com cabo | Pinagem, alimentação, níveis lógicos e UART da unidade real |
| 1 | Teclado matricial 4×4 | Identificar a ordem das linhas e colunas |
| 1 | LCD 16×2 com interface I²C | Presença do backpack e endereço; exemplo usa `0x27` |
| 1 | LED ou módulo RGB | Tipo de comum, pinagem e resistores já existentes |
| 2 | Botões ou sensores de contato | Contatos fechados quando a porta está fechada |
| 1 | Buzzer ativo 5 V, até 50 mA | Identificar polaridade e tipo; acionar com transistor |
| 1 | Transistor NPN compatível, resistor de base de 330 Ω a 1 kΩ (470 Ω nominal; a bancada usou 330 Ω) e resistor de 10 kΩ | Conferir pinagem; resistor de base e pull-down para o buzzer |
| Até 3 | Resistores para os canais RGB | Usar somente se o módulo não tiver resistores adequados; dimensionar ao LED |
| 1 + 1 | Resistor de 1 kΩ e resistor de 2 kΩ (ou três de 1 kΩ) | Divisor de tensão D16 -> GPIO13 (MONTAGEM seção 3.3). Substitui o conversor de nível (decisão do dono, 31/10/2026); na prática, com os 330 Ω em série (HANDOFF seção 7), pois só sobra um 1 kΩ |
| Conforme DY50 | Segundo divisor (1 kΩ e 2 kΩ) para o RX do DY50 | Montado em 02/11/2026 com três 1 kΩ (MONTAGEM 3.9) |
| 1 | Regulador step-down LM2596 (com display) ajustado em 5,0 V, alimentado pela bateria de 12 V | Alimenta a CAM. Ajustar sem carga antes de ligar. Comprado em 2 unidades (uma de reserva) |
| 1 | Fechadura 12 V / 2 A e bateria 12 V 5200 mAh | Confirmar regime da bobina e forma de retravamento antes de energizar. Bateria: descarga contínua de 3 A ou mais e carregador |
| 1 | Driver de potência para a fechadura e proteção indutiva | Entrada compatível com Mega 5 V e carga DC de 12 V / 2 A com margem |
| Conforme montagem | Cabos, conectores e protoboard para sinais | Usar fios e conexões dimensionados para a corrente da fechadura; não conduzir 2 A pela protoboard |

A versão anterior com ESP32 DevKit foi descontinuada.

## Situação do material do dono (31/10/2026)

Inventário pela foto do dono em 31/10/2026 (identificação visual; valores não medidos).

| Situação | Itens |
|---|---|
| Tem | Mega 2560 com cabo USB; ESP32-CAM com câmera; adaptador USB-serial PL2303 (desde 31/10/2026); leitor de digital (DY50 ou equivalente) com cabo emendado por conector e jumpers (02/11/2026; alimentado pela MB102 e comunicando); teclado 4x4 de teclas rígidas (barra de 8 pinos soldada em 02/11/2026); LCD 1602 (sem módulo I2C); buzzer solto de 2 pernas (ativo, em uso); módulo de buzzer de 3 pinos `S V G` (passivo, descartado em 02/11/2026); 2 botões de painel; módulo relé 5 V (candidato a driver da fechadura); 2 módulos de fonte de protoboard (YwRobot MB102 em uso desde 02/11/2026); fonte de parede de 7 V (em uso, plugue P4 na MB102); adaptador 5 V 1 A F05W-050100SPAE (disponível, não usado); conectores de alavanca; saquinho com LEDs e resistores; fechadura 12 V (guardada fora da bancada); jumpers; protoboard; alicate amperímetro; ferro de solda e barra de pinos |
| Comprando | Bateria 12 V 5200 mAh; 2 step-down LM2596 com display |
| Falta comprar | Módulo I2C PCF8574 para o LCD; carregador da bateria (se não vier junto); módulo LED RGB `R G B GND` (ausente em 02/11/2026: a peça não está com o dono). A base ESP32-CAM-MB não é mais necessária |
| Conferir na bancada | Resistores (medidos com o alicate em 02/11/2026, ver abaixo): 4 de 1 kΩ, uma tira de 10 kΩ (quantidade não contada) e vários de 330 Ω; diodo 1N4007 (se o relé não tiver diodo); buzzer resolvido em 02/11/2026 (de 2 pernas, ativo, com BC546; módulo S V G descartado, ver abaixo); se o módulo LED RGB tem resistores; entrada e diodo do módulo relé |
| Não usados | Sensor DHT11, RTC DS1302, Bluetooth HC-05/06, servo SG90, outro Arduino |

Atualização de 02/11/2026 (sessão 4):

- LED RGB `R G B GND`: ausente em 02/11/2026; a peça não está com o dono. O firmware funciona sem ele.
- Módulo de buzzer `S V G` (3 pinos): é passivo (inferência) e não serve com o firmware atual. Descartado.
- Buzzer solto de 2 pernas: é ativo (verificado em hardware). Está em uso, no circuito com BC546 e resistor de 330 Ω na base.
- Transistor: BC546 (NPN) em uso. O BC327-25 encontrado é PNP e não serve.
- Resistores conferidos com o alicate: 4 de 1 kΩ; uma tira de 10 kΩ (quantidade não contada); vários de 330 Ω.
- DY50: cabo emendado por conector e jumpers (02/11/2026); alimentado pela MB102 e comunicando (`dy50=ok`) (ver `docs/MONTAGEM.md`, 3.9, e `docs/HANDOFF.md`, seção 4, continuação).
- Teclado 4x4: barra de 8 pinos soldada e lida pelo Mega (02/11/2026), com a coluna C4 verificada no mesmo dia. Ver `docs/VALIDACAO.md`.
- Fonte de protoboard YwRobot MB102 (reguladores AMS1117 de 3,3 V e 5 V; jumper por lado 3.3 / OFF / 5V; entrada P4 6,5 a 12 V ou USB-A): em uso desde 02/11/2026, alimentada por fonte de parede de 7 V no plugue P4 (saída 3,3 V medida). Ligação em `docs/MONTAGEM.md`, 3.9.
- Módulo Hi-Link HLK-PM12 (entrada 100 a 240 V AC, saída 12 V 0,25 A): não usar na bancada (recusado por segurança: lado da tomada com fios e emendas expostos em caixa aberta).
- Módulo Bluetooth HC-05/ZS-040 e módulo RTC com suporte de bateria de botão: não servem (não usar).
- Fonte de parede de 7 V (valor informado pelo dono; etiqueta não fotografada): em uso, com plugue P4 na MB102 (02/11/2026). Conferir a etiqueta.
- Adaptador 5 V 1 A (F05W-050100SPAE): apareceu em 02/11/2026; disponível, não usado.
- Resistores de 1 kΩ: três no divisor do DY50 (02/11/2026); sobra um. Divisor nas colunas 18 a 27 da protoboard (`docs/MONTAGEM.md`, 3.9).

## Ferramentas e itens de apoio (aprovados pelo dono em 30/10/2026)

| Quantidade | Material | Uso |
|---|---|---|
| 1 | Multímetro | Medições de tensão do roteiro |
| 2 | Jumpers para D30 e D31 a GND na bancada | Acionamento de teste das entradas na bancada |
| 1 | Resistor de 10 kΩ adicional | Pull-down da entrada do driver da fechadura (D35) |
| 1 | Resistor de 220 Ω a 1 kΩ | Teste da entrada do driver sem firmware (seção 6 do MONTAGEM) |
| 1 | Computador com Python 3.9+ na mesma rede | Servidor e testes |
| 1 | Rede Wi-Fi de 2,4 GHz | Conexão do servidor e da ESP32-CAM |
