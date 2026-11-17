
"""Compatibility and provenance checks for the vendored TikTok engine."""

import asyncio
import inspect
import logging
import os
import re

from contextlib import asynccontextmanager
from functools import wraps
from urllib.parse import parse_qs, urlparse

from playwright.async_api import async_playwright

from .session import profile_lock


logger = logging.getLogger("TikTokRuntime")

USERNAME = re.compile(r"^[A-Za-z0-9._]{1,24}$")


class AccessRestricted(RuntimeError):
    pass


class IdentityError(RuntimeError):
    pass


def checked_int(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, str))
        or not re.fullmatch(r"[0-9]+", str(value))
    ):
        raise ValueError("Unknown numeric metric")

    return int(value)


def first_known(*values):
    return next(
        (value for value in values if value is not None),
        None
    )


def metric_dict(item):
    result = {}

    for field in ("stats", "statsV2"):
        stats = item.get(field)

        if not isinstance(stats, dict):
            continue

        for key, value in stats.items():
            try:
                result[key] = checked_int(value)
            except ValueError:
                pass

    return result


def publication_url(url):
    parsed = urlparse(url)

    match = re.fullmatch(
        r"/@([A-Za-z0-9._]{1,24})/(video|photo)/(\d+)/?",
        parsed.path
    )

    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"www.tiktok.com", "tiktok.com"}
        or not match
    ):
        raise IdentityError(
            "Enlace de publicación no verificable."
        )

    return match.groups()


def verified_profile(user, requested):
    if (
        not isinstance(user, dict)
        or str(user.get("uniqueId", "")).casefold()
        != requested.casefold()
    ):
        raise IdentityError(
            "El perfil no corresponde al usuario solicitado."
        )

    return {
        key: str(user[key])
        for key in ("uniqueId", "id", "secUid")
        if user.get(key)
    }


def verified_publication(item, url, expected):
    username, _, publication_id = publication_url(url)

    if str(item.get("id", "")) != publication_id:
        raise IdentityError(
            "El JSON no corresponde a la publicación solicitada."
        )

    owner = {
        "uniqueId": username,
        **expected
    }

    author = item.get("author")

    if isinstance(author, str):
        author = {"uniqueId": author}

    author = dict(author) if isinstance(author, dict) else {}

    for field, key in (
        ("authorId", "id"),
        ("authorSecId", "secUid")
    ):
        if item.get(field) is not None:
            if (
                author.get(key) is not None
                and str(author[key]) != str(item[field])
            ):
                raise IdentityError(
                    "Autoría contradictoria en la publicación."
                )

            author[key] = item[field]

    shared = set(author) & set(owner)

    if not shared:
        raise IdentityError(
            "Autoría de la publicación no verificable."
        )

    for key in shared:
        a = str(author[key])
        b = str(owner[key])

        matches = (
            a.casefold() == b.casefold()
            if key == "uniqueId"
            else a == b
        )

        if not matches:
            raise IdentityError(
                "La publicación pertenece a otra cuenta."
            )

    if username.casefold() not in {
        str(value).casefold()
        for value in owner.values()
    }:
        raise IdentityError(
            "El enlace pertenece a otra cuenta."
        )

    return True


def response_query(response, path):
    parsed = urlparse(response.url)

    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"www.tiktok.com", "tiktok.com"}
        or parsed.path.rstrip("/") != path
        or response.status != 200
    ):
        return None

    return parse_qs(
        parsed.query,
        keep_blank_values=True
    )


def comment_response_matches(response, video_url):
    query = response_query(
        response,
        "/api/comment/list"
    )

    return (
        query is not None
        and query.get("aweme_id")
        == [publication_url(video_url)[2]]
    )


def comment_data_matches(data, video_url):
    publication_id = publication_url(video_url)[2]

    return (
        isinstance(data, dict)
        and isinstance(data.get("comments"), list)
        and all(
            type(data[key]) is int and data[key] == 0
            for key in ("status_code", "statusCode")
            if key in data
        )
        and (
            "aweme_id" not in data
            or str(data["aweme_id"]) == publication_id
        )
    )


