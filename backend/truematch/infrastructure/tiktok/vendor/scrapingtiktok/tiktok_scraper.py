"""TikTok Scraper Module.

Extracts public profile information, followers/following when available,
recent videos, interaction metrics and public comments.

The persistent browser and manual verification lifecycle are managed by
truematch.infrastructure.tiktok.runtime.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from playwright.async_api import (
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from ...runtime import (
    AccessRestricted,
    IdentityError,
    checked_int,
    comment_already_captured,
    comment_data_matches,
    comment_response_matches,
    first_known,
    metric_dict,
    persistent_playwright,
    publication_url,
    setup_persistent_context,
    user_data_matches,
    user_response_matches,
    valid_comment,
    validate_access,
    verified_profile,
    verified_publication,
)


logger = logging.getLogger("TikTokScraper")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._]{1,24}$")


def load_env_cookie() -> Optional[str]:
    """Read TIKTOK_SESSION_ID from a local .env or environment variable.

    The value is returned only for compatibility with callers. This scraper
    does not inject, copy or manipulate private cookies automatically.
    """

    candidates: List[str] = []

    if "__file__" in globals():
        candidates.append(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        )

    candidates.append(os.path.join(os.getcwd(), ".env"))

    for env_path in candidates:
        if not os.path.exists(env_path):
            continue

        try:
            with open(env_path, "r", encoding="utf-8") as file:
                for raw_line in file:
                    line = raw_line.strip()

                    if (
                        line.startswith("TIKTOK_SESSION_ID=")
                        and not line.startswith("#")
                    ):
                        value = line.split("=", 1)[1].strip()
                        value = value.strip('"').strip("'")

                        if value:
                            return value

        except (AccessRestricted, IdentityError):
            raise
        except Exception:
            logger.exception("Error leyendo el archivo .env: %s", env_path)

    env_value = os.getenv("TIKTOK_SESSION_ID")
    return env_value.strip() if env_value else None


class TikTokScraper:
    """Scraper basado en Chromium persistente y Playwright."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        headless: bool = True,
    ) -> None:
        # La sesión persistente del navegador la administra runtime.py.
        # No se inyecta session_id ni se copian cookies privadas.
        self.session_id = None
        self._profile_owner: Dict[str, str] = {}
        self._active_scene: Optional[str] = None
        self._list_status = {
            "67": "not_observed",
            "21": "not_observed",
        }
        self.headless = headless
        self.stealth = None

    async def _setup_context(self, playwright) -> tuple[Any, Any]:
        """Create the persistent Chromium context managed by runtime.py."""
        return await setup_persistent_context(self, playwright)

    async def _wait_for_profile_data(
        self,
        page: Page,
        username: str,
        timeout_ms: Optional[int] = None,
    ) -> bool:
        """Wait for valid profile data and allow manual verification.

        In visible mode, runtime.validate_access() pauses here while the user
        completes TikTok's own CAPTCHA or authentication challenge. In
        headless mode, runtime keeps its normal fail-fast behavior.
        """

        clean_user = username.strip().lstrip("@").lower()

        if timeout_ms is None:
            # Runtime permits up to 600 seconds for manual verification by
            # default. Keep this outer wait slightly longer than that period.
            timeout_ms = 660000 if not self.headless else 20000

        timeout_ms = max(1000, timeout_ms)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + (timeout_ms / 1000)

        profile_script = """
            (username) => {
                const script = document.querySelector(
                    'script#__UNIVERSAL_DATA_FOR_REHYDRATION__'
                );

                if (!script || !script.textContent) {
                    return false;
                }

                try {
                    const data = JSON.parse(script.textContent);
                    const detail = data
                        .__DEFAULT_SCOPE__?.["webapp.user-detail"];
                    const user = detail?.userInfo?.user;

                    return (
                        detail?.statusCode === 0 &&
                        user?.uniqueId?.toLowerCase() === username
                    );
                } catch (_) {
                    return false;
                }
            }
        """

        if not self.headless:
            logger.warning(
                "Chromium está abierto. Si TikTok solicita CAPTCHA o "
                "autenticación, completa la verificación manualmente. "
                "El scraper continuará cuando TikTok permita acceder."
            )

        while loop.time() < deadline:
            try:
                # AccessRestricted must propagate. runtime.py waits in visible
                # mode and raises only when verification is not completed.
                await validate_access(page)

                remaining_ms = int((deadline - loop.time()) * 1000)
                if remaining_ms <= 0:
                    break

                # Short waits let us re-check access restrictions frequently.
                await page.wait_for_function(
                    profile_script,
                    arg=clean_user,
                    timeout=min(1000, remaining_ms),
                    polling=250,
                )

                logger.info("Datos del perfil de @%s disponibles.", clean_user)
                return True

            except (AccessRestricted, IdentityError):
                raise
            except PlaywrightTimeoutError:
                # The profile payload is not ready yet; check again.
                continue
            except Exception:
                logger.exception(
                    "Error esperando los datos del perfil de @%s.",
                    clean_user,
                )
                return False

        logger.warning(
            "Tiempo agotado esperando el perfil de @%s.",
            clean_user,
        )
        return False

    async def _read_profile_data(
        self,
        page: Page,
        username: str,
    ) -> Optional[Dict[str, Any]]:
        """Read and validate the profile payload embedded in the page."""

        ready = await self._wait_for_profile_data(page, username)
        if not ready:
            return None

        script_el = await page.query_selector(
            "script#__UNIVERSAL_DATA_FOR_REHYDRATION__"
        )
        if not script_el:
            return None

        content = await script_el.text_content()

        try:
            raw_data = json.loads(content or "{}")
        except json.JSONDecodeError:
            logger.error("No se pudieron interpretar los datos del perfil.")
            return None

        user_detail = (
            raw_data.get("__DEFAULT_SCOPE__", {})
            .get("webapp.user-detail", {})
        )

        status_code = user_detail.get("statusCode", 0)
        if status_code != 0:
            logger.warning(
                "TikTok devolvió statusCode=%s para @%s.",
                status_code,
                username,
            )
            return None

        user_info = user_detail.get("userInfo", {})
        user = user_info.get("user", {})

        if not isinstance(user, dict) or not user.get("uniqueId"):
            return None

        return user_info

    async def scrape(
        self,
        username: str,
        max_list_items: int = 30,
        max_videos: int = 10,
        max_comments_per_video: int = 20,
    ) -> Dict[str, Any]:
        """Extract profile data, lists, recent videos and comments."""

        clean_user = username.strip().lstrip("@")

        if not clean_user:
            return {
                "success": False,
                "error": "Debes proporcionar un nombre de usuario.",
                "username": username,
            }

        if not USERNAME_PATTERN.fullmatch(clean_user):
            return {
                "success": False,
                "error": "El nombre de usuario no tiene un formato válido.",
                "username": clean_user,
            }

        profile_url = f"https://www.tiktok.com/@{clean_user}"
        followers_list: List[Dict[str, Any]] = []
        following_list: List[Dict[str, Any]] = []

        self._profile_owner = {}
        self._active_scene = None
        self._list_status = {
            "67": "not_observed",
            "21": "not_observed",
        }

        async with persistent_playwright(self) as playwright:
            browser, context = await self._setup_context(playwright)
            page = await context.new_page()
            following_private = False

            async def intercept_user_list(response) -> None:
                nonlocal followers_list, following_list, following_private

                if not user_response_matches(
                    response,
                    self._profile_owner,
                    self._active_scene,
                ):
                    return

                try:
                    data = await response.json()

                    if not user_data_matches(data, self._profile_owner):
                        return

                    status_code = data.get(
                        "statusCode",
                        data.get("status_code", 0),
                    )

                    if status_code == 10222:
                        self._list_status[self._active_scene] = "private"
                        following_private = self._active_scene == "21"
                        return

                    if type(status_code) is not int or status_code != 0:
                        self._list_status[self._active_scene] = "unavailable"
                        return

                    self._list_status[self._active_scene] = "partial"
                    items = data.get("userList", [])
                    if not items:
                        return

                    parsed: List[Dict[str, Any]] = []

                    for item in items:
                        user_data = item.get("user", {})
                        if not isinstance(user_data, dict):
                            continue

                        unique_id = user_data.get("uniqueId") or ""
                        if not USERNAME_PATTERN.fullmatch(unique_id):
                            continue

                        stats = item.get("stats", {})
                        parsed.append(
                            {
                                "username": unique_id,
                                "nickname": user_data.get("nickname"),
                                "avatar_url": (
                                    user_data.get("avatarThumb")
                                    or user_data.get("avatarMedium")
                                ),
                                "followers_count": stats.get(
                                    "followerCount", 0
                                ),
                                "following_count": stats.get(
                                    "followingCount", 0
                                ),
                                "verified": user_data.get("verified", False),
                                "sec_uid": user_data.get("secUid", ""),
                            }
                        )

                    scene_match = re.search(
                        r"[?&]scene=(\d+)", response.url
                    )
                    scene = scene_match.group(1) if scene_match else ""

                    destination = (
                        followers_list if scene == "67"
                        else following_list if scene == "21"
                        else None
                    )

                    if destination is not None:
                        known = {
                            entry["username"] for entry in destination
                        }
                        for user_data in parsed:
                            if user_data["username"] not in known:
                                destination.append(user_data)
                                known.add(user_data["username"])

                except (AccessRestricted, IdentityError):
                    raise
                except Exception:
                    logger.debug(
                        "No se pudo procesar una respuesta de listas.",
                        exc_info=True,
                    )

            page.on("response", intercept_user_list)

            logger.info("Navegando al perfil: %s", profile_url)

            try:
                await page.goto(
                    profile_url,
                    wait_until="domcontentloaded",
                    timeout=35000,
                )
            except (AccessRestricted, IdentityError):
                raise
            except PlaywrightTimeoutError:
                logger.warning(
                    "La navegación inicial agotó su tiempo. "
                    "Se comprobará si el perfil terminó de cargar."
                )
            except Exception as error:
                logger.exception("Error cargando el perfil de TikTok.")
                await browser.close()
                return {
                    "success": False,
                    "error": (
                        "Error cargando la página de TikTok: "
                        f"{str(error)}"
                    ),
                    "username": clean_user,
                }

            user_info = await self._read_profile_data(page, clean_user)

            if not user_info:
                await browser.close()
                return {
                    "success": False,
                    "error": (
                        f"No se pudo acceder al perfil de @{clean_user}. "
                        "Comprueba si TikTok solicita una verificación, "
                        "si el usuario existe o si el acceso está restringido."
                    ),
                    "username": clean_user,
                }

            user = user_info.get("user", {})
            self._profile_owner = verified_profile(user, clean_user)

            stats = user_info.get("stats", {})
            stats_v2 = user_info.get("statsV2", {})

            def _parse_stat(key: str, default=None):
                value = stats_v2.get(key)
                if value is not None:
                    try:
                        return checked_int(value)
                    except (ValueError, TypeError):
                        pass

                number = stats.get(key, default)
                if isinstance(number, int) and number < 0:
                    return number + (1 << 32)

                try:
                    return checked_int(number)
                except (ValueError, TypeError):
                    return default

            bio_link_value = ""
            bio_link = user.get("bioLink", {})
            if isinstance(bio_link, dict):
                bio_link_value = bio_link.get("link", "")

            commerce_info = user.get("commerceUserInfo", {}) or {}
            is_commerce = (
                bool(commerce_info.get("commerceUser", False))
                if isinstance(commerce_info, dict)
                else False
            )

            profile_data: Dict[str, Any] = {
                "success": True,
                "username": user.get("uniqueId", clean_user),
                "nickname": user.get("nickname", ""),
                "avatar_url": (
                    user.get("avatarLarger")
                    or user.get("avatarMedium")
                    or user.get("avatarThumb", "")
                ),
                "followers_count": _parse_stat("followerCount"),
                "following_count": _parse_stat("followingCount"),
                "heart_count": first_known(
                    _parse_stat("heartCount"),
                    _parse_stat("heart"),
                ),
                "video_count": _parse_stat("videoCount"),
                "bio": user.get("signature", ""),
                "bio_link": bio_link_value,
                "is_commerce_user": is_commerce,
                "region": user.get("region", ""),
                "verified": user.get("verified", False),
                "private_account": user.get("privateAccount", False),
                "sec_uid": user.get("secUid", ""),
                "user_id": user.get("id", ""),
                "requires_login_for_lists": None,
                "following_list": [],
                "followers_list": [],
                "videos": [],
                "note": "",
            }

            # -------------------------------------------------
            # FOLLOWERS / FOLLOWING
            # -------------------------------------------------
            if self._profile_owner and max_list_items > 0:
                # Followers
                try:
                    self._active_scene = "67"
                    followers_btn = await page.query_selector(
                        'strong[data-e2e="followers-count"]'
                    )

                    if followers_btn:
                        await followers_btn.click(timeout=5000)
                        await asyncio.sleep(2)

                        max_scrolls = max(6, (max_list_items // 10) + 3)
                        no_new_count = 0
                        previous_length = len(followers_list)

                        for _ in range(max_scrolls):
                            if len(followers_list) >= max_list_items:
                                break

                            await page.evaluate(
                                """() => {
                                    const modal = document.querySelector(
                                        'div[class*="DivUserListContainer"], '
                                        + 'div[role="dialog"] div[class*="ScrollContainer"], '
                                        + '[data-e2e="user-list-item"]'
                                    );
                                    if (modal) {
                                        const scrollable = modal.closest(
                                            'div[style*="overflow"], '
                                            + 'div[class*="Scroll"]'
                                        ) || modal.parentElement;
                                        if (scrollable) {
                                            scrollable.scrollTop += 1500;
                                            scrollable.dispatchEvent(
                                                new Event('scroll', { bubbles: true })
                                            );
                                        }
                                    }
                                }"""
                            )
                            await page.mouse.move(640, 450)
                            await page.mouse.wheel(0, 1000)
                            await asyncio.sleep(random.uniform(0.8, 1.3))

                            if len(followers_list) == previous_length:
                                no_new_count += 1
                                if no_new_count >= 5:
                                    break
                            else:
                                no_new_count = 0
                                previous_length = len(followers_list)

                        await page.keyboard.press("Escape")
                        await asyncio.sleep(1)

                except (AccessRestricted, IdentityError):
                    raise
                except Exception as error:
                    logger.warning(
                        "Aviso al extraer seguidores: %s",
                        type(error).__name__,
                    )

                # Following
                try:
                    self._active_scene = "21"
                    following_btn = await page.query_selector(
                        'strong[data-e2e="following-count"]'
                    )

                    if following_btn:
                        await following_btn.click(timeout=5000)
                        await asyncio.sleep(2)

                        max_scrolls = max(6, (max_list_items // 10) + 3)
                        no_new_count = 0
                        previous_length = len(following_list)

                        for _ in range(max_scrolls):
                            if len(following_list) >= max_list_items:
                                break

                            await page.evaluate(
                                """() => {
                                    const modal = document.querySelector(
                                        'div[class*="DivUserListContainer"], '
                                        + 'div[role="dialog"] div[class*="ScrollContainer"], '
                                        + '[data-e2e="user-list-item"]'
                                    );
                                    if (modal) {
                                        const scrollable = modal.closest(
                                            'div[style*="overflow"], '
                                            + 'div[class*="Scroll"]'
                                        ) || modal.parentElement;
                                        if (scrollable) {
                                            scrollable.scrollTop += 1500;
                                            scrollable.dispatchEvent(
                                                new Event('scroll', { bubbles: true })
                                            );
                                        }
                                    }
                                }"""
                            )
                            await page.mouse.move(640, 450)
                            await page.mouse.wheel(0, 1000)
                            await asyncio.sleep(random.uniform(0.8, 1.3))

                            if len(following_list) == previous_length:
                                no_new_count += 1
                                if no_new_count >= 5:
                                    break
                            else:
                                no_new_count = 0
                                previous_length = len(following_list)

                        await page.keyboard.press("Escape")
                        await asyncio.sleep(0.5)

                except (AccessRestricted, IdentityError):
                    raise
                except Exception as error:
                    logger.warning(
                        "Aviso al extraer seguidos: %s",
                        type(error).__name__,
                    )

            elif not self._profile_owner:
                profile_data["note"] = (
                    "TikTok requiere una sesión válida para listar "
                    "usuarios individuales de seguidores/seguidos."
                )

            self._active_scene = None
            profile_data["list_status"] = dict(self._list_status)
            profile_data["following_list"] = following_list[:max_list_items]
            profile_data["followers_list"] = followers_list[:max_list_items]
            profile_data["following_list_private"] = following_private

            page.remove_listener("response", intercept_user_list)

            # -------------------------------------------------
            # VIDEOS
            # -------------------------------------------------
            if max_videos > 0:
                await page.close()

                logger.info(
                    "Buscando los últimos %s videos de @%s...",
                    max_videos,
                    clean_user,
                )

                video_urls = await self._extract_video_urls(
                    browser,
                    clean_user,
                    max_videos,
                )

                logger.info(
                    "Se encontraron %s URLs de videos.",
                    len(video_urls),
                )

                videos_data: List[Dict[str, Any]] = []

                for index, video_url in enumerate(video_urls, 1):
                    logger.info(
                        "Extrayendo métricas y comentarios [%s/%s]: %s",
                        index,
                        len(video_urls),
                        video_url,
                    )

                    video_context = None
                    try:
                        video_context = await browser.new_context(
                            viewport={"width": 1280, "height": 800},
                            locale="es-ES",
                        )

                        video_info = await self._extract_single_video_details(
                            context=video_context,
                            video_url=video_url,
                            max_comments=max_comments_per_video,
                        )
                        videos_data.append(video_info)

                    except (AccessRestricted, IdentityError):
                        raise
                    except Exception as error:
                        logger.exception(
                            "Error extrayendo video: %s",
                            video_url,
                        )
                        videos_data.append(
                            {
                                "video_url": video_url,
                                "error": str(error),
                                "comments": [],
                            }
                        )
                    finally:
                        if video_context is not None:
                            try:
                                await video_context.close()
                            except Exception:
                                logger.warning(
                                    "No se pudo cerrar el contexto del video."
                                )

                profile_data["videos"] = videos_data

            await browser.close()
            return profile_data

    async def _extract_video_urls(
        self,
        browser: Any,
        username: str,
        max_videos: int,
    ) -> List[str]:
        """Collect recent video URLs from the requested profile."""

        raw_urls: List[str] = []
        clean_user = username.strip().lstrip("@").lower()
        profile_url = f"https://www.tiktok.com/@{clean_user}"

        ctx = None

        try:
            ctx = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="es-ES",
            )
            page = await ctx.new_page()

            logger.info("Abriendo nuevamente el perfil de @%s...", clean_user)

            try:
                await page.goto(
                    profile_url,
                    wait_until="domcontentloaded",
                    timeout=35000,
                )
            except (AccessRestricted, IdentityError):
                raise
            except PlaywrightTimeoutError:
                logger.warning(
                    "La navegación del perfil tardó demasiado. "
                    "Se comprobará si terminó de cargar."
                )

            profile_ready = await self._wait_for_profile_data(
                page,
                clean_user,
            )

            if not profile_ready:
                logger.error(
                    "No se pudo cargar el perfil de @%s para extraer videos.",
                    clean_user,
                )
                return []

            logger.info("Perfil disponible. Extrayendo URLs de videos...")
            scroll_count = max(4, (max_videos // 3) + 3)

            for _ in range(scroll_count):
                if len(raw_urls) >= max_videos:
                    break

                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(1.2)

                links = await page.evaluate(
                    """() => Array.from(
                        document.querySelectorAll('a')
                    ).map(a => a.href)"""
                )

                for link in links:
                    base = link.split("?")[0]
                    try:
                        author_name, kind, _ = publication_url(base)
                        is_user_video = (
                            author_name.casefold() == clean_user
                            and kind == "video"
                        )
                    except IdentityError:
                        is_user_video = False

                    if is_user_video and base not in raw_urls:
                        raw_urls.append(base)

                logger.info(
                    "Videos encontrados: %s/%s",
                    len(raw_urls),
                    max_videos,
                )

            def get_video_id(url: str) -> int:
                match = re.search(r"/video/(\d+)", url)
                return int(match.group(1)) if match else 0

            unique_urls = list(dict.fromkeys(raw_urls))
            sorted_urls = sorted(
                unique_urls,
                key=get_video_id,
                reverse=True,
            )
            result = sorted_urls[:max_videos]

            logger.info(
                "Extracción finalizada: %s videos.",
                len(result),
            )
            return result

        except (AccessRestricted, IdentityError):
            raise
        except Exception:
            logger.exception(
                "Error extrayendo URLs de videos de @%s.",
                clean_user,
            )
            return []
        finally:
            if ctx is not None:
                try:
                    await ctx.close()
                except Exception:
                    logger.warning(
                        "No se pudo cerrar el contexto del perfil."
                    )

    async def _extract_single_video_details(
        self,
        context: BrowserContext,
        video_url: str,
        max_comments: int = 20,
    ) -> Dict[str, Any]:
        """Extract video metadata, interaction counts and public comments."""

        page = await context.new_page()
        captured_comments: List[Dict[str, Any]] = []

        async def intercept_comments(response) -> None:
            nonlocal captured_comments

            if not comment_response_matches(response, video_url):
                return

            try:
                response_text = await response.text()
                if not response_text:
                    return

                data = json.loads(response_text)
                if not comment_data_matches(data, video_url):
                    return

                raw_comments = data.get("comments", []) or []
                logger.info(
                    "API de comentarios interceptada: %s comentarios.",
                    len(raw_comments),
                )

                for comment in raw_comments:
                    if not valid_comment(comment, video_url):
                        continue

                    user = comment.get("user", {}) or {}
                    comment_id = str(comment.get("cid", ""))

                    if comment_already_captured(captured_comments, comment):
                        continue

                    created_ts = comment.get("create_time")
                    date_string = ""
                    if created_ts:
                        try:
                            date_string = datetime.fromtimestamp(
                                created_ts,
                                tz=timezone.utc,
                            ).strftime("%Y-%m-%d %H:%M:%S UTC")
                        except (AccessRestricted, IdentityError):
                            raise
                        except Exception:
                            pass

                    author_user = (
                        user.get("unique_id", "")
                        or user.get("uniqueId", "")
                    )
                    author_nick = user.get("nickname", "")
                    avatar_obj = user.get("avatar_thumb", {})
                    author_avatar = (
                        avatar_obj.get("url_list", [""])[0]
                        if isinstance(avatar_obj, dict)
                        and avatar_obj.get("url_list")
                        else ""
                    )

                    captured_comments.append(
                        {
                            "comment_id": comment_id,
                            "username": author_user,
                            "nickname": author_nick,
                            "avatar_url": author_avatar,
                            "text": comment.get("text", ""),
                            "likes_count": comment.get("digg_count"),
                            "replies_count": comment.get(
                                "reply_comment_total"
                            ),
                            "author_liked": bool(
                                comment.get("is_author_digged", False)
                            ),
                            "is_pinned": bool(
                                comment.get("is_pinned", False)
                            ),
                            "create_time": created_ts,
                            "date": date_string,
                        }
                    )

            except (AccessRestricted, IdentityError):
                raise
            except Exception:
                logger.exception("Error procesando comentarios interceptados.")

        page.on("response", intercept_comments)

        video_info: Dict[str, Any] = {
            "video_id": "",
            "video_url": video_url,
            "description": "",
            "create_time": None,
            "date": "",
            "duration": 0,
            "hashtags": [],
            "cover_image_url": "",
            "is_ad": False,
            "likes_count": None,
            "comments_count": None,
            "views_count": None,
            "shares_count": None,
            "bookmarks_count": None,
            "music_title": "",
            "music_author": "",
            "comments": [],
        }

        try:
            await page.goto(
                video_url,
                wait_until="domcontentloaded",
                timeout=25000,
            )
            await asyncio.sleep(2.5)

        except (AccessRestricted, IdentityError):
            raise
        except Exception as error:
            logger.warning(
                "Error navegando al video %s: %s",
                video_url,
                type(error).__name__,
            )
            await page.close()
            return {
                "video_url": video_url,
                "error": str(error),
                "comments": [],
            }

        # -------------------------------------------------
        # VIDEO PAYLOAD
        # -------------------------------------------------
        try:
            element = await page.wait_for_selector(
                "script#__UNIVERSAL_DATA_FOR_REHYDRATION__",
                state="attached",
                timeout=12000,
            )

            if element:
                content = await element.text_content()
                data = json.loads(content or "{}")
                detail = (
                    data.get("__DEFAULT_SCOPE__", {})
                    .get("webapp.video-detail", {})
                )
                item = (
                    detail.get("itemInfo", {})
                    .get("itemStruct", {})
                )

                verified_publication(
                    item,
                    video_url,
                    self._profile_owner,
                )

                video_info["_verified"] = True
                video_info["author"] = item.get("author")
                stats = metric_dict(item)

                def to_int(value):
                    try:
                        return checked_int(value)
                    except (ValueError, TypeError):
                        return None

                created_time = to_int(item.get("createTime", 0))
                date_string = ""
                if created_time:
                    try:
                        date_string = datetime.fromtimestamp(
                            created_time,
                            tz=timezone.utc,
                        ).strftime("%Y-%m-%d %H:%M:%S UTC")
                    except (AccessRestricted, IdentityError):
                        raise
                    except Exception:
                        pass

                video_info["video_id"] = str(item.get("id", ""))
                video_info["description"] = item.get("desc", "")
                video_info["create_time"] = created_time
                video_info["date"] = date_string
                video_info["likes_count"] = to_int(
                    stats.get("diggCount")
                )
                video_info["comments_count"] = to_int(
                    stats.get("commentCount")
                )
                video_info["views_count"] = to_int(
                    stats.get("playCount")
                )
                video_info["shares_count"] = to_int(
                    stats.get("shareCount")
                )
                video_info["bookmarks_count"] = to_int(
                    stats.get("collectCount")
                )

                video_struct = item.get("video", {})
                video_info["duration"] = to_int(
                    video_struct.get("duration", 0)
                )
                video_info["cover_image_url"] = (
                    video_struct.get("cover", "")
                    or video_struct.get("dynamicCover", "")
                )
                video_info["is_ad"] = bool(item.get("isAd", False))

                challenges = item.get("challenges", []) or []
                extracted_tags = [
                    challenge.get("title")
                    for challenge in challenges
                    if isinstance(challenge, dict)
                    and challenge.get("title")
                ]

                if not extracted_tags and video_info["description"]:
                    extracted_tags = re.findall(
                        r"#(\w+)",
                        video_info["description"],
                    )

                video_info["hashtags"] = extracted_tags
                music = item.get("music", {})
                video_info["music_title"] = music.get("title", "")
                video_info["music_author"] = music.get("authorName", "")

        except (AccessRestricted, IdentityError):
            raise
        except Exception:
            logger.exception(
                "Error interpretando los datos internos del video."
            )

        if not video_info["video_id"]:
            match = re.search(r"/video/(\d+)", video_url)
            if match:
                video_info["video_id"] = match.group(1)

        # -------------------------------------------------
        # COMMENTS
        # -------------------------------------------------
        try:
            await validate_access(page)
            btn = None

            if max_comments > 0:
                btn = await page.wait_for_selector(
                    '[data-e2e="comment-icon"], '
                    '[data-e2e="comment-count"], '
                    'button[class*="tux"]:has-text("Comentarios"), '
                    'button[class*="tux"]:has-text("Comments")',
                    timeout=5000,
                )

            if btn:
                logger.info("Botón de comentarios encontrado.")
                try:
                    await btn.click(timeout=3000)
                except (AccessRestricted, IdentityError):
                    raise
                except Exception:
                    logger.warning(
                        "No se pudo abrir el panel de comentarios."
                    )

                await asyncio.sleep(1.5)
                max_scrolls = max(6, (max_comments // 8) + 4)
                no_new_comments = 0
                previous_length = len(captured_comments)

                for _ in range(max_scrolls):
                    if len(captured_comments) >= max_comments:
                        break

                    await page.evaluate(
                        """() => {
                            const containers = document.querySelectorAll(
                                '[data-e2e="comment-list"], '
                                + 'div[class*="CommentList"], '
                                + 'div[class*="DivCommentListContainer"], '
                                + 'div[class*="CommentItemContainer"]'
                            );
                            for (const container of containers) {
                                container.scrollTop += 1800;
                                container.dispatchEvent(
                                    new Event('scroll', { bubbles: true })
                                );
                            }
                        }"""
                    )
                    await page.mouse.move(950, 450)
                    await page.mouse.wheel(0, 1000)
                    await asyncio.sleep(random.uniform(0.9, 1.4))

                    if len(captured_comments) == previous_length:
                        no_new_comments += 1
                        if no_new_comments >= 5:
                            break
                    else:
                        no_new_comments = 0
                        previous_length = len(captured_comments)

            if not captured_comments and max_comments > 0:
                tab_btn = await page.query_selector(
                    'button[class*="tux"]:has-text("Comentarios"), '
                    'button[class*="tux"]:has-text("Comments")'
                )

                if tab_btn:
                    try:
                        await tab_btn.click(timeout=3000)
                    except (AccessRestricted, IdentityError):
                        raise
                    except Exception:
                        logger.warning(
                            "No se pudo abrir la pestaña de comentarios."
                        )

                    await asyncio.sleep(1.5)
                    max_scrolls = max(6, (max_comments // 8) + 3)
                    no_new_comments = 0
                    previous_length = len(captured_comments)

                    for _ in range(max_scrolls):
                        if len(captured_comments) >= max_comments:
                            break

                        await page.evaluate(
                            """() => {
                                const containers = document.querySelectorAll(
                                    '[data-e2e="comment-list"], '
                                    + 'div[class*="CommentList"], '
                                    + 'div[class*="DivCommentListContainer"]'
                                );
                                for (const container of containers) {
                                    container.scrollTop += 1800;
                                    container.dispatchEvent(
                                        new Event('scroll', { bubbles: true })
                                    );
                                }
                            }"""
                        )
                        await page.mouse.move(950, 450)
                        await page.mouse.wheel(0, 1000)
                        await asyncio.sleep(random.uniform(0.9, 1.4))

                        if len(captured_comments) == previous_length:
                            no_new_comments += 1
                            if no_new_comments >= 5:
                                break
                        else:
                            no_new_comments = 0
                            previous_length = len(captured_comments)

        except (AccessRestricted, IdentityError):
            raise
        except Exception:
            logger.warning(
                "Aviso al extraer comentarios.",
                exc_info=True,
            )

        # -------------------------------------------------
        # DOM COMMENTS FALLBACK
        # -------------------------------------------------
        if len(captured_comments) < max_comments:
            try:
                dom_comments = await page.evaluate(
                    r"""() => {
                        const list = [];
                        const items = document.querySelectorAll(
                            '[data-e2e="comment-item"], '
                            + 'div[class*="DivCommentItemContainer"], '
                            + 'div[class*="CommentItem"]'
                        );

                        for (const el of items) {
                            const own = node => (
                                node && node.closest(
                                    '[data-e2e="comment-item"], '
                                    + 'div[class*="DivCommentItemContainer"], '
                                    + 'div[class*="CommentItem"]'
                                ) === el
                            );

                            const userEl = el.querySelector(
                                '[data-e2e="comment-username"], '
                                + 'a[href*="/@"], '
                                + 'span[class*="SpanUserName"]'
                            );
                            const textEl = el.querySelector(
                                '[data-e2e="comment-level-1"], '
                                + 'p[class*="PCommentText"], '
                                + 'span[class*="SpanCommentText"]'
                            );
                            const likeEl = el.querySelector(
                                '[data-e2e="comment-like-count"], '
                                + 'span[class*="SpanCount"]'
                            );
                            const anchor = (
                                userEl?.closest('a[href]')
                                || userEl?.querySelector('a[href]')
                            );

                            let username = "";
                            if (anchor && el.contains(anchor) && own(anchor)) {
                                try {
                                    const url = new URL(
                                        anchor.getAttribute('href'),
                                        'https://www.tiktok.com'
                                    );
                                    const match = url.pathname.match(
                                        /^\/@([A-Za-z0-9._]{1,24})\/?$/
                                    );
                                    if (
                                        url.protocol === 'https:'
                                        && ['www.tiktok.com', 'tiktok.com']
                                            .includes(url.hostname)
                                        && match
                                    ) {
                                        username = match[1];
                                    }
                                } catch (_) {}
                            }

                            if (
                                own(textEl)
                                && username
                                && textEl.innerText.trim()
                            ) {
                                list.push({
                                    username,
                                    text: textEl.innerText.trim(),
                                    likes_text: likeEl
                                        ? likeEl.innerText.trim()
                                        : "0"
                                });
                            }
                        }
                        return list;
                    }"""
                )

                for comment in dom_comments:
                    username = comment.get("username", "")
                    comment_text = comment.get("text", "")

                    already_exists = any(
                        existing["text"] == comment_text
                        and existing["username"].casefold()
                        == username.casefold()
                        for existing in captured_comments
                    )

                    if (
                        not already_exists
                        and USERNAME_PATTERN.fullmatch(username)
                    ):
                        captured_comments.append(
                            {
                                "comment_id": "",
                                "username": username,
                                "nickname": username,
                                "avatar_url": "",
                                "text": comment_text,
                                "likes_count": None,
                                "replies_count": None,
                                "create_time": None,
                                "date": "",
                            }
                        )

            except (AccessRestricted, IdentityError):
                raise
            except Exception:
                logger.debug(
                    "No se pudieron recuperar comentarios desde el DOM.",
                    exc_info=True,
                )

        page.remove_listener("response", intercept_comments)
        await page.close()
        video_info["comments"] = captured_comments[:max_comments]
        return video_info


def scrape_tiktok_user(
    username: str,
    session_id: Optional[str] = None,
    max_videos: int = 10,
    max_comments: int = 20,
) -> Dict[str, Any]:
    """Run the scraper from synchronous code."""

    scraper = TikTokScraper(session_id=session_id)
    return asyncio.run(
        scraper.scrape(
            username,
            max_videos=max_videos,
            max_comments_per_video=max_comments,
        )
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    user_to_test = sys.argv[1] if len(sys.argv) > 1 else "tiktok"
    print(f"Probando scraper completo para: @{user_to_test}...")

    result = scrape_tiktok_user(
        user_to_test,
        max_videos=3,
        max_comments=5,
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )
