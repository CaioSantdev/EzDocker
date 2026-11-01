"""Validação manual: cria e remove exclusivamente um container descartável."""

import time
import uuid

import docker
from fastapi.testclient import TestClient

from ezdocker.api import app


def main():
    docker_client = docker.from_env(timeout=30)
    container = None
    try:
        # Usa imagem já instalada; não baixa imagens nem monta arquivos do host.
        image = docker_client.images.get("busybox:1.37")
        container = docker_client.containers.create(
            image.id,
            ["sh", "-c", "echo ezdocker-sprint3; exec sleep 300"],
            name=f"ezdocker-sprint3-{uuid.uuid4().hex[:8]}",
            network_disabled=True,
            labels={"ezdocker.validation": "sprint3"},
        )
        with TestClient(app) as api:
            for action, expected in [
                ("start", "running"),
                ("restart", "running"),
                ("stop", "exited"),
            ]:
                response = api.post(f"/containers/{container.id}/{action}")
                assert response.status_code == 200, response.text
                assert response.json()["status"] == expected, response.text
                print(f"{action}: {expected}")
                if action == "start":
                    for _ in range(20):
                        logs = api.get(f"/containers/{container.id}/logs?tail=10")
                        assert logs.status_code == 200, logs.text
                        if "ezdocker-sprint3" in logs.json()["logs"]:
                            break
                        time.sleep(0.1)
                    else:
                        raise AssertionError("Log não encontrado")
                    print("logs: conteúdo validado")
            container.remove()
            missing_id = container.id
            container = None
            assert api.post(f"/containers/{missing_id}/start").status_code == 404
            print("container removido: 404 validado")
    finally:
        if container is not None:
            container.remove(force=True)
        docker_client.close()


if __name__ == "__main__":
    main()
