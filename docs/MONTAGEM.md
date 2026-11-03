# Guia de montagem: Arduino Mega 2560 + ESP32-CAM

Este guia liga o Mega (controlador) à ESP32-CAM (rede e foto). A versão com
ESP32 DevKit foi descontinuada e não faz parte da entrega.

Status: montagem para bancada. Em hardware foram verificados o passo 3 (30/10/2026); em 02/11/2026, o teclado 4x4 lido pelo Mega, o circuito do buzzer, o DY50 alimentado pela MB102 e comunicando (seção 3.9), o cadastro, os acessos pela digital e pela senha e o buzzer pelo firmware. O restante (LED RGB, LCD, CAM e fechadura) ainda não foi testado em hardware. Detalhes em [VALIDACAO.md](VALIDACAO.md). Os pinos abaixo
foram conferidos no código (`firmware/MegaControlador/Config.example.h`,
`firmware/MegaControlador/MegaControlador.ino` e `firmware/Esp32CamRede/Esp32CamRede.ino`).
Valores de ficha de componente aparecem como "conferir na ficha", porque não
foram medidos.

Lista de materiais: [MATERIAIS.md](MATERIAIS.md).

---

## 1. Avisos de segurança

Leia antes de energizar qualquer coisa.

- [ ] 12 V nunca vai para pino de lógica, 3V3, 5V ou GPIO. Só para a fechadura, pela fonte 12 V.
- [ ] A corrente da fechadura (2 A) não passa pela protoboard nem pela trilha da placa. Use fio e bornes dimensionados.
- [ ] TX de 5 V do Mega nunca vai direto ao GPIO13 da CAM. Sempre pelo divisor de tensão da seção 3.3 (1 kΩ em série e 2 kΩ ao GND).
- [ ] Primeira bancada: `LOCK_MODE=0` no `Config.h` do Mega e fechadura desconectada.
- [ ] Desligue tudo antes de ligar ou mexer em fios.
- [ ] Não ligue a fonte 5 V externa ao 5V do Mega enquanto o USB estiver conectado.
- [ ] Não ligue nada em GPIO12 da CAM.
- [ ] Com a fonte 12 V ligada e a fechadura conectada ao driver, não reinicie nem regrave o Mega: não feche/reabra o monitor serial, não pressione RESET, não mexa no cabo USB. Durante qualquer reinício o D35 flutua por 1 a 2 s. Antes de reiniciar, desligue os 12 V (ou solte um fio da fechadura).

---

## 2. Tabela-resumo de pinos

### Arduino Mega 2560

| Pino | Sinal | Liga em | Observação |
|---|---|---|---|
| D16 | TX2 (link com a CAM) | Resistor de 1 kΩ do divisor (seção 3.3) | Sinal 5 V; nunca direto ao GPIO13 |
| D17 | RX2 (link com a CAM) | GPIO14 da CAM, direto | Recebe 3,3 V da CAM |
| D18 | TX1 (DY50) | RX do DY50, pelo 1 kΩ (seção 3.9) | Serigrafia do clone diz RX1; medido: TX1 |
| D19 | RX1 (DY50) | TX do DY50, direto | Serigrafia do clone diz TX1; medido: RX1 |
| D20 | Livre | Não ligar | Livre (o LCD usa 4 bits, sem I²C) |
| D21 | Livre | Não ligar | Livre (o LCD usa 4 bits, sem I²C) |
| D22 a D25 | Linhas R1 a R4 | Teclado | Entradas com pull-up (o Mega lê) |
| D26 a D29 | Colunas C1 a C4 | Teclado | Saídas (o Mega aciona) |
| D30 | Botão 1 da porta | Contato para GND | Pull-up interno |
| D31 | Botão 2 da porta | Contato para GND | Pull-up interno |
| D32 | LED RGB, vermelho | Resistor do canal | |
| D33 | LED RGB, verde | Resistor do canal | |
| D34 | LED RGB, azul | Resistor do canal | |
| D35 | Entrada do driver da fechadura | Driver (IN) + pull-down 10 kΩ | Ver seção 3.10 |
| D36 | Buzzer | Base do NPN, por 470 Ω (ou 330 Ω a 1 kΩ) | Ver seção 3.8 |
| D37 | RS do LCD | Pino 4 (RS) do LCD 1602 | Ver seção 3.5 |
| D38 | E do LCD | Pino 6 (E) do LCD 1602 | Ver seção 3.5 |
| D39 | D4 do LCD | Pino 11 (D4) do LCD 1602 | Ver seção 3.5 |
| D40 | D5 do LCD | Pino 12 (D5) do LCD 1602 | Ver seção 3.5 |
| D41 | D6 do LCD | Pino 13 (D6) do LCD 1602 | Ver seção 3.5 |
| D42 | D7 do LCD | Pino 14 (D7) do LCD 1602 | Ver seção 3.5 |
| D0 e D1 | USB | Não usar | Ligados ao USB do Mega |

### ESP32-CAM (Ai-Thinker)