def valid_comment(entry, video_url):
    if not isinstance(entry, dict):
        return False

    if (
        "aweme_id" in entry
        and str(entry["aweme_id"])
        != publication_url(video_url)[2]
    ):
        return False

    user = entry.get("user")

    names = (
        [
            user[key]
            for key in ("unique_id", "uniqueId")
            if user.get(key)
        ]
        if isinstance(user, dict)
        else []
    )

    return (
        bool(names)
        and all(
            isinstance(name, str)
            and USERNAME.fullmatch(name)
            for name in names
        )
        and len({name.casefold() for name in names}) == 1
        and isinstance(entry.get("text"), str)
        and bool(entry["text"].strip())
    )


def comment_already_captured(comments, entry):
    cid = entry.get("cid")

    if cid is not None and str(cid).isdigit():
        return any(
            comment["comment_id"] == str(cid)
            for comment in comments
        )

    user = entry.get("user") or {}

    name = (
        user.get("unique_id")
        or user.get("uniqueId")
        or ""
    )

    return any(
        comment["username"].casefold() == name.casefold()
        and comment["text"] == entry.get("text")
        for comment in comments
    )


def user_response_matches(response, owner, active_scene):
    query = response_query(
        response,
        "/api/user/list"
    )

    if (
        query is None
        or active_scene not in {"67", "21"}
        or query.get("scene") != [active_scene]
    ):
        return False

    matched = False

    for parameter, key in (
        ("secUid", "secUid"),
        ("userId", "id")
    ):
        if parameter in query:
            if (
                not owner.get(key)
                or query[parameter] != [str(owner[key])]
            ):
                return False

            matched = True

    return matched


def user_data_matches(data, owner):
    return (
        isinstance(data, dict)
        and all(
            str(data[field]) == str(owner.get(key, ""))
            for field, key in (
                ("secUid", "secUid"),
                ("userId", "id")
            )
            if field in data
        )
    )


# ---------------------------------------------------------
# DETECCIÓN DE CAPTCHA E INICIO DE SESIÓN
# ---------------------------------------------------------

async def _has_visible_element(page, selector):
    """Comprueba si existe algún elemento visible para el selector."""

    try:
        locator = page.locator(selector)
        count = min(await locator.count(), 10)

        for index in range(count):
            if await locator.nth(index).is_visible():
                return True

    except Exception:
        return False

    return False


async def _detect_access_issue(page):
    """
    Devuelve el tipo de restricción detectada o None.

    No intenta resolver, saltar ni interactuar automáticamente
    con los mecanismos de verificación de TikTok.
    """

    path = urlparse(page.url).path.lower()

    if re.search(r"/(captcha|verify|challenge)(/|$)", path):
        return (
            "TikTok solicita verificación mediante CAPTCHA."
        )

    if re.search(r"/(login|signup)(/|$)", path):
        return (
            "TikTok solicita autenticación."
        )

    captcha_selectors = (
        '[id*="captcha"]',
        '[class*="captcha"]',
        'iframe[src*="captcha"]',
        'iframe[src*="verify"]',
        '[class*="Verify"]',
        '[id*="verify"]',
    )

    for selector in captcha_selectors:
        if await _has_visible_element(page, selector):
            return (
                "TikTok solicita verificación mediante CAPTCHA."
            )

    login_selectors = (
        '[data-e2e="login-modal"]',
        '[data-e2e="login-dialog"]',
    )

    for selector in login_selectors:
        if await _has_visible_element(page, selector):
            return (
                "TikTok solicita autenticación."
            )

    return None


