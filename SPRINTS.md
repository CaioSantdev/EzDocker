# Sprints do EzDocker

Executaremos uma sprint por vez. Cada sprint termina com validação e uma entrega
utilizável; a próxima começa após a revisão com o usuário.

## Sprint 1 — Fundação e conexão com Docker

Status: concluída; conexão real confirmada após habilitar a integração WSL.

- Inicializar pacote Python com UV, `.venv` e dependências travadas em `uv.lock`.
- Separar acesso ao Docker da interface.
- Criar comando que lista containers ativos e parados: ID, nome, status e imagem.
- Tratar indisponibilidade do Docker com orientação clara e saída de erro.
- Documentar execução e verificar os principais caminhos de falha.

Aceite: ambiente instalado, testes e lint aprovados, comando executável e resultado
da tentativa de conexão real registrado no README.

## Sprint 2 — API local com FastAPI

Status: concluída. Endpoints `/health`, `/docker/status` e `/containers` validados
por HTTP com Docker real. Treze testes aprovados, lint e formatação aprovados.

- Criar API e endpoint de saúde.
- Expor listagem de containers e situação da conexão com Docker.
- Definir modelos de resposta e erros; testar com Docker simulado.
- Executar em `127.0.0.1` por padrão.

Aceite: consultar a API local e obter respostas consistentes com e sem Docker ativo.

## Sprint 3 — Ações e logs

Status: concluída. Ações e logs validados pela API em container BusyBox
descartável, removido ao terminar; 404 após remoção confirmado. Os 33 testes
passaram, incluindo erros de operação, timeout e validação do limite de logs.

- Iniciar, parar e reiniciar containers pela API.
- Consultar logs com limite de linhas.
- Tratar container inexistente, falha da operação e tempo limite.

Aceite: validar operações em container descartável autorizado e cobrir erros em testes.

## Sprint 4 — Painel web

Status: implementada. Frontend independente em `frontend/`, usando TypeScript +
Vite + CSS puro, sem framework de interface. TypeScript e build aprovados; página
HTTP 200 e proxy `/api` validados com seis containers reais. Falta validar o fluxo
visual e as interações no navegador (ferramenta de navegador indisponível nesta sessão).

- Definir a tecnologia da interface ao iniciar esta sprint.
- Exibir lista, status, ações e logs usando a API.
- Mostrar carregamento, lista vazia e falhas; confirmar operações de parada.

Aceite: fluxo completo pelo navegador, com mensagens claras e atualização de status.

## Sprint 5 — Preparação do MVP

Em andamento: comando `uv run ezdocker dev` e atalho `./ez` iniciam backend e
frontend com recarregamento automático e encerramento conjunto. Os 36 testes
Python e quatro testes do frontend passaram; TypeScript, build e lint aprovados.
Faltam validação visual integrada e revisão final da instalação em outra máquina.

- Melhorar configuração, diagnóstico e documentação de instalação.
- Executar validação integrada e revisar acesso exclusivamente local.
- Registrar limitações e preparar versão inicial.

Aceite: instalação reproduzível e fluxo do MVP validado.

## Backlog posterior

Criação e remoção de containers, imagens, volumes, métricas de CPU/memória e Docker
Compose. Acesso remoto e autenticação exigirão escopo próprio.