| Pino | Sinal | Liga em | Observação |
|---|---|---|---|
| 5V | Alimentação | Saída do step-down ajustada em 5,0 V (seção 3.1) | Não usar o 3V3 para alimentar |
| GND | Comum | GND comum | Ver seção 3.1 |
| 3V3 | Saída de 3,3 V | Nada | Só para medir |
| GPIO13 | RX do link | Ponto do meio do divisor (seção 3.3) | Sinal 3,3 V |
| GPIO14 | TX do link | D17 do Mega, direto | Sinal 3,3 V |
| U0R (GPIO3) | RX da programação | TX do adaptador USB-serial | Só para gravar |
| U0T (GPIO1) | TX da programação | RX do adaptador USB-serial | Só para gravar |
| GPIO0 | Modo de gravação | GND, só durante o reset de gravação | Também é o clock da câmera no firmware |

Não ligue nada em GPIO12, no LED de flash (GPIO4) nem nos demais pinos usados
pela câmera. A ESP32-CAM não usa cartão microSD.

---

## 3. Passo a passo por componente

Faça um componente por vez, com tudo desligado. Depois de cada etapa, confira
continuidade e tensões antes de seguir.

### 3.1 Alimentação

Topologia de bancada:

- Mega: alimentado pelo USB do computador.
- ESP32-CAM: alimentada por um regulador step-down (LM2596) ajustado em 5,0 V,
  ligado à bateria de 12 V (a mesma da fechadura), no pino 5V da placa.
- Entre o lado do Mega e o lado da CAM: **somente os GNDs** são unidos.
- Não há ligação de 5 V entre o Mega e a CAM.

Fios:

| De | Para |
|---|---|
| Bateria 12 V, (+) | Entrada (+) do step-down |
| Bateria 12 V, (-) | Entrada (-) do step-down, direto no borne da bateria |
| Step-down, saída (+) | 5V da ESP32-CAM |
| Step-down, saída (-) | GND da ESP32-CAM |
| GND do Mega | GND da ESP32-CAM (ponto comum) |
| GND do Mega | GND do divisor (resistor de 2 kΩ) |

Observações:

- A fonte da CAM precisa de corrente para picos de câmera e Wi-Fi. O valor
  exato deve ser conferido na ficha da fonte e da placa.
- Alguns clones tratam o pino marcado VCC como saída, não como entrada. Antes
  de alimentar, confira na placa real.
- O USB do Mega e a fonte da CAM são fontes separadas. Não as ligue ao mesmo
  barramento de 5 V.

Antes de energizar:

- [ ] Ajuste o step-down para 5,0 V sem carga (display do módulo e multímetro)
      antes de conectá-lo à CAM. Saída acima de 5,2 V pode danificar a CAM.
- [ ] O negativo do step-down vai direto ao borne da bateria, não pelo caminho
      da corrente da fechadura.
- [ ] Com multímetro em continuidade, confirme que todos os GNDs estão ligados
      (Mega, CAM, divisor e, depois, o adaptador da seção 4).
- [ ] Nenhum fio de 12 V está próximo dos pinos de lógica.

### 3.2 ESP32-CAM

Fios:

| De | Para |
|---|---|
| Step-down, saída (+) (5,0 V) | 5V da CAM |
| GND da CAM | GND comum |
| GPIO13 da CAM | Ponto do meio do divisor (seção 3.3) |
| GPIO14 da CAM | D17 do Mega, direto |

Observações:

- Os pinos da câmera são definidos no firmware (função `startCamera()` em
  `Esp32CamRede.ino`). Não ligue nada neles.
- GPIO0 é usado como clock da câmera. Deixe-o livre, exceto durante a gravação
  (seção 4). Se ficar em GND ao ligar, a placa entra em modo de gravação.
- O pino 3V3 da placa não alimenta nada neste projeto.
- O Wi-Fi da CAM é 2,4 GHz. Uma rede que só tem 5 GHz não conecta.

Antes de energizar:

- [ ] Continuidade confirmada entre GND da CAM e GND comum.
- [ ] Nenhum GPIO da CAM está ligado a 5 V.
- [ ] GPIO0 sem ligação para GND.
- [ ] Flat da câmera encaixado com a CAM desligada.

### 3.3 Divisor de tensão (Mega <-> CAM)

Decisão do dono (31/10/2026): o conversor de nível foi trocado por um divisor
de tensão com resistores. Só o sentido Mega -> CAM precisa baixar a tensão.

Mega envia (D16, 5 V) -> CAM recebe (GPIO13, 3,3 V):

| De | Para |
|---|---|
| D16 do Mega | Um terminal do resistor de 1 kΩ |
| Outro terminal do 1 kΩ | Ponto do meio (uma fileira da protoboard) |
| Ponto do meio | Um terminal do resistor de 2 kΩ (ou dois de 1 kΩ em série) |
| Outro terminal do 2 kΩ | GND comum |
| Ponto do meio | GPIO13 da CAM |

CAM envia (GPIO14, 3,3 V) -> Mega recebe (D17):

| De | Para |
|---|---|
| GPIO14 da CAM | D17 do Mega, fio direto |

Observações:

- Com 5 V no D16, o ponto do meio fica em cerca de 3,3 V (5 V x 2 / 3).
- O resistor de 2 kΩ precisa estar no GND. Sem ele, o GPIO13 recebe 5 V.
- O nível alto mínimo do Mega é 3,0 V (0,6 x 5 V). Os 3,3 V da CAM ficam acima,
  com pouca folga. Costuma funcionar; se o passo 6 falhar, este é o primeiro
  suspeito.
- Não use o 3V3 da CAM para nada neste projeto.
- Alternativa com resistores de 330 Ω, porque o dono só tem 4 de 1 kΩ: 3 em série (~1 kΩ) no lugar do 1 kΩ e 6 em série (~2 kΩ) no lugar do 2 kΩ (mesma proporção).