async def validate_access(
    page,
    *,
    headless=None,
    manual_timeout_seconds=None
):
    """
    Comprueba si TikTok está solicitando verificación.

    Modo headless:
        Lanza AccessRestricted inmediatamente.

    Modo visible:
        Mantiene Chromium abierto y espera a que el usuario
        complete manualmente el CAPTCHA o inicio de sesión.
    """

    raw_page = getattr(page, "raw", page)

    if raw_page.is_closed():
        raise AccessRestricted(
            "La página de TikTok se cerró antes de completar "
            "la verificación."
        )

    # Las páginas administradas por GuardedPage llevan
    # el modo headless asociado.
    if headless is None:
        headless = getattr(page, "headless", True)

    issue = await _detect_access_issue(raw_page)

    if issue is None:
        return

    # En ejecución invisible no es posible resolver manualmente
    # el CAPTCHA desde el navegador.
    if headless:
        raise AccessRestricted(
            f"{issue} Ejecuta: "
            "python -m truematch.interfaces.cli.main session"
        )

    # Tiempo máximo de espera configurable por variable de entorno.
    if manual_timeout_seconds is None:
        try:
            manual_timeout_seconds = int(
                os.getenv(
                    "TRUEMATCH_TIKTOK_MANUAL_VERIFY_TIMEOUT_SECONDS",
                    "600"
                )
            )
        except (TypeError, ValueError):
            manual_timeout_seconds = 600

    manual_timeout_seconds = max(
        30,
        manual_timeout_seconds
    )

    logger.warning(
        "%s Chromium permanecerá abierto. "
        "Completa manualmente la verificación en esa ventana. "
        "Tiempo máximo de espera: %s segundos.",
        issue,
        manual_timeout_seconds
    )

    loop = asyncio.get_running_loop()
    deadline = (
        loop.time() + manual_timeout_seconds
    )

    while loop.time() < deadline:

        if raw_page.is_closed():
            raise AccessRestricted(
                "Chromium se cerró mientras esperábamos "
                "la verificación manual."
            )

        await asyncio.sleep(1)

        issue = await _detect_access_issue(raw_page)

        if issue is None:
            logger.info(
                "La verificación manual terminó. "
                "El scraper continuará."
            )

            return

    raise AccessRestricted(
        "No se completó la verificación de TikTok dentro de "
        f"{manual_timeout_seconds} segundos. "
        "La ejecución se ha detenido."
    )


# ---------------------------------------------------------
# ENVOLTURAS PARA PLAYWRIGHT
# ---------------------------------------------------------

class GuardedInput:
    def __init__(self, raw, page):
        self.raw = raw
        self.page = page

    def __getattr__(self, name):
        method = getattr(self.raw, name)

        async def invoke(*args, **kwargs):
            await validate_access(self.page)

            result = await method(*args, **kwargs)

            await validate_access(self.page)

            return result

        return invoke


class GuardedPage:
    def __init__(self, raw, headless=True):
        self.raw = raw
        self.headless = headless

        self.mouse = GuardedInput(
            raw.mouse,
            self
        )

        self.keyboard = GuardedInput(
            raw.keyboard,
            self
        )

    def __getattr__(self, name):
        method = getattr(self.raw, name)

        if not inspect.iscoroutinefunction(method):
            return method

        @wraps(method)
        async def invoke(*args, **kwargs):

            if name != "close":
                await validate_access(self)

            result = await method(
                *args,
                **kwargs
            )

            if name != "close":
                await validate_access(self)

            return result

        return invoke


class ContextLease:
    """
    Ciclo de vida lógico de las páginas.

    Todas las páginas comparten el contexto persistente original.
    """

    def __init__(self, context, headless=True):
        self.context = context
        self.headless = headless
        self.pages = []

    async def new_page(self):
        raw_page = await self.context.new_page()

        page = GuardedPage(
            raw_page,
            headless=self.headless
        )

        self.pages.append(page)

        return page

    async def close(self):
        for page in self.pages:
            if not page.is_closed():
                await page.close()


class SharedBrowser:
    def __init__(self, context, engine):
        self.context = context
        self.engine = engine

    async def new_context(self, **kwargs):
        # Se conserva el contexto persistente.
        # Los argumentos por video no crean sesiones aisladas.
        return ContextLease(
            self.context,
            headless=self.engine.headless
        )

    async def close(self):
        if self.context is None:
            return

        try:
            await self.context.close()

        finally:
            self.engine._shared_context_closed = True


# ---------------------------------------------------------
# PLAYWRIGHT PERSISTENTE
# ---------------------------------------------------------

@asynccontextmanager
async def persistent_playwright(engine):
    with profile_lock() as profile:

        async with async_playwright() as playwright:

            engine._profile_path = str(profile)
            engine._shared_context = None
            engine._shared_context_closed = False

            try:
                yield playwright

            finally:
                context = engine._shared_context

                if (
                    context is not None
                    and not getattr(
                        engine,
                        "_shared_context_closed",
                        False
                    )
                ):
                    try:
                        await context.close()

                    except Exception:
                        logger.debug(
                            "El contexto persistente ya estaba cerrado.",
                            exc_info=True
                        )

                engine._shared_context = None


async def setup_persistent_context(engine, playwright):
    engine._shared_context = (
        await playwright.chromium.launch_persistent_context(
            user_data_dir=engine._profile_path,
            headless=engine.headless,
            accept_downloads=False
        )
    )

    engine._shared_context_closed = False

    browser = SharedBrowser(
        engine._shared_context,
        engine
    )

    return (
        browser,
        await browser.new_context()
    )
