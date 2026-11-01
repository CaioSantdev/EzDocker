# EzDocker

Gerenciador local de Docker e containers em Python, com painel web independente.
Sprint atual: **4 — Painel web**.
O planejamento está em [SPRINTS.md](SPRINTS.md).

## Manter rodando com Docker

Requer Docker Engine/Desktop iniciado e Docker Compose. Não precisa instalar UV,
Python, Node ou npm na máquina: as dependências são instaladas nas imagens.

```bash
docker compose up -d --build
```

Abra **http://localhost:18081**. O Compose inicia dois containers: Nginx serve o
painel compilado e encaminha `/api` para o backend. Apenas o painel tem porta
publicada, restrita a localhost. O backend acessa o socket do Docker da máquina,
então pode ver e controlar seus outros containers. Esse acesso dá controle sobre
o Docker; mantenha o painel local enquanto não houver autenticação.

Os containers usam `restart: unless-stopped`: voltam quando o Docker reinicia,
exceto se você os parar manualmente. Docker Desktop precisa estar iniciado para
isso funcionar. A configuração limita o armazenamento dos logs do próprio
EzDocker a três arquivos de 10 MB por serviço.

```bash
docker compose ps                 # situação dos serviços
docker compose logs -f           # acompanhar o próprio EzDocker
docker compose stop              # parar o painel e a API
docker compose start             # voltar a executar
docker compose up -d --build     # aplicar mudanças no código
docker compose down              # remover somente os serviços e a rede do EzDocker
```

Para usar outra porta, copie `.env.example` para `.env` e ajuste `EZDOCKER_PORT`.
Por exemplo, `EZDOCKER_PORT=18091` permite manter o desenvolvimento em 18081 e o
painel Docker em **http://localhost:18091**. No Docker rootless, ajuste também
`EZDOCKER_SOCKET`. Em WSL, mantenha a integração com Docker Desktop habilitada.
O socket precisa existir; o Compose não cria uma pasta no lugar dele.

Neste ambiente, `.env` já foi criado com `EZDOCKER_PORT=18091` porque a porta de
desenvolvimento estava ocupada. A instância Docker foi iniciada e validada nessa
porta. Esse arquivo não é versionado; uma instalação nova usa 18081 por padrão.

O painel também lista seus próprios containers; parar o backend ou o frontend
do EzDocker interrompe seu acesso ao painel. Use `docker compose start` para
recuperar. Os painéis de logs selecionados ficam apenas no navegador e precisam
ser adicionados novamente após recarregar a página.

