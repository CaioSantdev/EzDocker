"""API local de gerenciamento do EzDocker."""

from typing import Annotated, Literal

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ezdocker import docker_service


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class DockerStatusResponse(BaseModel):
    status: Literal["connected"] = "connected"


class ContainerResponse(BaseModel):
    id: str
    name: str
    image: str
    status: str


class ErrorResponse(BaseModel):
    code: Literal[
        "docker_unavailable",
        "container_not_found",
        "operation_failed",
        "docker_timeout",
    ]
    message: str


app = FastAPI(title="EzDocker", version="0.1.0")
docker_errors = {503: {"model": ErrorResponse, "description": "Docker indisponível"}}
docker_errors.update(
    {
        404: {"model": ErrorResponse, "description": "Container não encontrado"},
        502: {"model": ErrorResponse, "description": "Operação recusada pelo Docker"},
        504: {"model": ErrorResponse, "description": "Tempo limite no Docker"},
    }
)


class LogsResponse(BaseModel):
    logs: str


async def operation_error(request: Request, exc: Exception) -> JSONResponse:
    status, code = {
        docker_service.ContainerNotFoundError: (404, "container_not_found"),
        docker_service.ContainerOperationError: (502, "operation_failed"),
        docker_service.DockerTimeoutError: (504, "docker_timeout"),
    }[type(exc)]
    return JSONResponse(status_code=status, content={"code": code, "message": str(exc)})


for error_type in (
    docker_service.ContainerNotFoundError,
    docker_service.ContainerOperationError,
    docker_service.DockerTimeoutError,
):
    app.add_exception_handler(error_type, operation_error)


@app.exception_handler(docker_service.DockerUnavailableError)
async def docker_unavailable(
    request: Request, exc: docker_service.DockerUnavailableError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(code="docker_unavailable", message=str(exc)).model_dump(),
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Saúde da API; funciona mesmo quando o Docker está desligado."""
    return HealthResponse()


@app.get("/docker/status", response_model=DockerStatusResponse, responses=docker_errors)
def docker_status() -> DockerStatusResponse:
    docker_service.check_connection()
    return DockerStatusResponse()


@app.get("/containers", response_model=list[ContainerResponse], responses=docker_errors)
def containers() -> list[docker_service.ContainerInfo]:
    return docker_service.list_containers()


@app.post(
    "/containers/{container_id}/start",
    response_model=ContainerResponse,
    responses=docker_errors,
)
def start_container(container_id: str) -> docker_service.ContainerInfo:
    return docker_service.container_action(container_id, "start")


@app.post(
    "/containers/{container_id}/stop",
    response_model=ContainerResponse,
    responses=docker_errors,
)
def stop_container(container_id: str) -> docker_service.ContainerInfo:
    return docker_service.container_action(container_id, "stop")


@app.post(
    "/containers/{container_id}/restart",
    response_model=ContainerResponse,
    responses=docker_errors,
)
def restart_container(container_id: str) -> docker_service.ContainerInfo:
    return docker_service.container_action(container_id, "restart")


@app.get(
    "/containers/{container_id}/logs",
    response_model=LogsResponse,
    responses=docker_errors,
)
def logs(
    container_id: str, tail: Annotated[int, Query(ge=1, le=1000)] = 100
) -> LogsResponse:
    return LogsResponse(logs=docker_service.container_logs(container_id, tail))
