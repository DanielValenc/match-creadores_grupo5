"""Línea de comandos de TrueMatch AI.

Uso (desde la carpeta backend/):
    python -m truematch.interfaces.cli.main session            # inicio de sesión manual en Chromium
    python -m truematch.interfaces.cli.main audit <usuario>    # auditoría sobre un datos_<usuario>.json existente
    python -m truematch.interfaces.cli.main web                # dashboard web en http://127.0.0.1:5000
"""
import argparse


def run_session():
    # Import diferido: --help funciona aunque Playwright o filelock no estén instalados.
    from truematch.infrastructure.tiktok.session import configure_session

    configure_session()
    print("Sesión local guardada. TikTok puede solicitar autenticación de nuevo.")


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
        raise SystemExit(f"No existe {path}. Extrae primero el perfil con: python main.py {user.value}")
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
    audit = commands.add_parser("audit", help="Auditar la audiencia (Benford) de un datos_<usuario>.json existente")
    audit.add_argument("usuario", help="Usuario de TikTok, con o sin @")
    audit.add_argument("--dir", default=None,
                       help="Carpeta donde está datos_<usuario>.json (por defecto, la carpeta de datos configurada)")
    web = commands.add_parser("web", help="Levantar el dashboard web local (Flask)")
    web.add_argument("--host", default="127.0.0.1", help="Dirección donde escucha (por defecto 127.0.0.1)")
    web.add_argument("--port", type=int, default=5000, help="Puerto (por defecto 5000)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "session":
            run_session()
        elif args.command == "audit":
            run_audit(args.usuario, args.dir)
        elif args.command == "web":
            run_web(args.host, args.port)
    except RuntimeError as error:  # incluye SessionBusyError y ConfigError
        raise SystemExit(str(error)) from None
    except ValueError as error:  # usuario inválido o JSON ilegible
        raise SystemExit(f"Error: {error}") from None
    except OSError:
        raise SystemExit("No se pudo acceder a los datos locales. Comprueba los permisos.") from None
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("Operación cancelada.") from None


if __name__ == "__main__":
    main()
