from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from docker.errors import DockerException
from requests.exceptions import ConnectionError

from ezdocker.docker_service import (
    DockerUnavailableError,
    check_connection,
    list_containers,
)


def test_lists_running_and_stopped_containers_and_closes_connection():
    client = MagicMock()
    client.containers.list.return_value = [
        SimpleNamespace(
            short_id="abc123",
            name="postgres",
            status="exited",
            attrs={"Config": {"Image": "postgres:17"}},
        )
    ]
    with patch("ezdocker.docker_service.docker.from_env", return_value=client):
        containers = list_containers()
    assert containers[0].name == "postgres"
    assert containers[0].status == "exited"
    assert containers[0].image == "postgres:17"
    client.containers.list.assert_called_once_with(all=True)
    client.close.assert_called_once()


def test_ping_checks_daemon_and_closes_connection():
    client = MagicMock()
    client.ping.return_value = True
    with patch("ezdocker.docker_service.docker.from_env", return_value=client):
        check_connection()
    client.ping.assert_called_once_with()
    client.close.assert_called_once()


@pytest.mark.parametrize("error", [ConnectionError("lost"), DockerException("offline")])
def test_ping_failure_is_translated_and_connection_is_closed(error):
    client = MagicMock()
    client.ping.side_effect = error
    with (
        patch("ezdocker.docker_service.docker.from_env", return_value=client),
        pytest.raises(DockerUnavailableError),
    ):
        check_connection()
    client.close.assert_called_once()


def test_connection_failure_has_actionable_message():
    with (
        patch(
            "ezdocker.docker_service.docker.from_env",
            side_effect=DockerException("offline"),
        ),
        pytest.raises(DockerUnavailableError, match="Docker Desktop"),
    ):
        list_containers()


def test_closes_connection_when_listing_fails():
    client = MagicMock()
    client.containers.list.side_effect = DockerException("connection lost")
    with (
        patch("ezdocker.docker_service.docker.from_env", return_value=client),
        pytest.raises(DockerUnavailableError),
    ):
        list_containers()
    client.close.assert_called_once()
