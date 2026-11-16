# Origen: media-scraper, rama feature/setup-inicial, commit a3ef81d2e533d0c9e58e144ee6c4c863a43961cc,
# archivo tests/test_reference_engine.py (ver docs/plan-backend.md, paso 8). Solo se traen, sin cambios,
# OWNER, raw_profile() y estos casos de AdapterTests, con los imports ajustados:
#   - test_pristine_upstream_copy_and_mit_license_are_preserved
#   - test_comment_responses_require_exact_host_endpoint_and_publication
#   - test_user_response_requires_profile_identity_and_current_scene
# No se traen: los casos que usan normalize_profile/ProfileRepository/MemoryDatabase (MongoDB), los que usan
# reference_adapter, reference_engine o backend.main (llegan en el paso 9) y OriginalBrowserTests (abre Chromium).
"""Integrated original engine tests. All browser traffic is intercepted offline."""
import hashlib
from pathlib import Path
import unittest
from unittest.mock import Mock

from truematch.infrastructure.tiktok import runtime as reference_runtime
from truematch.infrastructure.tiktok.vendor.scrapingtiktok import tiktok_scraper as original

OWNER = {'uniqueId': 'example', 'id': '42', 'secUid': 'public-example'}


def raw_profile():
    return {'success': True, 'username': 'example', 'user_id': '42', 'sec_uid': 'public-example',
            'followers_count': 1234567, 'following_count': 0, 'heart_count': None,
            'followers_list': [{'username': 'reader'}, {'username': 'READER'}], 'following_list': [],
            'videos': [{'_verified': True, 'video_id': '333', 'video_url': 'https://www.tiktok.com/@example/video/333',
                        'description': 'Text', 'create_time': 1700000000, 'views_count': 2345678,
                        'likes_count': 0, 'comments_count': 20, 'shares_count': None,
                        'comments': [{'comment_id': '5', 'username': 'reader', 'text': 'Network', 'likes_count': 0},
                                     {'comment_id': '', 'username': 'dom', 'text': 'DOM', 'likes_count': None}]}]}


class AdapterTests(unittest.TestCase):
    def test_pristine_upstream_copy_and_mit_license_are_preserved(self):
        root = Path(original.__file__).parent
        digest = hashlib.sha256((root / 'upstream' / 'tiktok_scraper.py').read_bytes()).hexdigest()
        self.assertEqual(digest, 'b836bbc154b29a96abc491313ddb1409a1a5240be977c2dc37baef292459ad0a')
        license_text = (root / 'LICENSE').read_text()
        self.assertIn('MIT License', license_text)
        self.assertIn('Copyright (c) 2026 Jccasav', license_text)

    def test_comment_responses_require_exact_host_endpoint_and_publication(self):
        for url, accepted in (
            ('https://www.tiktok.com/api/comment/list/?aweme_id=333', True),
            ('https://www.tiktok.com/api/comment/list/?aweme_id=999', False),
            ('https://www.tiktok.com/api/comment/list/', False),
            ('https://www.tiktok.com/api/comment/list/?aweme_id=333&aweme_id=999', False),
            ('https://foreign.invalid/api/comment/list/?aweme_id=333', False),
            ('https://www.tiktok.com/api/comment/list/reply/?aweme_id=333', False),
        ):
            response = Mock(url=url, status=200)
            self.assertEqual(reference_runtime.comment_response_matches(response, raw_profile()['videos'][0]['video_url']), accepted)

    def test_user_response_requires_profile_identity_and_current_scene(self):
        for query, accepted in (('scene=67&secUid=public-example', True), ('scene=21&secUid=public-example', False),
                                ('scene=67', False), ('scene=67&secUid=other', False),
                                ('scene=67&secUid=public-example&userId=99', False)):
            response = Mock(url='https://www.tiktok.com/api/user/list/?' + query, status=200)
            self.assertEqual(reference_runtime.user_response_matches(response, OWNER, '67'), accepted)
