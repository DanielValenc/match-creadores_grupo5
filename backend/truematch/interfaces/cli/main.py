"""Línea de comandos de TrueMatch AI.

Uso (desde la carpeta backend/):
    python -m truematch.interfaces.cli.main session                      # inicio de sesión manual en Chromium
    python -m truematch.interfaces.cli.main analyze <usuario>            # extracción + Big Five + auditoría
    python -m truematch.interfaces.cli.main analyze <usuario> --sin-analisis
    python -m truematch.interfaces.cli.main bigfive <usuario> [...]      # Big Five sobre datos ya extraídos
    python -m truematch.interfaces.cli.main bigfive --todos
    python -m truematch.interfaces.cli.main bigfive --listar-modelos
    python -m truematch.interfaces.cli.main audit <usuario>              # auditoría sobre datos ya extraídos
    python -m truematch.interfaces.cli.main web                          # dashboard en http://127.0.0.1:5000

Los imports de cada comando son diferidos: --help funciona aunque falte alguna dependencia.
"""
import argparse
import logging

CLI = "python -m truematch.interfaces.cli.main"


def run_session():
    from truematch.infrastructure.tiktok.session import configure_session

    configure_session()
    print("Sesión local guardada. TikTok puede solicitar autenticación de nuevo.")


def run_analyze(username, with_personality=True):
    """Caso de uso AnalyzeCreator: TikTok → auditoría → personalidad (opcional) → datos_<usuario>.json."""
    from truematch.application.use_cases.analyze_creator import AnalyzeCreator
    from truematch.domain.creator_profiling.username import Username
    from truematch.infrastructure.ai.groq_client import GroqClient
    from truematch.infrastructure.ai.groq_personality_analyzer import GroqPersonalityAnalyzer
    from truematch.infrastructure.config import load_settings
    from truematch.infrastructure.persistence.legacy_json_repository import LegacyJsonCreatorRepository
    from truematch.infrastructure.tiktok.tiktok_creator_source import MAX_VIDEOS, TikTokCreatorSource
    from truematch.interfaces.cli.formatting import audit_line, creator_summary, personality_line

    settings = load_settings()
    user = Username.parse(username)
    analyzer = None
    if with_personality:
        # Sin GROQ_API_KEY, ConfigError termina el comando antes de abrir TikTok.
        analyzer = GroqPersonalityAnalyzer(GroqClient(settings.require_groq_api_key(), settings.groq_model))

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(f"\nIniciando extracción para: @{user} (motor SCRAPINGTIKTOK, hasta {MAX_VIDEOS} videos)")
    use_case = AnalyzeCreator(TikTokCreatorSource(), LegacyJsonCreatorRepository(settings.data_dir), analyzer)
    try:
        result = use_case.execute(user)
    except Exception as error:
        print("\nError: no se pudo extraer el perfil.")
        print(f"Detalle: {error}")
        print(f"Si TikTok pide verificación o inicio de sesión, ejecuta: {CLI} session")
        raise SystemExit(1) from None

    print(f"\n¡ÉXITO! Se extrajeron {len(result.creator.videos)} videos. Archivo: {result.location}")
    print(f"\n{creator_summary(result.creator)}")
    if result.personality:
        print(f"\n{personality_line(result.personality)}")
    elif result.personality_error:
        print(f"\nAnálisis de personalidad no completado: {result.personality_error}")
    print(f"\n{audit_line(result.audit)}")


def _username_from(entry):
    """Acepta 'usuario', '@usuario' o 'datos_usuario.json' (como el antiguo analisis_bigfive.py)."""
    entry = entry.strip().removeprefix("@")
    if entry.lower().endswith(".json"):
        entry = entry[:-len(".json")].removeprefix("datos_")
    return entry


def run_bigfive(entries, all_profiles=False, model=None, list_models=False):
    """Caso de uso AnalyzePersonality sobre datos_<usuario>.json ya extraídos, o lista de modelos de Groq."""
    from truematch.application.ports.personality_analyzer import PersonalityAnalysisError
    from truematch.application.use_cases.analyze_personality import AnalyzePersonality
    from truematch.domain.creator_profiling.username import InvalidUsername, Username
    from truematch.infrastructure.ai.groq_client import GroqClient
    from truematch.infrastructure.ai.groq_personality_analyzer import GroqPersonalityAnalyzer
    from truematch.infrastructure.config import load_settings
    from truematch.infrastructure.persistence.legacy_json_repository import LegacyJsonCreatorRepository
    from truematch.interfaces.cli.formatting import personality_detail, personality_line

    settings = load_settings()
    client = GroqClient(settings.require_groq_api_key(), model or settings.groq_model)
    if list_models:
        print("Modelos disponibles en tu cuenta:")
        for model_id in client.list_models():
            print(f"  - {model_id}")
        return

    repository = LegacyJsonCreatorRepository(settings.data_dir)
    if all_profiles:
        names = sorted(path.name[len("datos_"):-len(".json")] for path in settings.data_dir.glob("datos_*.json"))
        if not names:
            raise SystemExit(f"No se encontraron archivos datos_*.json en {settings.data_dir}.")
    else:
        names = [_username_from(entry) for entry in entries]

    use_case = AnalyzePersonality(repository, GroqPersonalityAnalyzer(client))
    succeeded = 0
    for name in names:
        try:
            user = Username.parse(name)
        except InvalidUsername as error:
            print(f"\n{name!r}: {error}")
            continue
        if not repository.path_for(user).is_file():
            print(f"\nNo existe {repository.path_for(user)}. Extrae primero el perfil con: {CLI} analyze {user}")
            continue
        print(f"\nAnalizando @{user} (modelo: {client.model})...")
        try:
            personality = use_case.execute(user)
        except PersonalityAnalysisError as error:
            print(f"Error: {error}")
            continue
        print(personality_detail(personality))
        print(personality_line(personality))
        print(f"Guardado en {repository.path_for(user)}.")
        succeeded += 1

    print(f"\nResumen: {succeeded} de {len(names)} perfiles analizados correctamente.")
    if succeeded < len(names):
        raise SystemExit(1)


def run_audit(username, directory=None):
    """Solo la auditoría de audiencia, sin TikTok ni Groq; añade auditoria_audiencia al archivo."""
    from truematch.application.use_cases.audit_audience import AuditAudience
    from truematch.domain.creator_profiling.username import Username
    from truematch.infrastructure.config import load_settings
    from truematch.infrastructure.persistence.legacy_json_repository import LegacyJsonCreatorRepository
    from truematch.interfaces.cli.formatting import audit_line, distribution_table

    repository = LegacyJsonCreatorRepository(directory or load_settings().data_dir)
    user = Username.parse(username)
    path = repository.path_for(user)
    if not path.is_file():
        raise SystemExit(f"No existe {path}. Extrae primero el perfil con: {CLI} analyze {user}")
    audit = AuditAudience(repository).execute(user)
    print(distribution_table(audit))
    for warning in audit.warnings:
        print(f"- {warning}")
    print(audit.disclaimer)
    print(f"\n{audit_line(audit)}")
    print(f"Guardado en {path} (clave auditoria_audiencia).")


def run_web(host, port):
    from truematch.interfaces.web.app import run

    run(host=host, port=port)


def build_parser():
    parser = argparse.ArgumentParser(prog="truematch", description="Herramientas locales de TrueMatch AI")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("session", help="Iniciar sesión manualmente en TikTok con Chromium visible")

    analyze = commands.add_parser("analyze", help="Extraer un perfil de TikTok, analizar su personalidad y auditar su audiencia")
    analyze.add_argument("usuario", help="Usuario de TikTok, con o sin @")
    analyze.add_argument("--sin-analisis", action="store_true", help="Solo extraer y auditar, sin Big Five (no usa Groq)")

    bigfive = commands.add_parser("bigfive", help="Analizar el Big Five de perfiles ya extraídos (datos_<usuario>.json)")
    bigfive.add_argument("usuarios", nargs="*", help="Usuarios (con o sin @) o archivos datos_<usuario>.json")
    bigfive.add_argument("--todos", action="store_true", help="Analizar todos los datos_*.json de la carpeta de datos")
    bigfive.add_argument("--modelo", help="Modelo de Groq (por defecto, GROQ_MODEL o el de config.py)")
    bigfive.add_argument("--listar-modelos", action="store_true", help="Mostrar los modelos disponibles en tu cuenta y salir")

    audit = commands.add_parser("audit", help="Auditar la audiencia (Benford) de un datos_<usuario>.json existente")
    audit.add_argument("usuario", help="Usuario de TikTok, con o sin @")
    audit.add_argument("--dir", default=None,
                       help="Carpeta donde está datos_<usuario>.json (por defecto, la carpeta de datos configurada)")

    web = commands.add_parser("web", help="Levantar el dashboard web local (Flask)")
    web.add_argument("--host", default="127.0.0.1", help="Dirección donde escucha (por defecto 127.0.0.1)")
    web.add_argument("--port", type=int, default=5000, help="Puerto (por defecto 5000)")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "bigfive" and sum((bool(args.usuarios), args.todos, args.listar_modelos)) != 1:
        parser.error("bigfive necesita exactamente una opción: uno o más usuarios, --todos o --listar-modelos")
    try:
        if args.command == "session":
            run_session()
        elif args.command == "analyze":
            run_analyze(args.usuario, with_personality=not args.sin_analisis)
        elif args.command == "bigfive":
            run_bigfive(args.usuarios, args.todos, args.modelo, args.listar_modelos)
        elif args.command == "audit":
            run_audit(args.usuario, args.dir)
        elif args.command == "web":
            run_web(args.host, args.port)
    except RuntimeError as error:  # incluye SessionBusyError, ConfigError y GroqError
        raise SystemExit(str(error)) from None
    except ValueError as error:  # usuario inválido o JSON ilegible
        raise SystemExit(f"Error: {error}") from None
    except OSError:
        raise SystemExit("No se pudo acceder a los datos locales. Comprueba los permisos.") from None
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("Operación cancelada.") from None


if __name__ == "__main__":
    main()