Antes de energizar:

- [ ] Resistores conferidos (código de cores ou multímetro): 1 kΩ e 2 kΩ.
- [ ] Ponto do meio medido perto de 3,3 V com o Mega ligado e a CAM ainda solta
      (passo 4 da seção 5).

### 3.4 Teclado 4x4

Fios:

| De (teclado) | Para (Mega) |
|---|---|
| R1 | D22 |
| R2 | D23 |
| R3 | D24 |
| R4 | D25 |
| C1 | D26 |
| C2 | D27 |
| C3 | D28 |
| C4 | D29 |

Observações:

- A ordem dos pinos varia por fabricante. Antes de ligar, use multímetro em
  continuidade: cada tecla fecha uma linha com uma coluna.
- Pelo mapa do código, as teclas da linha R1 são `1 2 3 A`, da R2 `4 5 6 B`, da R3
  `7 8 9 C` e da R4 `* 0 # D`. A coluna C1 tem `1 4 7 *`, a C2 tem `2 5 8 0`, a C3
  tem `3 6 9 #` e a C4 tem `A B C D`.
- Não há VCC nem GND separados no teclado.
- Não troque linhas por colunas no código. A biblioteca Keypad lê R1 a R4 (entradas
  com pull-up) e aciona C1 a C4 (saídas, uma de cada vez).

Antes de energizar:

- [ ] Continuidade confirmada para cada tecla, sem curto entre pinos vizinhos.

### 3.5 LCD 1602 (modo 4 bits)

Ligue o LCD direto ao Mega, sem módulo adaptador. Depois de ligar, o LCD mostra "Iniciando..." (ver seção 5).

Fios (pino do LCD 1602 -> Mega):

| Pino do LCD | Nome | Liga em |
|---|---|---|
| 1 | VSS | GND |
| 2 | VDD | 5V |
| 3 | V0 | Pino do meio de um potenciômetro de 10 kΩ (pontas em 5V e GND), ou resistor de 1 kΩ a 2,2 kΩ para o GND |
| 4 | RS | D37 |
| 5 | RW | GND |
| 6 | E | D38 |
| 7 a 10 | D0 a D3 | Nada (não ligar) |
| 11 | D4 | D39 |
| 12 | D5 | D40 |
| 13 | D6 | D41 |
| 14 | D7 | D42 |
| 15 | A (luz de fundo +) | 5V por resistor de 220 Ω |
| 16 | K (luz de fundo -) | GND |

Observações:

- Os pinos mudam definindo `LCD_PIN_RS`, `LCD_PIN_E` e `LCD_PIN_D4` a `LCD_PIN_D7` no `Config.h`, com `#define LCD_PIN_RS 43` etc. antes do fim do `Config.h` (use `#define`, não `constexpr`).
- Usa a biblioteca LiquidCrystal (vem com a Arduino IDE).
- O firmware não detecta LCD ausente: o STATUS e o BOOT não têm o campo `lcd=`.
- O espelho `LCD| ...` na serial continua funcionando.
- O LCD precisa de barra de pinos soldada.
- Ajuste o contraste (potenciômetro ligado ao pino 3) até ver os caracteres. Sem contraste, a tela fica vazia ou só com blocos.
- Alguns LCD 1602 já têm resistor da luz de fundo na placa; confira antes. Se tiver, o de 220 Ω pode ficar ou sair.

Antes de energizar:

- [ ] Pinos 1 e 16 identificados na ficha do LCD. Pino 1 (VSS) vai ao GND e pino 2 (VDD) ao 5V; não inverter.
- [ ] Continuidade confirmada na solda, sem curto entre pinos vizinhos.
- [ ] Resistor da luz de fundo (220 Ω) ligado ao pino 15.
- [ ] Pino 5 (RW) ao GND e pino 3 (V0) no potenciômetro ou resistor (solto, a tela fica vazia ou com lixo).

### 3.6 Botões da porta (contatos)

Fios, para cada botão:

| De | Para |
|---|---|
| Botão 1 (contato) | D30 |
| Botão 1 (outro terminal) | GND |
| Botão 2 (contato) | D31 |
| Botão 2 (outro terminal) | GND |

Observações:

- Os dois pinos usam pull-up interno (`INPUT_PULLUP`). Não precisam de resistor externo.
- Porta fechada: os dois contatos fecham para GND. O Mega lê LOW nos dois pinos.
- Porta aberta: pelo menos um contato abre e o Mega lê HIGH.
- Sem jumper ou contato em D30 e D31, o Mega lê HIGH e inicia em alarme (`forced_open` no boot).
- Na bancada, sem a porta, use dois jumpers de D30 e D31 para GND para simular
  porta fechada.
- Os botões não autorizam nem comandam a abertura. São só sensores.

Antes de energizar:

- [ ] Com os contatos abertos, D30 e D31 devem estar em HIGH no multímetro, depois de ligar.

### 3.7 LED RGB

Fios:

| De (LED) | Para |
|---|---|
| R (canal vermelho) | Resistor do canal, depois D32 |
| G (canal verde) | Resistor do canal, depois D33 |
| B (canal azul) | Resistor do canal, depois D34 |
| Comum | GND (cátodo comum) ou 5V (ânodo comum) |

Observações:

