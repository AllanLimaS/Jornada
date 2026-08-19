# MCP Jornada

Servidor MCP que expoe o timesheet Jornada como ferramentas. Cliente externo:
nao mexe no codigo do app, so consome a API REST (escrita) e o SQLite (leitura).

## Ferramentas

| Tool | O que faz | Como |
|------|-----------|------|
| `jornada_listar_atividades` | Lista com filtros (todas as datas), com `chamado_numero` resolvido | SQLite (ro) |
| `jornada_criar_atividade` | Cria acompanhamento (UTF-8 nativo, sem shell) | API POST |
| `jornada_atualizar_atividade` | PATCH parcial (marcar lancado, vincular chamado...) | API PATCH |
| `jornada_ler_sprint` | Markdown de uma sprint (ou a mais recente) | SQLite (ro) |
| `jornada_resolver_chamado` | id <-> numero + titulo | SQLite (ro) |
| `jornada_criar_chamado` | Cria um chamado (numero/titulo/categoria...) | API POST |
| `jornada_preparar_lancamento` | Payload pronto pro `qualitor_registrar_horas` | API GET |
| `jornada_marcar_lancado` | Marca `portal_status=lancado` | API PATCH |
| `jornada_resumo_dia` | Total do dia vs meta + blocos + buracos | SQLite (ro) |
| `jornada_listar_chamados` | Lista chamados com filtros (numero/titulo/cat/status) | SQLite (ro) |
| `jornada_listar_pendentes_para_lancar` | Pendentes c/ chamado por dia, payload pronto | SQLite (ro) |
| `jornada_ler_expediente` | Ponto batido (entrada/saida) por dia ou range | SQLite (ro) |
| `jornada_deletar_atividade` | Apaga atividade (irreversivel) | API DELETE |
| `jornada_atualizar_chamado` | PATCH parcial num chamado | API PATCH |

### Fluxo de lancamento (Opcao A — este MCP NAO fala com o qualitor)

O agente orquestra os 3 passos, cada um com seu MCP:

1. `jornada_preparar_lancamento(atividade_id)` -> `{numero, inicio, fim, descricao}`
2. `qualitor_registrar_horas(numero, inicio, fim, descricao, dry_run=...)`  (MCP qualitor)
3. confirma com `qualitor_horas` e entao `jornada_marcar_lancado(atividade_id)`

## Instalar

VENV PROPRIO (nao compartilhar com o Jornada — o SDK `mcp` puxa starlette novo,
incompativel com o FastAPI 0.110.1 do app e quebra o servidor):

```powershell
cd C:\Users\6512615\Documents\Pessoal\Jornada\mcp
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Registrar no Claude Code

```bash
claude mcp add jornada -- "C:\Users\6512615\Documents\Pessoal\Jornada\mcp\.venv\Scripts\python.exe" "C:\Users\6512615\Documents\Pessoal\Jornada\mcp\server.py"
```

## Config (env, opcional)

| Var | Default |
|-----|---------|
| `JORNADA_URL` | `http://127.0.0.1:7734` |
| `JORNADA_DB` | `jornada.db` na raiz do repo |

## Pre-requisito

O app Jornada precisa estar rodando (abra pelo atalho). As tools de escrita fazem
health check em `/api/health` e falham com mensagem clara se estiver down.



