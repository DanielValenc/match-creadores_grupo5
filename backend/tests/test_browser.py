# Origen: media-scraper, rama feature/setup-inicial, commit a3ef81d2e533d0c9e58e144ee6c4c863a43961cc,
# archivo tests/test_browser.py (ver docs/plan-backend.md, paso 8). Solo se trae, sin cambios, el caso
# test_profile_persists_cookie_and_local_storage (prueba session.py), con los imports ajustados.
# Los demás casos prueban el frontend de media-scraper y no se traen.
# ATENCIÓN: este caso abre Chromium en modo headless con tráfico interceptado (sin red). Requiere
# `playwright install chromium`.
"""Offline Chromium checks; all requests use local synthetic fixtures."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from truematch.infrastructure.tiktok import session

ORIGIN = "https://media-scraper.invalid"


class OfflineBrowserTests(unittest.TestCase):
    def test_profile_persists_cookie_and_local_storage(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(session, 'PRIVATE_DIR', Path(folder) / 'private'):
            for first_visit in (True, False):
                with session.persistent_context() as context:
                    context.route('**/*', lambda route: route.fulfill(body='<html>Local test</html>', content_type='text/html'))
                    page = context.new_page()
                    page.goto(ORIGIN)
                    if first_visit:
                        context.add_cookies([{'name': 'synthetic_test', 'value': 'offline',
                                              'url': ORIGIN, 'expires': 4102444800}])
                        page.evaluate("localStorage.setItem('synthetic_test', 'offline')")
                    else:
                        self.assertEqual(page.evaluate("localStorage.getItem('synthetic_test')"), 'offline')
                        self.assertTrue(any(c['name'] == 'synthetic_test' and c['value'] == 'offline'
                                            for c in context.cookies()))