- Um resistor por canal. Se o módulo já tiver resistores adequados, não precisa
  de outros. Dimensione o valor pela ficha do LED, conferindo a corrente por canal.
- Cátodo comum: comum no GND e `RGB_COMMON_ANODE = false`.
- Ânodo comum: comum no 5V e `RGB_COMMON_ANODE = true`. Confirme na ficha se a
  corrente do pino do Mega fica dentro do limite.
- A cor é digital, ligado ou desligado, sem PWM. Amarelo é vermelho e verde juntos.
- Se o módulo consumir mais corrente do que a ficha permite para o pino, use
  transistor de acionamento. Não é item da lista atual.

Antes de energizar:

- [ ] Identifique o comum e os canais R, G e B pela ficha do módulo ou por
      continuidade com o multímetro.
- [ ] Confirme que `RGB_COMMON_ANODE` no `Config.h` bate com o tipo do módulo.

### 3.8 Buzzer com transistor NPN

Fios:

| De | Para |
|---|---|
| Buzzer (+) | 5V do Mega |
| Buzzer (-) | Coletor do NPN |
| Emissor do NPN | GND |
| Base do NPN | Um terminal do resistor de 470 Ω (ou 330 Ω a 1 kΩ) |
| Outro terminal do resistor de 470 Ω (ou 330 Ω a 1 kΩ) | D36 |
| Base do NPN | Um terminal do resistor de 10 kΩ |
| Outro terminal do resistor de 10 kΩ | GND (junto do emissor) |

Observações:

- Use buzzer ativo de 5 V, com corrente de até 50 mA.
- A pinagem do NPN (base, coletor, emissor) muda por modelo. Confira na ficha
  do transistor usado, não pela forma do encapsulamento.
- O resistor de 10 kΩ entre base e emissor mantém o transistor desligado
  enquanto o pino do Mega estiver indefinido.
- Se o buzzer tiver circuito integrado próprio, confirme na ficha se aceita sinal de 5 V
  e se o disparo é ativo em HIGH. Faça essa conferência também se trocar o buzzer por outro modelo.
- Resistor de base de 330 Ω a 1 kΩ também serve. A bancada usou 330 Ω no lugar do 470 Ω (corrente no D36 de cerca de 13 mA, em 02/11/2026).
- Módulo de buzzer passivo de 3 pinos (como o módulo SainSmart `S V G` testado em 02/11/2026, que ficou em silêncio com nível fixo) não serve com o firmware atual, que só liga e desliga o D36. Um buzzer de 2 pernas ligado direto a 5 V e GND apitou contínuo: é ativo.
- Teste rápido do circuito sem firmware: com o fio de teste ligado ao 5 V (no lugar do D36), o buzzer deve apitar. No GND, deve ficar em silêncio (não testado separadamente).
- NPN que servem (conferir a pinagem na ficha): BC337, BC546 a BC550, 2N2222, 2N3904, S8050, C945, C1815. Só o BC546 foi testado na bancada.
- PNP não servem (com PNP no lado alto a lógica inverte e o buzzer apitaria em repouso): BC327, BC557, 2N3906, S8550.
- Avisos do firmware: três bipes curtos ao expirar o minuto sem abrir. Um bipe
  a cada 2 s após 5 minutos de porta aberta. Porta aberta sem autorização (forçada, ou
  já aberta no boot): bipe de 250 ms ligado e 250 ms desligado até fechar a porta
  (`outputsTick` em `MegaControlador.ino`). Ver `BuzzerLogic.h`.
- Com `LOCK_MODE=0`, o buzzer funciona normalmente. Só a fechadura fica desligada.

Antes de energizar:

- [ ] Continuidade entre emissor do NPN e GND.
- [ ] Nenhum fio de 5 V ligado diretamente à base.

### 3.9 DY50 (leitor de digital)

Fios (confira a ordem dos pinos na ficha da sua unidade antes de ligar):

| De (Mega) | Para (DY50) |
|---|---|
| D18 (TX1) | 1 kΩ, depois RX do DY50 (o RX tem dois 1 kΩ em série para GND) |
| D19 (RX1) | TX do DY50, direto |
| 3,3 V da fonte de protoboard MB102 (trilha vermelha de baixo; fonte de parede de 7 V) | 3V3 do DY50 (nunca 5 V nesta unidade) |
| GND (trilha azul de cima, comum com o Mega) | GND do DY50 |

Observações:

- Ligue o DY50 só depois de concluir o roteiro de comunicação da seção 5 (passo 7) (regra original; adiantada em 02/11/2026, ver a decisão abaixo).
- Decisão de 02/11/2026: a ligação do DY50 foi adiantada, porque a CAM aguarda bateria e step-down e a ligação do DY50 não depende da CAM (ver `docs/HANDOFF.md`, seção 4).
- Montagem usada em 02/11/2026 (verificada em hardware: `dy50=ok`): fonte de parede de 7 V (valor informado pelo dono; etiqueta não fotografada) com plugue P4 no DC-in da fonte de protoboard YwRobot MB102. A MB102 fica na ponta do lado do Mega; a saída de 3,3 V (trilha vermelha de baixo) alimenta o 3V3 do DY50. O GND da MB102 encosta na trilha azul de cima, comum com o Mega. Saída medida: 3,3 V (`003` no alicate, medição grosseira).
- Cuidado com o jumper do lado das trilhas de cima da MB102: elas levam 5 V e GND do Mega. Esse jumper fica em OFF, não em 3.3. Em 02/11/2026 ele ficou em 3.3 por engano e foi corrigido. Antes de ligar a USB, medir: trilha de cima `000`, trilha de baixo `003`. O Mega segue alimentado só pela USB; nunca ligar o 5V do Mega na trilha de 3,3 V.
- Protoboard: as trilhas de cima são cortadas no meio, perto da coluna 30. Usar só a metade esquerda.
- Divisor do RX montado em 02/11/2026 (medido desligado): 1 kΩ entre as colunas 18 e 21 (D18 na coluna 18, RX do DY50 na coluna 21); 1 kΩ entre 21 e 24; 1 kΩ entre 24 e 27; jumper da coluna 27 à trilha azul de cima. Coluna 18 até GND = 3 kΩ; coluna 21 até GND = 2 kΩ. O cabo do DY50 foi emendado por conector branco a fios coloridos e jumpers.
- Serigrafia deste clone trocada: a placa diz `RX1 18` e `TX1 19`. Medido com o firmware rodando e pinos livres: pino 18 = TX1 (repouso alto, `005`) e pino 19 = RX1 (`000`). Seguir os números, como no ATmega2560.
- Não tire a alimentação do DY50 do 5V do Mega com o Mega alimentado só pelo USB
  antes de conferir o consumo do DY50 na ficha. Se a ficha ou a corrente disponível
  no USB não bastarem, use fonte separada com GND comum.
- Não deduza a ordem dos pinos pela cor ou pela imagem genérica. Cada fio pode
  estar invertido.
- A faixa de alimentação diverge entre a página do produto e tutoriais
  (3 V a 6 V ou 3,6 V a 6 V). Confirme na ficha da sua unidade.
- Alimentar o DY50 com 5 V não prova que o TX dele é de 5 V. O TX pode ser
  de 3,3 V. Meça ou confirme na ficha antes de ligar.
- O UART do DY50 é 57600 bps (`Serial1` no firmware).
- O RX do DY50 não deve receber os 5 V do D18 sem confirmação na ficha da unidade.
  Se o DY50 for 3,3 V, use um segundo divisor (1 kΩ e 2 kΩ) no D18, como na seção 3.3.
- Se o nível for incompatível, use conversão de nível para UART. Itens sem uso
  ficam isolados.
- Mensagens esperadas: "Falha memoria" bloqueia. "DY50 fora do ar" aparece
  no LCD se o leitor não responder no boot. Durante o cadastro, um modelo no leitor
  sem registro válido (ID 1 a 100, memória OK) é apagado no primeiro dedo: LCD
  "Slot orfao limpo" / "Recoloque o dedo"; recoloque o dedo. "Slot DY orfao" só
  aparece se o apagamento falhar, o ID estiver fora da faixa ou o registro
  estiver corrompido; o cadastro para. Não apague a base de digitais.
- Unidade do dono (rótulos lidos na placa em 02/11/2026): 6 pinos `GND`, `RX`, `TX`, `3V3`, `T_OUT` e `T_3V3`. Pela marcação 3V3, alimentar com 3,3 V e não com 5 V (inferência pela marcação; a ficha não foi conferida). `T_OUT` e `T_3V3` ficam isolados, sem uso.
- Cabo com 6 fios vermelhos e conector de passo ~1 mm (JST SH/1.25), que não encaixa em jumper. Corte o conector da ponta solta, identifique cada fio por continuidade contra os rótulos da placa e solde jumpers: GND preto; 3V3 em cor exclusiva (não vermelha), marcada; TX e RX em cores distintas. Emenda feita em 02/11/2026: conector branco a fios coloridos e jumpers.
- Ponto em aberto: a especificação oficial do Mega 2560 cita 50 mA para o pino 3.3V; o DY50 pede menos de 120 mA (pico menos de 140 mA). Não usar o pino 3.3V do Mega para o DY50; usar fonte de 3,3 V separada com GND comum (usada: MB102, ver acima; `docs/HANDOFF.md`, seção 4, continuação).
- Divisor do RX (ligação montada em 02/11/2026, ver acima): D18 -> 1 kΩ -> RX do DY50; RX do DY50 -> dois de 1 kΩ em série -> GND. Procedimento antes de ligar TX e RX (em 02/11/2026 este passo foi pulado: a medição do TX do DY50 não foi executada, e o DY50 foi ligado mesmo assim): alimente só 3V3 e GND e meça o TX: esperado `002` ou `003` no alicate, que lê cerca de 1 V abaixo. Pare se der `004` ou mais.

Antes de energizar:

- [ ] Ficha da unidade lida: VCC, GND, TX, RX e faixa de tensão confirmados.
- [ ] TX do DY50 medido ou confirmado em 3,3 V ou 5 V.
- [ ] Se o TX for 3,3 V, confira na ficha do Mega que o nível alto é reconhecido.
      O nível alto mínimo do Mega é 3,0 V; 3,3 V costuma funcionar, com pouca folga.
- [ ] Se o RX do DY50 não aceitar 5 V, o sinal D18 passa por divisor (seção 3.3).
- [ ] Jumper do lado das trilhas de cima da MB102 em OFF; medidos `000` (trilha de cima) e `003` (trilha de baixo) antes de ligar a USB.

### 3.10 Fechadura 12 V / 2 A com driver

Esquema de princípio (os nomes dos bornes dependem do driver comprado):

