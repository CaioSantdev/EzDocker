from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from ezdocker.api import app
from ezdocker.docker_service import ContainerInfo, DockerUnavailableError


def test_health_does_not_require_docker():
    with (
        patch("ezdocker.docker_service.docker.from_env") as connect,
        TestClient(app) as client,
    ):
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    connect.assert_not_called()


def test_docker_status():
    with (
        patch("ezdocker.docker_service.check_connection") as check,
        TestClient(app) as client,
    ):
        response = client.get("/docker/status")
    assert response.status_code == 200
    assert response.json() == {"status": "connected"}
    check.assert_called_once_with()


@pytest.mark.parametrize(
    "items, expected",
    [
        ([], []),
        (
            [ContainerInfo("abc123", "db", "postgres:17", "exited")],
            [
                {
                    "id": "abc123",
                    "name": "db",
                    "image": "postgres:17",
                    "status": "exited",
                }
            ],
        ),
    ],
)
def test_container_response(items, expected):
    with (
        patch("ezdocker.docker_service.list_containers", return_value=items),
        TestClient(app) as client,
    ):
        response = client.get("/containers")
    assert response.status_code == 200
    assert response.json() == expected


@pytest.mark.parametrize(
    "path, operation",
    [("/docker/status", "check_connection"), ("/containers", "list_containers")],
)
def test_docker_unavailable_is_consistent(path, operation):
    with (
        patch(
            f"ezdocker.docker_service.{operation}",
            side_effect=DockerUnavailableError("Docker indisponível"),
        ),
        TestClient(app) as client,
    ):
        response = client.get(path)
    assert response.status_code == 503
    assert response.json() == {
        "code": "docker_unavailable",
        "message": "Docker indisponível",
    }


def test_openapi_documents_docker_errors():
    schema = app.openapi()
    for path in ("/containers", "/docker/status"):
        assert "503" in schema["paths"][path]["get"]["responses"]
