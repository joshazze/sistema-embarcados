"""Confere, pelo texto, que a OTA da CAM so existe sob a guarda OTA_PASSWORD. Nao abre Config.h."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAM = ROOT / 'firmware/Esp32CamRede'


class CamOtaTests(unittest.TestCase):
    def test_arduino_ota_only_under_ota_password_guard(self):
        lines = (CAM / 'Esp32CamRede.ino').read_text().splitlines()
        stack = []
        found = 0
        for line in lines:
            code = line.strip()
            if code.startswith('#if'):
                stack.append(code)
            elif code.startswith('#endif'):
                stack.pop()
            elif 'ArduinoOTA' in code:
                found += 1
                self.assertTrue(any('defined(OTA_PASSWORD)' in g for g in stack), code)
        self.assertGreater(found, 0)

    def test_ota_password_is_set_from_config(self):
        sketch = (CAM / 'Esp32CamRede.ino').read_text()
        self.assertIn('ArduinoOTA.setPassword(OTA_PASSWORD)', sketch)
        self.assertIn('ArduinoOTA.setHostname("controle-cam")', sketch)
        self.assertIn('static_assert(sizeof(OTA_PASSWORD) > 8', sketch)

    def test_config_example_has_ota_line_commented(self):
        example = (CAM / 'Config.example.h').read_text().splitlines()
        self.assertIn('// #define OTA_PASSWORD "DEFINA_UMA_SENHA_OTA"', example)
        self.assertFalse(any(re.match(r'\s*#\s*define\s+OTA_PASSWORD', line) for line in example))


if __name__ == '__main__':
    unittest.main()
