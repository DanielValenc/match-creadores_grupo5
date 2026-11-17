"""TikTokCreatorSource: capa anticorrupción entre TikTok (motor SCRAPINGTIKTOK) y el dominio.

scrape_profile y extract_profile vienen de media-scraper (backend/reference_engine.py, commit a3ef81d) con
estos cambios: 30 videos, sin listas de seguidores/seguidos (max_list_items=0) ni comentarios
(max_comments_per_video=0), y headless configurable. Ver docs/plan-backend.md, paso 9.
"""
import asyncio
from datetime import datetime, timezone
import logging

from playwright.async_api import Error as PlaywrightError

from truematch.application.ports.creator_source import CreatorSource
from truematch.domain.creator_profiling.creator import Creator
from truematch.domain.creator_profiling.public_profile import PublicProfile
from truematch.domain.creator_profiling.username import Username
from truematch.domain.creator_profiling.video import Video, VideoStats

from .adapter import adapt_profile
from .runtime import USERNAME, AccessRestricted, IdentityError
from .vendor.scrapingtiktok.tiktok_scraper import TikTokScraper

MAX_VIDEOS = 30
logger = logging.getLogger(__name__)


async def extract_profile(username, max_videos=MAX_VIDEOS, headless=True):
    engine = TikTokScraper(headless=headless)
    try:
        raw = await engine.scrape(username, max_list_items=0, max_videos=max_videos, max_comments_per_video=0)
        return adapt_profile(raw, username, max_videos=max_videos)
    except (AccessRestricted, IdentityError):
        raise
    except PlaywrightError:
        raise RuntimeError('No se pudo iniciar Chromium o cargar TikTok. Comprueba la sesión local y la conexión.') from None


def scrape_profile(username, max_videos=MAX_VIDEOS, headless=True):
    """Diccionario adaptado del motor (contrato de media-scraper), con enteros exactos o None."""
    username = username.strip().removeprefix('@')
    if not USERNAME.fullmatch(username):
        raise ValueError('Invalid TikTok username.')
    profile = asyncio.run(extract_profile(username, max_videos=max_videos, headless=headless))
    logger.info('engine=SCRAPINGTIKTOK publications=%s', len(profile['videos']))
    return profile


def _datetime(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp is not None else None


def to_creator(profile, requested):
    """Traduce el diccionario adaptado a un Creator. El usuario es el solicitado: el adaptador ya verificó
    que coincide con la cuenta de TikTok (sin distinguir mayúsculas)."""
    videos = tuple(
        Video(
            id=video['id'],
            url=video['url'],
            description=video.get('title') or None,
            published_at=_datetime(video.get('created_at')),
            thumbnail_url=video.get('preview_url') or None,
            stats=VideoStats(views=video['views'], likes=video['likes'], comments=video['comments'],
                             shares=video['shares'], saves=video['saves']),
        )
        for video in profile['videos']
    )
    public_profile = PublicProfile(
        followers=profile['followers'], following=profile['following'], likes=profile['likes'],
        nickname=profile.get('nickname') or None, avatar_url=profile.get('avatar_url') or None,
    )
    return Creator(username=requested, profile=public_profile, videos=videos)


class TikTokCreatorSource(CreatorSource):
    def __init__(self, max_videos=MAX_VIDEOS, headless=True):
        self.max_videos = max_videos
        self.headless = headless

    def fetch(self, username: Username) -> Creator:
        profile = scrape_profile(username.value, max_videos=self.max_videos, headless=self.headless)
        for warning in profile.get('_meta', {}).get('warnings', []):
            logger.info(warning)
        return to_creator(profile, username)
