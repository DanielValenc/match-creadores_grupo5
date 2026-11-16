"""Línea de comandos de TrueMatch AI.

Uso (desde la carpeta backend/):
    python -m truematch.interfaces.cli.main session    # inicio de sesión manual en Chromium
"""
import argparse


def run_session():
    # Import diferido: --help funciona aunque Playwright o filelock no estén instalados.
    from truematch.infrastructure.tiktok.session import configure_session

    configure_session()
    print("Sesión local guardada. TikTok puede solicitar autenticación de nuevo.")


def build_parser():
    parser = argparse.ArgumentParser(prog="truematch", description="Herramientas locales de TrueMatch AI")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("session", help="Iniciar sesión manualmente en TikTok con Chromium visible")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "session":
            run_session()
    except RuntimeError as error:  # incluye SessionBusyError
        raise SystemExit(str(error)) from None
    except OSError:
        raise SystemExit("No se pudo acceder a los datos locales. Comprueba los permisos.") from None
    except (KeyboardInterrupt, EOFError):
        raise SystemExit("Operación cancelada; Chromium se ha cerrado.") from None


if __name__ == "__main__":
    main()
