"""API web que consume la app móvil: no abre TikTok ni llama a Groq; los datos van a una carpeta temporal."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from truematch.interfaces.cli.main import decide_login
from truematch.interfaces.web.app import app

PROPUESTA = {
    "usuario_creador": "@ana.ec", "marca": "Marca Demo", "correo_contacto": "marca@demo.com",
    "sector": "Moda y accesorios", "campana": "Verano 2026", "mensaje": "Hola, queremos colaborar.",
    "presupuesto": 500,
}


class WebApiTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        patcher = patch.dict(os.environ, {"TRUEMATCH_DATA_DIR": self.folder.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = app.test_client()

    def guardar_creador(self, usuario, **extra):
        data = {"usuario": usuario, "perfil": {"foto_perfil": "https://x/f.jpg", "seguidores": 1200}, **extra}
        Path(self.folder.name, f"datos_{usuario}.json").write_text(json.dumps(data), encoding="utf-8")

    def test_health(self):
        self.assertEqual(self.client.get("/api/health").get_json(), {"ok": True, "servicio": "Match Creadores"})

    def test_datos_guardados(self):
        self.assertEqual(self.client.get("/api/datos/nadie").status_code, 404)
        self.guardar_creador("ana.ec")
        respuesta = self.client.get("/api/datos/@ana.ec").get_json()
        self.assertTrue(respuesta["ok"])
        self.assertEqual(respuesta["datos"]["usuario"], "ana.ec")

    def test_listar_creadores_ignora_archivos_invalidos(self):
        self.guardar_creador("ana.ec", auditoria_audiencia={"puntaje_organico": 80})
        Path(self.folder.name, "datos_roto.json").write_text("{no es json", encoding="utf-8")
        respuesta = self.client.get("/api/creadores").get_json()
        self.assertEqual(respuesta["total"], 1)
        self.assertEqual(respuesta["creadores"][0]["usuario"], "ana.ec")
        self.assertEqual(respuesta["creadores"][0]["puntaje_organico"], 80)

    def test_propuesta_exige_creador_analizado(self):
        self.assertEqual(self.client.post("/api/propuestas", json=PROPUESTA).status_code, 409)

    def test_propuesta_validaciones(self):
        self.guardar_creador("ana.ec")
        for cambio in ({"correo_contacto": "no-es-correo"}, {"marca": ""}, {"presupuesto": -1},
                       {"presupuesto": "mucho"}, {"mensaje": "x" * 3001}, {"usuario_creador": "a b"}):
            with self.subTest(cambio=cambio):
                self.assertEqual(self.client.post("/api/propuestas", json={**PROPUESTA, **cambio}).status_code, 400)

    def test_crear_listar_y_obtener_propuesta(self):
        self.guardar_creador("ana.ec")
        creada = self.client.post("/api/propuestas", json=PROPUESTA)
        self.assertEqual(creada.status_code, 201)
        propuesta = creada.get_json()["propuesta"]
        self.assertEqual((propuesta["usuario_creador"], propuesta["estado"]), ("ana.ec", "pendiente"))

        self.assertEqual(self.client.get("/api/propuestas").get_json()["total"], 1)
        self.assertEqual(self.client.get("/api/propuestas?username=@ANA.EC").get_json()["total"], 1)
        self.assertEqual(self.client.get("/api/propuestas?username=otro").get_json()["total"], 0)
        self.assertEqual(self.client.get(f"/api/propuestas/{propuesta['id']}").get_json()["propuesta"]["id"], propuesta["id"])
        self.assertEqual(self.client.get("/api/propuestas/inexistente").status_code, 404)

    def test_propuesta_con_acentos_cabe_en_el_limite_de_peticion(self):
        self.guardar_creador("ana.ec")
        grande = {**PROPUESTA, "mensaje": "ñ" * 3000}
        self.assertEqual(self.client.post("/api/propuestas", json=grande).status_code, 201)


class DecideLoginTests(unittest.TestCase):
    def test_banderas_mandan(self):
        self.assertTrue(decide_login(True, False))
        self.assertFalse(decide_login(False, True))

    def test_sin_terminal_no_pregunta(self):
        with patch("sys.stdin.isatty", return_value=False), patch("builtins.input") as pregunta:
            self.assertFalse(decide_login(False, False))
        pregunta.assert_not_called()

    def test_con_terminal_pregunta(self):
        with patch("sys.stdin.isatty", return_value=True):
            for respuesta, esperado in (("s", True), ("Sí", True), ("n", False), ("", False)):
                with self.subTest(respuesta=respuesta), patch("builtins.input", return_value=respuesta):
                    self.assertEqual(decide_login(False, False), esperado)


if __name__ == "__main__":
    unittest.main()
