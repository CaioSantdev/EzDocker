"""Acesso ao Docker Engine, separado da interface."""

from contextlib import contextmanager
from dataclasses import dataclass

import docker
from docker.errors import APIError, DockerException, NotFound
from requests.exceptions import RequestException, Timeout


class DockerUnavailableError(Exception):
    """Não foi possível consultar o Docker Engine."""


class ContainerNotFoundError(Exception):
    """Container não encontrado."""


class ContainerOperationError(Exception):
    """O daemon recusou a operação."""


class DockerTimeoutError(Exception):
    """Tempo limite ao comunicar com Docker; resultado pode ser incerto."""


@dataclass(frozen=True)
class ContainerInfo:
    id: str
    name: str
    image: str
    status: str


@contextmanager
def docker_connection():
    """Abre uma conexão por operação e traduz falhas de transporte."""
    client = None
    try:
        client = docker.from_env(timeout=30)
        yield client
    except NotFound as exc:
        raise ContainerNotFoundError("Container não encontrado.") from exc
    except Timeout as exc:
        raise DockerTimeoutError(
            "O Docker excedeu o tempo limite. Consulte o status antes de repetir a ação."
        ) from exc
    except APIError as exc:
        raise ContainerOperationError(
            "O Docker não conseguiu concluir a operação."
        ) from exc
    except (DockerException, RequestException, OSError) as exc:
        raise DockerUnavailableError(
            "Não foi possível acessar o Docker. Verifique se o Docker Engine ou "
            "Docker Desktop está iniciado e se seu usuário tem acesso ao socket. "
            "No WSL, confira a integração da distribuição no Docker Desktop. "
            "Se necessário, configure DOCKER_HOST."
        ) from exc
    finally:
        if client is not None:
            client.close()


def check_connection() -> None:
    """Confirma que o daemon responde, sem depender da listagem de containers."""
    with docker_connection() as client:
        if not client.ping():
            raise DockerUnavailableError("O Docker não respondeu ao diagnóstico.")


def list_containers() -> list[ContainerInfo]:
    """Lista containers ativos e parados, sem alterar o Docker."""
    with docker_connection() as client:
        return [
            ContainerInfo(
                id=container.short_id,
                name=container.name,
                image=container.attrs.get("Config", {}).get("Image") or "<sem imagem>",
                status=container.status,
            )
            for container in client.containers.list(all=True)
        ]


def container_action(container_id: str, action: str) -> ContainerInfo:
    """Executa uma ação permitida e consulta o estado resultante."""
    if action not in {"start", "stop", "restart"}:
        raise ValueError("Ação inválida.")
    with docker_connection() as client:
        container = client.containers.get(container_id)
        if action == "start":
            container.start()
        elif action == "stop":
            container.stop(timeout=10)
        else:
            container.restart(timeout=10)
        container.reload()
        return ContainerInfo(
            id=container.short_id,
            name=container.name,
            image=container.attrs.get("Config", {}).get("Image") or "<sem imagem>",
            status=container.status,
        )


def container_logs(container_id: str, tail: int = 100) -> str:
    """Retorna as últimas linhas de stdout e stderr, sem acompanhar o fluxo."""
    if not 1 <= tail <= 1000:
        raise ValueError("tail deve estar entre 1 e 1000.")
    with docker_connection() as client:
        container = client.containers.get(container_id)
        return container.logs(tail=tail, stream=False, follow=False).decode(
            "utf-8", errors="replace"
        )
