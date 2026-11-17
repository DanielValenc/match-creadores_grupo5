
# Origen: media-scraper, rama feature/setup-inicial,
# commit a3ef81d2e533d0c9e58e144ee6c4c863a43961cc.
# Adaptador entre el motor SCRAPINGTIKTOK y el modelo interno de TrueMatch.

from time import time

from .runtime import (
    USERNAME,
    IdentityError,
    checked_int,
    publication_url,
    verified_profile,
)

UPSTREAM_COMMIT = '7deb6d0189f8b05d2f4e7d4ea7292b616258c205'


def metric(value):
    try:
        return checked_int(value)
    except (ValueError, TypeError):
        return None


def timestamp(value):
    value = metric(value)

    return (
        value
        if value is not None and 1451606400 <= value <= time() + 300
        else None
    )


def usernames(values):
    result = []
    seen = set()

    for value in values or []:
        name = value.get('username') if isinstance(value, dict) else None

        if (
            isinstance(name, str)
            and USERNAME.fullmatch(name)
            and name.casefold() not in seen
        ):
            seen.add(name.casefold())
            result.append(name)

    return result


def adapt_profile(raw, requested, max_videos=10):
    """
    Adapta la respuesta original de SCRAPINGTIKTOK.

    IMPORTANTE:
    Ahora muestra el motivo real cuando TikTok no permite
    completar la extracción.
    """

    # Comprobar que la respuesta sea válida.
    if not isinstance(raw, dict):
        raise RuntimeError(
            "TikTok devolvió una respuesta inválida al extraer el perfil."
        )

    # Mostrar el error real del motor en lugar de ocultarlo.
    if raw.get('success') is not True:
        reason = raw.get('error')

        if not isinstance(reason, str) or not reason.strip():
            reason = "TikTok no devolvió información del perfil."

        reason = " ".join(reason.split())[:400]

        raise RuntimeError(
            "El motor SCRAPINGTIKTOK no pudo completar la extracción. "
            f"Motivo: {reason}"
        )

    # Validar que el perfil corresponda al usuario solicitado.
    owner = verified_profile(
        {
            'uniqueId': raw.get('username'),
            'id': raw.get('user_id'),
            'secUid': raw.get('sec_uid'),
        },
        requested,
    )

    warnings = [
        'Motor original: selección de candidatos por ID; '
        'no se garantiza la cronología completa del perfil.'
    ]

    # Datos generales del perfil.
    profile = {
        'username': raw['username'],
        'url': f"https://www.tiktok.com/@{raw['username']}",
        'nickname': raw.get('nickname'),
        'bio': raw.get('bio'),
        'avatar_url': raw.get('avatar_url'),

        'followers': metric(raw.get('followers_count')),
        'following': metric(raw.get('following_count')),
        'likes': metric(raw.get('heart_count')),

        'followers_users': usernames(raw.get('followers_list')),
        'following_users': usernames(raw.get('following_list')),

        'videos': [],
    }

    if owner.get('id'):
        profile['id'] = owner['id']

    if owner.get('secUid'):
        profile['secUid'] = owner['secUid']

    if raw.get('private_account'):
        warnings.append(
            'El perfil informa restricciones de privacidad; '
            'solo se conserva contenido accesible.'
        )

    # Advertencias de las listas de seguidores y seguidos.
    list_status = raw.get('list_status') or {}

    for scene, name in (
        ('67', 'seguidores'),
        ('21', 'seguidos'),
    ):
        state = list_status.get(scene, 'not_observed')

        warnings.append(
            f'Lista {name}: {state}; '
            'no se infiere una lista vacía ni completa.'
        )

    # Procesar publicaciones.
    seen = set()

    for entry in raw.get('videos') or []:

        if not isinstance(entry, dict) or entry.get('_verified') is not True:
            warnings.append(
                'Publicación omitida: faltan datos verificables '
                'o falló su acceso.'
            )
            continue

        username, kind, publication_id = publication_url(
            entry.get('video_url', '')
        )

        allowed_owners = {
            str(value).casefold()
            for value in owner.values()
        }

        if (
            str(entry.get('video_id')) != publication_id
            or username.casefold() not in allowed_owners
        ):
            raise IdentityError(
                'El resultado no corresponde al perfil '
                'o publicación solicitados.'
            )

        if publication_id in seen:
            continue

        seen.add(publication_id)

        video = {
            'id': publication_id,
            'url': entry['video_url'],
            'type': kind,

            'title': entry.get('description'),
            'preview_url': entry.get('cover_image_url'),

            'views': metric(entry.get('views_count')),
            'likes': metric(entry.get('likes_count')),
            'comments': metric(entry.get('comments_count')),
            'shares': metric(entry.get('shares_count')),
            'saves': metric(entry.get('bookmarks_count')),

            'comments_list': [],
            'created_at': timestamp(entry.get('create_time')),

            'author': dict(owner),
        }

        # Procesar comentarios.
        comment_ids = set()
        identities = set()

        for comment in entry.get('comments') or []:

            if not isinstance(comment, dict):
                continue

            name = comment.get('username')
            text = comment.get('text')

            if (
                not isinstance(name, str)
                or not USERNAME.fullmatch(name)
                or not isinstance(text, str)
                or not text.strip()
            ):
                continue

            cid = comment.get('comment_id')

            cid = (
                str(cid)
                if (
                    cid is not None
                    and not isinstance(cid, bool)
                    and str(cid).isdigit()
                )
                else None
            )

            identity = (name.casefold(), text.strip())

            if (
                (cid is not None and cid in comment_ids)
                or (cid is None and identity in identities)
            ):
                continue

            result = {
                'username': name,
                'text': text.strip(),
            }

            if cid is not None:
                result['cid'] = cid
                comment_ids.add(cid)

            identities.add(identity)

            for source, target in (
                ('create_time', 'create_time'),
                ('likes_count', 'digg_count'),
                ('replies_count', 'reply_comment_total'),
            ):
                value = (
                    timestamp(comment.get(source))
                    if source == 'create_time'
                    else metric(comment.get(source))
                )

                if value is not None:
                    result[target] = value

            video['comments_list'].append(result)

        profile['videos'].append(video)

    # Ordenar las publicaciones por fecha, cuando sea posible.
    if profile['videos'] and all(
        video['created_at'] is not None
        for video in profile['videos']
    ):
        profile['videos'].sort(
            key=lambda video: video['created_at'],
            reverse=True,
        )

    # Registrar si el resultado fue parcial.
    if len(profile['videos']) < max_videos:
        warnings.append(
            f"Resultado parcial: {len(profile['videos'])} "
            f"publicaciones verificadas de hasta {max_videos}."
        )

    recovered = sum(
        len(video['comments_list'])
        for video in profile['videos']
    )

    warnings.append(
        f'Comentarios recuperados: {recovered}; '
        'no se confirma la completitud ni ausencia mediante contadores.'
    )

    profile['_meta'] = {
        'mode': 'real',
        'engine': 'SCRAPINGTIKTOK',
        'upstream_commit': UPSTREAM_COMMIT,
        'warnings': list(dict.fromkeys(warnings)),
    }

    return profile
