# Diagramas da protoboard e da CAM

Data: 02/11/2026.

Os SVGs abrem no navegador (arrastar o arquivo para a janela, ou clicar com o botão direito e "Abrir com").

## Arquivos

- `01-projeto-completo-montagem-de-uso.svg`: montagem de uso planejada (Mega, MB102, DY50, teclado, buzzer, fechadura e CAM).
  Ressalvas:
  - A parte da CAM é PLANO, não montado nem testado: D16 -> divisor 330 Ω -> IO13; IO14 -> D17; CAM nas trilhas de cima a 5 V da fonte YwRobot, com o jumper de cima em 5V; fio 5V do Mega fora das trilhas.
  - No desenho, o divisor da CAM está nas colunas 31 a 40 da metade de baixo. O plano atual é reaproveitar o divisor da gravação nas colunas 40 a 49 (D16 na coluna 40; coluna 43 -> IO13). Vale o plano atual.
  - LCD, LED RGB e fechadura não aparecem ligados.
  - As cores dos fios do DY50 são ilustração.
- `02-cam-gravacao-pelo-mega.svg`: montagem para gravar a CAM usando o Mega como adaptador.
  - RESET do Mega no GND; 5V/GND do Mega na CAM só para gravar; IO0-GND na CAM.
  - Divisor de 9 resistores de 330 Ω nas colunas 40 a 49: pino 0 -> coluna 40; coluna 49 -> GND; coluna 43 -> U0R só depois de medir (ver `docs/HANDOFF.md`, seção 9); U0T -> pino 1.
- `03-protoboard-estado-02-11-antes-da-cam.svg`: estado da protoboard em 02/11, antes da CAM (fonte YwRobot com o lado de cima em OFF; 3,3 V embaixo para o DY50; fio 5V do Mega nas trilhas de cima). Superado pela troca do lado de cima para 5V (ver `docs/HANDOFF.md`).
- `04-cam-gravacao-pelo-pl2303-historico.svg`: tentativa de gravação pelo PL2303. Falhou; fica como histórico.

## Geradores

Os scripts ficam em `scripts/diagramas/` (`gen_full.py`, `gen_all.py`, `gen_ponte.py`, `gen_cam2.py`).
Para regenerar: entrar na pasta de saída e rodar `python3 <caminho-do-script>`. Os caminhos de saída são relativos, então o SVG é gravado na pasta corrente.

## Uso

Base para remontar e organizar os cabos. O dono vai refazer as conexões; estes desenhos não substituem a conferência na bancada.
