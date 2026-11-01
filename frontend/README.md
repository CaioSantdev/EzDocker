# EzDocker Frontend

Aplicação independente em TypeScript, Vite e CSS puro. Sem framework de interface,
roteador ou biblioteca de componentes. Esta pasta pode virar um repositório próprio;
não importa arquivos do backend nem exige Python para compilar.

## Desenvolvimento

Requer Node.js 22.12+ e npm (Node 24 LTS recomendado).

```bash
cd frontend
npm ci
npm run dev
```

Acesse http://127.0.0.1:5173. Em outro terminal, na raiz do backend:

```bash
./.tools/uv run uvicorn ezdocker.api:app --reload
```

Se Node foi instalado com NVM, execute `source ~/.nvm/nvm.sh` antes dos comandos.
O frontend usa `/api`; Vite encaminha para `http://127.0.0.1:8000`, retirando o
prefixo. Para mudar o destino, copie `.env.example` para `.env.local` e ajuste
`API_PROXY_TARGET`. Reinicie o Vite depois de alterar essa variável.

## Funcionalidades

Lista e busca por nome/imagem, totais, atualização manual, iniciar/parar/reiniciar
com confirmação para parada e reinício e painéis de logs com 1–1000 linhas.
Dados e logs do Docker são renderizados como texto. Falhas mantêm
a última lista com aviso de que ela pode estar desatualizada.

A navegação usa uma bolha flutuante central na parte inferior, com Containers,
Volumes e Logs. As seções têm links próprios (`#containers`, `#volumes`, `#logs`)
e suportam voltar/avançar do navegador. Logs permite acompanhar até três containers
simultaneamente. Cada painel consulta uma captura das últimas linhas a cada dois
segundos após a resposta anterior, sem sobrepor consultas no mesmo painel. Não é
streaming: os logs são atualizados por polling usando o endpoint existente.
Há pausa/retomada, remoção de painel e opção de seguir a saída automaticamente.
Desmarque “Seguir saída” para ler linhas anteriores sem perder a posição.
Consultas são canceladas ao pausar, remover ou sair da seção/ocultar a aba; os
painéis retomam ao voltar. Falhas preservam a última saída e tentam novamente.
Os painéis não são persistidos após recarregar a página. Volumes mostra um aviso de integração
pendente; ainda não existe endpoint de volumes no backend.

## Build e futuro deploy

```bash
npm run check
npm test
npm run build
npm run preview
```

Publique `dist/` em servidor estático. No deploy, configure um reverse proxy na
mesma origem que encaminhe `/api/*` ao backend, removendo `/api`. O proxy Vite é
usado somente em desenvolvimento/preview e não faz parte de `dist/`. `preview`
é apenas para verificar o build, não para servir em produção.

O backend deve continuar próximo ao Docker que administra. Antes de acesso remoto,
precisaremos adicionar autenticação e proteção das operações. A implantação não
faz parte desta sprint. As fontes externas têm fallback para sans-serif caso
Google Fonts não esteja disponível.

## Verificação desta entrega

TypeScript e build aprovados. Bundle JavaScript: cerca de 2 KB gzip; CSS: cerca de
2,2 KB gzip, sem contar fontes externas. Página retornou HTTP 200 e o proxy consultou
saúde e seis containers reais na API local. Ainda falta conferir o fluxo visual
no navegador: busca, ações, confirmações, logs e comportamento em tela pequena.
Não houve automação de navegador nesta sessão.

O acompanhamento automático tem quatro testes de cancelamento, respostas antigas,
consultas sem sobreposição e recuperação independente entre três aplicações.
Os testes usam suporte nativo a TypeScript do Node (22.18+; recomendado 24 LTS).