O build do backend segue a [integração oficial do UV com Docker](https://docs.astral.sh/uv/guides/integration/docker/).

## Rodar tudo com um comando

Depois da instalação inicial das dependências (`uv sync --locked` e
`cd frontend && npm ci`), execute na raiz:

```bash
./ez
```

Inicia backend e frontend com recarregamento automático. Abra
**http://127.0.0.1:18081**. Ctrl+C encerra os dois servidores. Se um servidor falhar
(por exemplo, porta ocupada), o outro é encerrado; não inicia cópias adicionais
intencionalmente. Encerre servidores antigos antes de usar este comando.

O atalho local usa UV do PATH ou `.tools/uv` e carrega o NVM quando necessário.
Também funciona como `./ez containers` ou `./ez serve` (apenas API).
Com UV e npm no PATH, o equivalente é:

```bash
uv run ezdocker dev
```

Alias opcional para executar de qualquer pasta (adicione ao `~/.zshrc`):

```bash
alias ezdocker='/home/caio/projetos/EzDocker/ez'
```

Depois de `source ~/.zshrc`, basta `ezdocker`. Ajuste o caminho em outra máquina.
O script não cria aliases nem altera configurações globais automaticamente.

## Requisitos

- Python 3.14 e UV.
- Docker Engine ou Docker Desktop iniciado, acessível pelo usuário atual.
- No WSL, integração habilitada para a distribuição no Docker Desktop.

## Instalação e execução

```bash
uv sync --locked
uv run ezdocker containers
```

O UV cria e usa `.venv` automaticamente. Ativação manual opcional:

```bash
source .venv/bin/activate
```

Neste ambiente, o UV foi instalado localmente em `.tools`, seguindo o
[instalador oficial](https://docs.astral.sh/uv/reference/installer/).
Se `uv` não estiver no PATH, substitua por `./.tools/uv`:

```bash
UV_CACHE_DIR=.uv-cache ./.tools/uv sync --locked
UV_CACHE_DIR=.uv-cache ./.tools/uv run ezdocker containers
```

O comando lista containers ativos e parados e retorna código 1 quando não consegue
consultar o Docker. Usa a configuração de ambiente do SDK (`DOCKER_HOST`,
`DOCKER_TLS_VERIFY` e `DOCKER_CERT_PATH`); não seleciona automaticamente contextos
da CLI Docker. Nenhum container é alterado nesta sprint.

## Desenvolvimento

### Painel web

O frontend está em [`frontend/`](frontend/README.md), preparado para se tornar
um repositório separado. Usa TypeScript, Vite e CSS puro, sem framework de interface.

Em um terminal na raiz, inicie a API:

```bash
./.tools/uv run uvicorn ezdocker.api:app --reload --port 18080
```

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

Abra **http://127.0.0.1:18081**. Requer Node.js 22.12+ e npm; se usa NVM, carregue
com `source ~/.nvm/nvm.sh`. O frontend usa o proxy local `/api`, sem exigir CORS
no backend. A documentação do frontend descreve build e reverse proxy para deploy.

### Backend

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Código em `src/ezdocker`; testes em `tests`. Os testes de API usam
[TestClient](https://fastapi.tiangolo.com/tutorial/testing/) com Docker simulado.

## API local

```bash
./.tools/uv run ezdocker serve
```

Inicia em `http://127.0.0.1:18080`. Documentação interativa em
`http://127.0.0.1:18080/docs`; contrato OpenAPI em `/openapi.json`.
Use Ctrl+C para encerrar.

| Endpoint GET | Resposta de sucesso | Docker indisponível |
| --- | --- | --- |
| `/health` | `200 {"status":"ok"}` | Continua retornando 200: verifica a API |
| `/docker/status` | `200 {"status":"connected"}` | 503 |
| `/containers` | 200 com lista de ID, nome, imagem e status; `[]` se vazia | 503 |

Erros de conexão têm o formato
`{"code":"docker_unavailable","message":"orientação para corrigir a conexão"}`.
Cada consulta fecha a conexão ao terminar; as operações Docker têm timeout de
30 segundos por requisição ao daemon. A API inicia mesmo sem Docker disponível.

### Ações e logs (sprint 3)

Use o ID ou nome do container no lugar de `{id}`. As ações podem ser executadas
pela página `/docs` com **Try it out**.

| Método | Endpoint | Resultado |
| --- | --- | --- |
| POST | `/containers/{id}/start` | Inicia e retorna o estado consultado |
| POST | `/containers/{id}/stop` | Para e retorna o estado consultado |
| POST | `/containers/{id}/restart` | Reinicia e retorna o estado consultado |
| GET | `/containers/{id}/logs?tail=100` | Retorna `{"logs":"conteúdo"}` |

`tail` aceita de 1 a 1000 linhas (padrão 100); valores inválidos retornam 422.
Os logs incluem stdout e stderr e são uma captura, sem acompanhamento contínuo.
O limite é de linhas, não de bytes; linhas muito longas podem gerar respostas grandes.
Bytes inválidos em UTF-8 são substituídos. A disponibilidade dos logs depende do
driver configurado no Docker.

Parada e reinício permitem 10 segundos para o processo encerrar antes de o Docker
forçar sua finalização, conforme o [SDK Docker](https://docker-py.readthedocs.io/en/stable/containers.html).
Os erros mantêm o formato `{"code":"...","message":"..."}`:

- 404: `container_not_found`.
- 502: `operation_failed` (o daemon recusou a operação).
- 503: `docker_unavailable` (conexão indisponível).
- 504: `docker_timeout`; consulte o estado antes de tentar novamente, pois a ação
  pode ter sido executada mesmo sem resposta.

Validação manual opcional: `uv run python scripts/validate_sprint3.py`. Ela requer
a imagem local `busybox:1.37`, cria um container isolado, valida as ações e os logs
pela API e remove apenas esse container ao terminar.

## Validação da sprint 1

O ambiente e o comando foram instalados. A tentativa real de listar containers em
01/11/2026 retornou a mensagem de indisponibilidade e código 1: não existe
`/var/run/docker.sock` e a CLI informou que a integração do Docker Desktop com esta
distribuição WSL não está habilitada. A listagem real ainda precisa ser validada
após habilitar Settings → Resources → WSL Integration no Docker Desktop e aplicar
a configuração. Depois, execute novamente `uv run ezdocker containers`.

## Validação da sprint 2

Em 01/11/2026, após habilitar a integração WSL, a CLI e a API consultaram com sucesso
o Docker real e listaram seis containers parados. Os três endpoints responderam
HTTP 200 em um servidor local. Os 13 testes passaram, incluindo lista vazia,
Docker indisponível com HTTP 503 e saúde independente do daemon. Lint, formatação
e sincronização offline com `uv.lock` aprovados.

O acesso ao socket e à porta local exigiu execução fora do sandbox do agente.
A combinação atual Starlette/TestClient emite um aviso de depreciação do transporte
HTTPX nos testes; os testes passam e isso não afeta o servidor.

## Validação da sprint 3

Os 33 testes passaram. Iniciar, consultar logs, reiniciar e parar foram validados
pela API com Docker real em um container BusyBox descartável. O container foi
removido ao terminar, e uma nova ação sobre seu ID retornou 404. Os containers
existentes não foram alterados. Lint e formatação aprovados.
