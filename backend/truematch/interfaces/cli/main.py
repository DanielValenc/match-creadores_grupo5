"""Línea de comandos de TrueMatch AI.

Uso (desde la carpeta backend/):
    python -m truematch.interfaces.cli.main session            # inicio de sesión manual en Chromium
    python -m truematch.interfaces.cli.main audit <usuario>    # auditoría sobre un datos_<usuario>.json existente
"""
import argparse
from pathlib import Path

# backend/truematch/interfaces/cli/main.py -> parents[4] es la raíz del repositorio, donde main.py deja los JSON.
REPO_ROOT = Path(__file__).resolve().parents[4]


def run_session():
    # Import diferido: --help funciona aunque Playwright o filelock no estén instalados.
    from truematch.infrastructure.tiktok.session import configure_session

    configure_session()
    print("Sesión local guardada. TikTok puede solicitar autenticación de nuevo.")


def run_audit(username, directory):
    """Solo la auditoría de audiencia, sin TikTok ni Groq; añade auditoria_audiencia al archivo."""
    from truematch.application.use_cases.audit_audience import AuditAudience
    from truematch.domain.creator_profiling.username import Username
    from truematch.infrastructure.persistence.legacy_json_repository import LegacyJsonCreatorRepository
    from truematch.interfaces.cli.formatting import audit_line, distribution_table

    repository = LegacyJsonCreatorRepository(directory)
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


def build_parser():
    parser = argparse.ArgumentParser(prog="truematch", description="Herramientas locales de TrueMatch AI")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("session", help="Iniciar sesión manualmente en TikTok con Chromium visible")
    audit = commands.add_parser("audit", help="Auditar la audiencia (Benford) de un datos_<usuario>.json existente")
    audit.add_argument("usuario", help="Usuario de TikTok, con o sin @")
    audit.add_argument("--dir", default=str(REPO_ROOT),
                       help="Carpeta donde está datos_<usuario>.json (por defecto, la raíz del repositorio)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "session":
            run_session()
        elif args.command == "audit":
            run_audit(args.usuario, args.dir)
    except RuntimeError as error:  # incluye SessionBusyError
        raise SystemExit(str(error)) from None
    except ValueError as error:  # usuario inválido o JSON ilegible
        raise SystemExit(f"Error: {error}") from None
    except OSError:
        raise SystemExit("No se pudo acceder a los datos locales. Comprueba los permisos.") from None
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("Operación cancelada; Chromium se ha cerrado.") from None


if __name__ == "__main__":
    main()
