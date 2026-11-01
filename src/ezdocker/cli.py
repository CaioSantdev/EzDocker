"""Comando inicial de diagnóstico e listagem."""

import argparse
import sys

from ezdocker.docker_service import DockerUnavailableError, list_containers


def main() -> int:
    parser = argparse.ArgumentParser(
        description="EzDocker — gerenciador local de Docker"
    )
    parser.add_argument(
        "command",
        choices=["containers", "serve", "dev"],
        help="Lista containers, inicia a API ou o ambiente completo de desenvolvimento",
    )
    args = parser.parse_args()
    if args.command == "dev":
        from ezdocker.dev import run_dev

        return run_dev()
    if args.command == "serve":
        import uvicorn

        uvicorn.run("ezdocker.api:app", host="127.0.0.1", port=18080)
        return 0
    try:
        containers = list_containers()
    except DockerUnavailableError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not containers:
        print("Docker conectado. Nenhum container encontrado.")
        return 0
    print(f"{'ID':<12}  {'NOME':<25}  {'STATUS':<12}  IMAGEM")
    for container in containers:
        print(
            f"{container.id:<12}  {container.name:<25}  "
            f"{container.status:<12}  {container.image}"
        )
    return 0
