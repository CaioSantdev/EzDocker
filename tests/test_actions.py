from unittest.mock import MagicMock, patch

import pytest
from docker.errors import APIError, NotFound
from fastapi.testclient import TestClient
from requests.exceptions import ReadTimeout

from ezdocker import docker_service as service
from ezdocker.api import app


@pytest.mark.parametrize("action", ["start", "stop", "restart"])
def test_action_calls_docker_and_refreshes_status(action):
    client = MagicMock()
    container = client.containers.get.return_value
    container.short_id = "abc"
    container.name = "test"
    container.status = "running"
    container.attrs = {"Config": {"Image": "busybox"}}
    with patch.object(service.docker, "from_env", return_value=client):
        result = service.container_action("abc", action)
    client.containers.get.assert_called_once_with("abc")
    getattr(container, action).assert_called_once_with(
        **({} if action == "start" else {"timeout": 10})
    )
    container.reload.assert_called_once_with()
    client.close.assert_called_once()
    assert result.status == "running"


@pytest.mark.parametrize("action", ["start", "stop", "restart"])
@pytest.mark.parametrize(
    "error, status, code",
    [
        (NotFound("missing"), 404, "container_not_found"),
        (APIError("failed"), 502, "operation_failed"),
        (ReadTimeout("slow"), 504, "docker_timeout"),
    ],
)
def test_action_errors_are_translated(action, error, status, code):
    docker = MagicMock()
    getattr(docker.containers.get.return_value, action).side_effect = error
    with (
        patch.object(service.docker, "from_env", return_value=docker),
        TestClient(app) as client,
    ):
        response = client.post(f"/containers/abc/{action}")
    assert response.status_code == status
    assert response.json()["code"] == code
    docker.close.assert_called_once()


def test_logs_decode_invalid_utf8_and_pass_tail():
    docker = MagicMock()
    container = docker.containers.get.return_value
    container.logs.return_value = b"hello\n\xff"
    with (
        patch.object(service.docker, "from_env", return_value=docker),
        TestClient(app) as client,
    ):
        response = client.get("/containers/abc/logs?tail=2")
    assert response.status_code == 200
    assert response.json() == {"logs": "hello\n\ufffd"}
    container.logs.assert_called_once_with(tail=2, stream=False, follow=False)
    docker.close.assert_called_once()


@pytest.mark.parametrize("tail", ["0", "1001", "all", "-1"])
def test_invalid_tail_never_calls_docker(tail):
    with patch.object(service.docker, "from_env") as connect, TestClient(app) as client:
        assert client.get(f"/containers/abc/logs?tail={tail}").status_code == 422
    connect.assert_not_called()


@pytest.mark.parametrize("action", ["start", "stop", "restart"])
def test_action_success_response(action):
    with (
        patch.object(
            service,
            "container_action",
            return_value=service.ContainerInfo("abc", "test", "busybox", "running"),
        ) as operation,
        TestClient(app) as client,
    ):
        response = client.post(f"/containers/abc/{action}")
    assert response.status_code == 200
    assert response.json()["id"] == "abc"
    operation.assert_called_once_with("abc", action)
