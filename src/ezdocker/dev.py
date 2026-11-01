"""Inicia frontend e backend e encerra ambos quando um deles termina."""

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


def stop_processes(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def run_dev() -> int:
    root = Path(__file__).resolve().parents[2]
    frontend = root / "frontend"
    npm = shutil.which("npm")
    if not npm:
        print(
            "npm não encontrado. Carregue o NVM: source ~/.nvm/nvm.sh", file=sys.stderr
        )
        return 1
    if not (frontend / "node_modules" / "vite").is_dir():
        print("Instale o frontend primeiro: cd frontend && npm ci", file=sys.stderr)
        return 1

    processes: list[subprocess.Popen] = []
    try:
        processes.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "ezdocker.api:app",
                    "--reload",
                    "--reload-dir",
                    str(root / "src"),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                ],
                cwd=root,
                start_new_session=True,
            )
        )
        processes.append(
            subprocess.Popen(
                [npm, "run", "dev"],
                cwd=frontend,
                start_new_session=True,
            )
        )
        print(
            "\nEzDocker: http://127.0.0.1:5173 · API: http://127.0.0.1:8000/docs",
            flush=True,
        )
        print(
            "Recarregamento automático ativo. Ctrl+C encerra os dois servidores.\n",
            flush=True,
        )
        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    print(
                        "Um servidor encerrou; finalizando o ambiente.", file=sys.stderr
                    )
                    return code
            time.sleep(0.2)
    except KeyboardInterrupt:
        return 0
    except OSError as exc:
        print(f"Não foi possível iniciar o ambiente: {exc}", file=sys.stderr)
        return 1
    finally:
        stop_processes(processes)