| De | Para |
|---|---|
| Fonte 12 V, (+) | Entrada de potência do driver (V+) |
| Driver, saída (OUT+) | Fechadura (+) |
| Driver, saída (OUT-) | Fechadura (-) |
| Fonte 12 V, (-) | GND de potência do driver |
| GND da lógica (Mega e protoboard) | Terminal GND do driver, por fio fino só de referência |
| D35 do Mega | Entrada de sinal do driver (IN) |
| Entrada IN do driver | Resistor de 10 kΩ para GND (pull-down) |

Observações:

- **Recomendação, consta em MATERIAIS.md, Ferramentas e itens de apoio:** o resistor de 10 kΩ
  entre a entrada do driver e o GND. Sem ele, D35 fica flutuando durante o
  reset e o bootloader do Mega, por 1 a 2 s, e a fechadura pode acionar.
- A entrada do driver deve aceitar 5 V do Mega, conforme MATERIAIS.md.
- Diodo de roda livre em paralelo com a bobina: faixa (cátodo) no +12 V e
  ânodo no negativo da fechadura. Se o driver já tiver diodo, confirme na ficha.
- A fonte 12 V fica separada da protoboard e da placa. Dimensione a corrente com
  margem sobre os 2 A da fechadura (conferir na ficha da fonte).
- A corrente da fechadura volta só pelo caminho fonte 12 V -> driver -> fechadura.
  Nunca pelo Mega nem pela protoboard. O fio de GND entre os dois lados é fino e só serve de referência.
- Se usar relé no lugar do driver (por exemplo, módulo MOSFET), os contatos e a ligação mudam. A bobina nunca
  vai direto a um pino do Mega.
- `LOCK_ON = HIGH`: D35 em HIGH energiza a fechadura. Confirme o sentido de
  acionamento do driver na ficha.

Modos de acionamento (`LOCK_MODE` no `Config.h`):

| Modo | Quando energiza | Quando usar |
|---|---|---|
| 0 | Nunca | Padrão de bancada. A fechadura fica desligada |
| 1 | Pulso de `LOCK_PULSE_MS` (no exemplo, 200 ms) após a autorização | Fechadura que abre por pulso e rearma ao fechar a porta |
| 2 | Enquanto a porta espera abertura, até abrir ou expirar 60 s | Só se a fechadura suportar energização contínua por esse tempo, pela ficha do fabricante |

Antes de energizar:

- [ ] `LOCK_MODE=0` no `Config.h` do Mega.
- [ ] Fechadura desconectada do driver.
- [ ] Fonte 12 V desligada.
- [ ] Medir D35 em 0 V após ligar o Mega (com o pull-down instalado).

---

## 4. Gravação da ESP32-CAM

A placa não tem auto-reset. Você precisa fazer o reset manualmente.

Fios para gravar:

| De (adaptador USB-serial) | Para (CAM) |
|---|---|
| TX | U0R (GPIO3) |
| RX | U0T (GPIO1) |
| GND | GND comum |

Passos:

1. Use um adaptador com sinais de 3,3 V. Se houver jumper 5 V/3V3, deixe em
   3V3. Meça a tensão do TX em repouso antes de ligar. Deve estar perto de 3,3 V.
   Se estiver em 5 V, pare.
2. **Nunca ligue o 5V/VCC do adaptador ao 5V da CAM.** A CAM é sempre alimentada
   pelo step-down da seção 3.1, ou pela base ESP32-CAM-MB (ver abaixo).
3. Com a CAM desligada, ligue GPIO0 ao GND.
4. Pressione o botão RST da placa, ou religue a alimentação. A placa entra em modo de gravação.
5. Grave pelo IDE ou pelo esptool, conforme o procedimento do seu ambiente.
6. Retire o GPIO0 do GND.
7. Pressione RST ou religue a alimentação. A placa roda o firmware.
8. Abra o monitor da CAM a 115200 no mesmo adaptador e pressione RST para ver `CAM boot ...`.

Observações:

- Não ligue nada em GPIO12. Ele define a tensão da flash no boot.
- Antes de gravar a CAM, confira que o `Config.h` local tem `WIFI_SSID`,
  `WIFI_PASSWORD`, `SERVER_URL`, `DEVICE_KEY` e `DEVICE_ID`. `DEVICE_KEY` deve
  bater com a configuração do servidor.
- Não comite o `Config.h` local nem coloque credenciais no repositório.

Adaptador do dono (31/10/2026): USB-serial PL2303, pinos `3V3`, `TXD`, `RXD`,
`GND`, `5V`; no Mac aparece como `/dev/cu.usbserial-10`. Use a tabela acima (TXD
no U0R, RXD no U0T, GND no GND). Os pinos `3V3` e `5V` do adaptador ficam soltos,
salvo decisão do dono (ver `docs/HANDOFF.md`, seção 7).

Alternativa, se um dia for usada a base ESP32-CAM-MB (conferir no produto):

- A CAM encaixa por cima da base. A base alimenta a CAM pela micro-USB e já liga
  a serial em 3,3 V. Não precisa dos fios da tabela acima.
- Antes de encaixar, desligue o step-down e solte da CAM os fios do 5V, do GND,
  do GPIO13 e do GPIO14. Nunca use a base USB e o step-down ao mesmo tempo.
