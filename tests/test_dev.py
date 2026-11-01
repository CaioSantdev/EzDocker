import signal
from unittest.mock import MagicMock, patch

from ezdocker.dev import run_dev, stop_processes


def test_missing_npm_exits_with_help(capsys):
    with patch("ezdocker.dev.shutil.which", return_value=None):
        assert run_dev() == 1
    assert "source ~/.nvm/nvm.sh" in capsys.readouterr().err


def test_server_failure_stops_remaining_process_group():
    backend = MagicMock(pid=123)
    backend.poll.return_value = 1
    frontend = MagicMock(pid=456)
    frontend.poll.return_value = None
    with (
        patch("ezdocker.dev.shutil.which", return_value="/bin/npm"),
        patch("ezdocker.dev.Path.is_dir", return_value=True),
        patch("ezdocker.dev.subprocess.Popen", side_effect=[backend, frontend]),
        patch("ezdocker.dev.os.killpg") as kill,
    ):
        assert run_dev() == 1
    kill.assert_called_once_with(456, signal.SIGTERM)
    backend.wait.assert_called_once()
    frontend.wait.assert_called_once()


def test_cleanup_handles_process_exiting_before_signal():
    process = MagicMock(pid=123)
    process.poll.return_value = None
    with patch("ezdocker.dev.os.killpg", side_effect=ProcessLookupError):
        stop_processes([process])
    process.wait.assert_called_once()
