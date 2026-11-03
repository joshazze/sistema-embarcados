"""Confere que o LCD 1602 do Mega é só o modo 4 bits (LiquidCrystal, sem I2C), por análise estática."""
import re
from pathlib import Path
import unittest

MEGA = Path(__file__).resolve().parents[1] / 'firmware/MegaControlador'
LCD_PINS = {'LCD_PIN_RS': 37, 'LCD_PIN_E': 38, 'LCD_PIN_D4': 39, 'LCD_PIN_D5': 40, 'LCD_PIN_D6': 41, 'LCD_PIN_D7': 42}


def pinos_do_exemplo():
    texto = (MEGA / 'Config.example.h').read_text()
    pinos = set()
    for nome in ('LOCK_PIN', 'BUZZER_PIN', 'BUTTON_1', 'BUTTON_2', 'LED_R', 'LED_G', 'LED_B'):
        m = re.search(r'\b%s\s*=\s*(\d+)' % nome, texto)
        assert m, 'pino %s não encontrado no Config.example.h' % nome
        pinos.add(int(m.group(1)))
    for nome in ('ROW_PINS', 'COL_PINS'):
        m = re.search(r'\b%s\[\d+\]\s*=\s*\{([\d,\s]+)\}' % nome, texto)
        assert m, '%s não encontrado no Config.example.h' % nome
        pinos.update(int(n) for n in re.findall(r'\d+', m.group(1)))
    return pinos


class Lcd4BitsTests(unittest.TestCase):
    def setUp(self):
        self.sketch = (MEGA / 'MegaControlador.ino').read_text()
        self.exemplo = (MEGA / 'Config.example.h').read_text()

    def test_sem_i2c_nem_wire_no_sketch(self):
        self.assertNotRegex(self.sketch, r'LiquidCrystal_I2C')
        self.assertNotRegex(self.sketch, r'#include\s*<Wire\.h>')
        self.assertNotRegex(self.sketch, r'\bWire\s*\.')

    def test_sem_macro_lcd_parallel(self):
        self.assertNotRegex(self.sketch, r'\bLCD_PARALLEL\b')

    def test_include_liquidcrystal_presente_uma_vez(self):
        self.assertEqual(len(re.findall(r'#include\s*<LiquidCrystal\.h>', self.sketch)), 1)

    def test_pinos_padrao_com_ifndef(self):
        for nome, valor in LCD_PINS.items():
            with self.subTest(nome=nome):
                self.assertRegex(
                    self.sketch,
                    r'#ifndef\s+%s\s+#define\s+%s\s+%d\s+#endif' % (nome, nome, valor),
                )

    def test_construtor_usa_os_seis_pinos(self):
        self.assertRegex(
            self.sketch,
            r'LiquidCrystal\s+lcd\s*\(\s*LCD_PIN_RS\s*,\s*LCD_PIN_E\s*,\s*LCD_PIN_D4\s*,'
            r'\s*LCD_PIN_D5\s*,\s*LCD_PIN_D6\s*,\s*LCD_PIN_D7\s*\)\s*;',
        )

    def test_lcdboot_inicializa_16_por_2(self):
        self.assertRegex(self.sketch, r'void\s+lcdBoot\s*\(\s*\)\s*\{\s*lcd\.begin\(16,\s*2\);')

    def test_pinos_do_lcd_nao_colidem_com_o_exemplo(self):
        usados = pinos_do_exemplo()
        self.assertTrue(usados, 'extração de pinos do Config.example.h falhou')
        for nome, valor in LCD_PINS.items():
            with self.subTest(nome=nome):
                self.assertNotIn(valor, usados)
                self.assertNotIn(valor, range(16, 22))

    def test_exemplo_sem_lcd_address(self):
        self.assertNotRegex(self.exemplo, r'\bLCD_ADDRESS\b')

    def test_exemplo_documenta_lcd_4_bits(self):
        self.assertRegex(self.exemplo, r'LCD 1602 em modo 4 bits')
        self.assertRegex(self.exemplo, r'RW do LCD vai no GND')


if __name__ == '__main__':
    unittest.main()