- Para gravar: segure o botão IO0 da base, pressione o RST da CAM, solte o IO0 e
  grave pelo IDE com a placa "AI Thinker ESP32-CAM". Depois, pressione o RST.
- A medição do passo 1 (TX em 3,3 V) não se aplica à base.

---

## 5. Roteiro mínimo de bancada

Use `LOCK_MODE=0`, com a fechadura e o driver desconectados. Siga a ordem.

### Passo 1: adaptador sozinho

- Ligue o adaptador USB-serial no computador, sem a CAM.
- Meça TX para GND: deve estar perto de 3,3 V. Se estiver em 5 V, pare.

### Passo 2: CAM sozinha

- Ligue GNDs, step-down (5,0 V) no 5V da CAM e, depois, meça 5V e 3V3.
- Grave a CAM pela seção 4.
- Monitor a 115200. Mensagens esperadas:
  - `CAM boot <id> camera=ok`
  - `CAM wifi conectado <ip>` (depois que a rede subir)
- Com `CAM wifi conectado`, meça 5V e 3V3 de novo, porque o Wi-Fi puxa picos de corrente.
  Abaixo de cerca de 4,75 V no 5V, a fonte ou o cabo não entrega corrente suficiente.
  Com o alicate de resolução 1 V esta leitura não é confiável: observe também se
  aparece mensagem de brownout no monitor.
- Se aparecer `camera=falha` ou `CAM: camera falhou (...)`, pare e confira a câmera.
- Se aparecer mensagem de brownout (ESP-IDF; confira no monitor), a fonte ou o
  cabo não está entregando corrente suficiente.

### Passo 3: Mega sozinho pelo USB

- Ligue o Mega pelo USB. Coloque os jumpers D30 e D31 em GND para simular porta fechada.
- No LCD, veja "Iniciando..." e depois "Senha ou digital". Até o passo 7 o DY50 não
  está ligado, então "DY50 fora do ar" é o esperado nesta fase. "Falha memoria" bloqueia.
- Abra o monitor serial a 115200, com final de linha "Nova linha" (Newline). Abrir o
  monitor costuma reiniciar o Mega. Aparece uma linha de boot, no formato
  `BOOT boot=<n> storage=ok|falha dy50=ok|indisponivel lock_mode=<n>`.
- Envie `AUTH <senha de administrador de 10 dígitos>`. A resposta deve ser `OK authenticated`.
  Sem AUTH, comandos respondem `ERR auth_required`.
- Envie `STATUS`. Formato esperado:
  `last_id=... queued=... dropped=... replies_dropped=... dy50=indisponivel lock_mode=0`
  Até o passo 7 o DY50 não está ligado, então `dy50=indisponivel` é esperado nesta
  fase, tanto aqui quanto na linha `BOOT`.
- Meça D16 (esperado perto de 5 V em repouso) e D35 (esperado 0 V). Cada reset
  faz D35 flutuar por 1 a 2 s, por isso o pull-down da seção 3.10. Meça depois do boot.
- Pode aparecer `queued=1` logo após o boot: é o evento `device_boot` esperando
  confirmação da CAM. Após qualquer reset do Mega, `queued=1` (só o `device_boot`
  do boot atual, até a CAM confirmar; com D30 e D31 em GND e storage=ok; sensor
  aberto no boot soma forced_open e falha de memória soma storage_error): a fila
  fica em RAM e o reset a perde. Isso é esperado.

### Passo 4: divisor sem a CAM

- Desligue tudo. Monte o divisor na protoboard (seção 3.3): D16 -> 1 kΩ -> ponto
  do meio -> 2 kΩ -> GND. A CAM fica solta.
- Ligue o Mega pelo USB e meça o ponto do meio x GND: esperado perto de 3,3 V
  (TX em repouso). Se estiver perto de 5 V, pare: o 2 kΩ não está no GND.

### Passo 5: Mega envia para a CAM

- Desligue tudo antes de mexer nos fios.
- Ligue o ponto do meio do divisor ao GPIO13 da CAM. GNDs do Mega, do step-down e
  da CAM juntos.
- Energize o Mega e a CAM e meça GPIO13 x GND: esperado perto de 3,3 V. Nunca
  perto de 5 V.
- Com o servidor parado, a CAM deve imprimir uma destas duas mensagens. As duas
  começam com `Fila CAM:` e terminam com `item mantido para reenvio`:
  - Wi-Fi caído: `Fila CAM: rede indisponivel; item mantido para reenvio`
  - Wi-Fi no ar: `Fila CAM: <id> evento: rede/transporte (<status>); item mantido para reenvio`
- Qualquer uma das duas prova que a CAM recebeu o evento do Mega.

### Passo 6: CAM envia para o Mega

- Desligue tudo antes de mexer nos fios.
- Com a CAM ligada e o GPIO14 ainda solto, meça GPIO14 x GND: esperado perto de
  3,3 V em repouso.
- Desligue tudo. Ligue o GPIO14 direto ao D17 e energize.
- `STATUS` deve ir a `queued=0`, com `dropped=0` e `replies_dropped=0`. Isso prova
  que a CAM aceitou e enfileirou o evento (a CAM envia o ACK ao enfileirar, antes
  de qualquer HTTP). Não prova que o servidor recebeu: isso acontece até com o
  servidor parado.
