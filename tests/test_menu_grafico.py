"""Pruebas de carga segura de configuración para la interfaz."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from menu_grafico import cargar_entorno_local


class CargarEntornoLocalTest(unittest.TestCase):
    def test_carga_variables_y_quita_comillas_sin_sobrescribir_entorno(self):
        with TemporaryDirectory() as temporal:
            archivo = Path(temporal) / ".env"
            archivo.write_text(
                '# configuración local\n'
                'CODEx_TEST_HOST=localhost\n'
                'CODEX_TEST_PASSWORD="clave local"\n'
                'CODEX_TEST_KEEP=archivo\n',
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"CODEX_TEST_KEEP": "proceso"}, clear=False):
                for clave in ("CODEx_TEST_HOST", "CODEX_TEST_PASSWORD"):
                    os.environ.pop(clave, None)
                cargar_entorno_local(archivo)
                self.assertEqual(os.environ["CODEx_TEST_HOST"], "localhost")
                self.assertEqual(os.environ["CODEX_TEST_PASSWORD"], "clave local")
                self.assertEqual(os.environ["CODEX_TEST_KEEP"], "proceso")
                os.environ.pop("CODEx_TEST_HOST", None)
                os.environ.pop("CODEX_TEST_PASSWORD", None)

    def test_ignora_archivo_inexistente(self):
        with TemporaryDirectory() as temporal:
            cargar_entorno_local(Path(temporal) / "ausente.env")


if __name__ == "__main__":
    unittest.main()