- A prova de entrega ao servidor é o evento aparecer no painel (passo 7). As
  mensagens `DESCARTADO` e `entregue apos falha` da CAM são diagnóstico da entrega
  ao servidor e não mudam o `queued` do Mega. Na entrega normal de `device_boot` a
  CAM não imprime nada; em `access_granted` sem foto imprime
  `Fila CAM: <id> sem foto disponivel`. `entregue apos falha` só aparece se houve
  falha antes.

**Alerta de falso positivo:** `queued=0` com `dropped` ou `replies_dropped` maior
que 0 não prova o ACK, porque itens foram descartados no Mega. Só considere o ACK
recebido com `queued=0`, `dropped=0` e `replies_dropped=0`.

### Passo 7: fim a fim

- Confira o servidor e a rede Wi-Fi (`WIFI_SSID` e `SERVER_URL` corretos).
- Confirme que o `device_boot` aparece no painel.
- Só depois teste o DY50, o cadastro e a foto. Não teste a fechadura aqui.

Não considere os passos concluídos sem registrar o resultado de cada um.

---

## 6. Ensaio da fechadura

Faça este ensaio separadamente, depois do roteiro da seção 5. `LOCK_MODE=0` vale
até o passo 4. O passo 5 é o primeiro em que `LOCK_MODE` sai de 0.

Pré-requisitos:

- [ ] Fabricante da fechadura identificado. Tipo, tensão e regime da bobina conferidos.
- [ ] Driver escolhido com entrada compatível com 5 V e carga 12 V / 2 A com margem.
- [ ] Diodo de roda livre instalado junto da bobina.
- [ ] Resistor de pull-down de 10 kΩ na entrada do driver.
- [ ] Fonte 12 V separada, GND comum no ponto de referência.

Roteiro:

1. Teste da entrada do driver sem firmware, com a fechadura DESCONECTADA do
   driver e a fonte 12 V DESLIGADA:
   1. Desligue tudo.
   2. Solte o fio do D35 da entrada IN do driver. Isso é obrigatório: D35 é saída
      em LOW e 5 V nele causaria curto.
   3. Ligue um jumper do 5V do Mega à IN, através de um resistor de 220 Ω a 1 kΩ.
   4. Energize só o Mega.
   5. Meça IN: deve ficar perto de 5 V, um pouco abaixo pelo pull-down de 10 kΩ.
      Observe o LED de entrada do driver, se houver.
   6. Desligue, retire o jumper e religue D35 à IN.
2. Com a fechadura desconectada e `LOCK_MODE=0`, confirme toda a lógica.
3. Conecte a fechadura ao driver, com fonte 12 V desligada.
4. Ligue a fonte 12 V e confira a tensão no driver sem acionamento.
5. Primeiro ponto em que `LOCK_MODE` sai de 0. Com a fechadura conectada e
   conferida nos passos anteriores, siga esta ordem:
   1. Desligue a fonte 12 V (ou solte um fio da fechadura). Durante a gravação e
      o bootloader o D35 flutua 1 a 2 s.
   2. Regrave o Mega com `LOCK_MODE=1` e `LOCK_PULSE_MS=200` (valor padrão em
      `firmware/MegaControlador/Config.example.h`; ajuste no `Config.h`).
   3. Abra o monitor serial a 115200 e confirme `lock_mode=1` na linha `BOOT`.
      Com o monitor aberto o Mega pode reiniciar; os 12 V continuam desligados (ou o fio da fechadura continua solto).
      Meça D35 x GND: esperado 0 V em repouso.
   4. Só então ligue os 12 V (reconecte o fio, se foi solto). A partir daqui vale o
      aviso da seção 1: com 12 V ligados, não reinicie o Mega (monitor serial, RESET, USB).
   5. Autorize um acesso e observe um pulso no mecanismo. Um pulso não prova que a
      bobina aguenta energização contínua. Deixe o monitor serial aberto desde o
      subitem 3; daqui em diante não o feche nem reabra, não pressione RESET e não
      mexa no USB com os 12 V ligados. Qualquer reinício exige desligar os 12 V antes,
      como no subitem 1.
6. Decida o modo final com base no que foi observado no passo 5:
   - `LOCK_MODE=1` (pulso), se o mecanismo abriu com o pulso e rearmou sozinho ao
     fechar a porta. Valide `LOCK_PULSE_MS` com o mecanismo real.
   - Se a lingueta só rearma ao fechar a porta, o modo 1 não retrava o mecanismo ao
     expirar os 60 s sem abrir; ver o último parágrafo.
   - Trocar de modo exige regravação: 12 V desligados, como no passo 5.
7. `LOCK_MODE=2` (energizada até abrir ou expirar em 60 s), só se o mecanismo
   voltar a travar ao cortar energia e o fabricante permitir energização por até
   60 s. Confirme pelo fabricante, não pelo resultado do pulso. Para gravar este
   modo, use a mesma regra do passo 5 (12 V desligados durante a regravação).
8. Feche a porta e confirme os dois sensores (D30 e D31) em LOW.
9. Teste o engate real separadamente, com a porta encaixada.

Se o ensaio não for conclusivo (mecanismo sem resposta clara, dúvida sobre o
rearme ou fabricante não confirma), volte a `LOCK_MODE=0` e não deixe a fechadura
energizada pelo software. Antes de regravar, desligue os 12 V, como no passo 5.

Se a exigência de retravar sem abrir após 60 s for indispensável e o
mecanismo não permitir, troque o tipo de fechadura. Não resolva isso com pulso mais longo.
