"""MCP Jornada — cliente externo do timesheet pessoal Jornada.

Regra de ouro (ver mcp-jornada-SPEC.md, ponto 4):
  - LER  -> SQLite direto, sempre read-only (nao briga com o write do FastAPI).
  - ESCREVER -> sempre via API REST (o service calcula duracao, normaliza status).

Opcao A da Ferramenta 6: este MCP NAO fala com o MCP qualitor.
Ele so prepara o payload (`jornada_preparar_lancamento`) e marca como lancado
depois (`jornada_marcar_lancado`). Quem chama o qualitor no meio e o agente.

Config por env:
  JORNADA_URL  base da API           (default http://127.0.0.1:7734)
  JORNADA_DB   caminho do jornada.db (default: repo pai deste arquivo)
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("JORNADA_URL", "http://127.0.0.1:7734").rstrip("/")
DEFAULT_DB = Path(__file__).resolve().parent.parent / "jornada.db"
DB_PATH = Path(os.environ.get("JORNADA_DB", str(DEFAULT_DB)))

mcp = FastMCP("jornada")


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def _db() -> sqlite3.Connection:
    """Abre o jornada.db em modo somente-leitura. Nunca escreve."""
    if not DB_PATH.exists():
        raise RuntimeError(f"jornada.db nao encontrado em {DB_PATH}. Defina JORNADA_DB.")
    uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _api() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=15.0)


def _ensure_up() -> None:
    """Health check. O MCP nao sobe o servidor — so avisa se estiver down."""
    try:
        with _api() as c:
            r = c.get("/api/health")
            r.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Jornada nao responde em {BASE_URL} ({exc}). Abra o app antes."
        ) from exc


def _hhmm(t: Optional[str]) -> Optional[str]:
    """Normaliza 'HH:MM[:SS]' -> 'HH:MM' (o banco guarda com segundos)."""
    if not t:
        return None
    return str(t)[:5]


# ----------------------------------------------------------------------------
# 1. listar atividades (leitura ampla — SQLite direto)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_listar_atividades(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    portal_status: Optional[str] = None,
    com_chamado: Optional[bool] = None,
    chamado_numero: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Lista atividades com filtros (todas as datas), cada uma ja com
    `chamado_numero` resolvido via join. Cobre o caso recorrente
    'todos os pendentes com chamado' que hoje exige SQL manual.

    Args:
        data_inicio: 'YYYY-MM-DD' inclusive (opcional).
        data_fim: 'YYYY-MM-DD' inclusive (opcional).
        portal_status: 'pendente' | 'lancado' (opcional).
        com_chamado: True = so com chamado vinculado; False = so sem.
        chamado_numero: filtra pelo numero visivel do Qualitor.
    """
    where = []
    params: list[Any] = []
    if data_inicio:
        where.append("a.data_referencia >= ?")
        params.append(data_inicio)
    if data_fim:
        where.append("a.data_referencia <= ?")
        params.append(data_fim)
    if portal_status:
        where.append("UPPER(a.portal_status) = ?")
        params.append(portal_status.upper())
    if com_chamado is True:
        where.append("a.chamado_id IS NOT NULL")
    elif com_chamado is False:
        where.append("a.chamado_id IS NULL")
    if chamado_numero:
        where.append("c.numero = ?")
        params.append(chamado_numero)

    sql = (
        "SELECT a.id, a.data_referencia, a.hora_inicio, a.hora_fim, "
        "a.duracao_minutos, a.descricao, LOWER(a.portal_status) AS portal_status, "
        "a.chamado_id, a.chamado_status_id, c.numero AS chamado_numero, "
        "c.titulo AS chamado_titulo "
        "FROM atividade a LEFT JOIN chamado c ON c.id = a.chamado_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY a.data_referencia, a.hora_inicio"

    with _db() as conn:
        rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["hora_inicio"] = _hhmm(d["hora_inicio"])
        d["hora_fim"] = _hhmm(d["hora_fim"])
        out.append(d)
    return out


# ----------------------------------------------------------------------------
# 2. criar atividade (escrita — via API, UTF-8 nativo, sem shell)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_criar_atividade(
    data_referencia: str,
    hora_inicio: str,
    hora_fim: str,
    descricao: str,
    chamado_id: Optional[int] = None,
) -> dict[str, Any]:
    """Cria uma atividade (acompanhamento). `duracao_minutos` e calculada pelo
    service — nao enviar. `chamado_id` fica nulo por padrao (vinculo depois).

    Args:
        data_referencia: 'YYYY-MM-DD'.
        hora_inicio: 'HH:MM'.
        hora_fim: 'HH:MM'.
        descricao: texto (acentos/travessao ok — vai como JSON UTF-8).
        chamado_id: id interno do Jornada (opcional).
    """
    _ensure_up()
    body: dict[str, Any] = {
        "data_referencia": data_referencia,
        "hora_inicio": hora_inicio,
        "hora_fim": hora_fim,
        "descricao": descricao,
    }
    if chamado_id is not None:
        body["chamado_id"] = chamado_id
    with _api() as c:
        r = c.post("/api/v1/atividades/", json=body)
        r.raise_for_status()
        return r.json()


# ----------------------------------------------------------------------------
# 3. atualizar atividade (escrita — via API)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_atualizar_atividade(
    atividade_id: int,
    data_referencia: Optional[str] = None,
    hora_inicio: Optional[str] = None,
    hora_fim: Optional[str] = None,
    descricao: Optional[str] = None,
    portal_status: Optional[str] = None,
    chamado_id: Optional[int] = None,
    chamado_status_id: Optional[int] = None,
) -> dict[str, Any]:
    """PATCH parcial numa atividade. So os campos informados sao alterados.
    Usado pra marcar `portal_status='lancado'`, vincular chamado, corrigir horario.
    """
    _ensure_up()
    body: dict[str, Any] = {}
    for k, v in {
        "data_referencia": data_referencia,
        "hora_inicio": hora_inicio,
        "hora_fim": hora_fim,
        "descricao": descricao,
        "portal_status": portal_status,
        "chamado_id": chamado_id,
        "chamado_status_id": chamado_status_id,
    }.items():
        if v is not None:
            body[k] = v
    if not body:
        raise ValueError("Nada pra atualizar: informe ao menos um campo.")
    with _api() as c:
        r = c.patch(f"/api/v1/atividades/{atividade_id}", json=body)
        r.raise_for_status()
        return r.json()


# ----------------------------------------------------------------------------
# 4. ler sprint (leitura — SQLite direto; sem endpoint JSON)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_ler_sprint(sprint_id: Optional[int] = None) -> dict[str, Any]:
    """Le o markdown de uma sprint. Sem `sprint_id`, retorna a mais recente
    por `data_fim`. A API do Jornada so tem HTML fragment — por isso SQLite.
    """
    with _db() as conn:
        if sprint_id is not None:
            row = conn.execute("SELECT * FROM sprint WHERE id = ?", (sprint_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM sprint ORDER BY data_fim DESC LIMIT 1").fetchone()
    if row is None:
        raise ValueError("Sprint nao encontrada.")
    return dict(row)


# ----------------------------------------------------------------------------
# 5. resolver chamado (leitura — helper id <-> numero)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_resolver_chamado(
    chamado_id: Optional[int] = None,
    numero: Optional[str] = None,
) -> dict[str, Any]:
    """Dado `chamado_id` OU `numero`, retorna {id, numero, titulo}. O Qualitor
    usa o `numero` visivel, nao o id interno do Jornada.
    """
    if (chamado_id is None) == (numero is None):
        raise ValueError("Informe exatamente um: chamado_id OU numero.")
    with _db() as conn:
        if chamado_id is not None:
            row = conn.execute(
                "SELECT id, numero, titulo FROM chamado WHERE id = ?", (chamado_id,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id, numero, titulo FROM chamado WHERE numero = ?", (numero,)
            ).fetchone()
    if row is None:
        raise ValueError("Chamado nao encontrado.")
    return dict(row)


# ----------------------------------------------------------------------------
# 5b. criar chamado (escrita — via API)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_criar_chamado(
    numero: str,
    titulo: str,
    descricao: Optional[str] = None,
    categoria_id: Optional[int] = None,
    status_id: Optional[int] = None,
) -> dict[str, Any]:
    """Cria um chamado no Jornada.

    Args:
        numero: numero visivel do Qualitor (nao o id interno).
        titulo: titulo curto do chamado.
        descricao: texto opcional (acentos ok — vai como JSON UTF-8).
        categoria_id: id da categoria (ver jornada.db, tabela chamado_categoria).
        status_id: id do status (ver tabela chamado_status).
    """
    _ensure_up()
    body: dict[str, Any] = {"numero": numero, "titulo": titulo}
    for k, v in {
        "descricao": descricao,
        "categoria_id": categoria_id,
        "status_id": status_id,
    }.items():
        if v is not None:
            body[k] = v
    with _api() as c:
        r = c.post("/api/v1/chamados/", json=body)
        r.raise_for_status()
        return r.json()


# ----------------------------------------------------------------------------
# 6. Ferramenta combinada — OPCAO A (nao chama o qualitor)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_preparar_lancamento(atividade_id: int) -> dict[str, Any]:
    """Monta o payload pronto pro `qualitor_registrar_horas` a partir de uma
    atividade. NAO chama o qualitor — o agente faz isso e depois chama
    `jornada_marcar_lancado`.

    Retorna: {numero, inicio, fim, descricao, chamado_titulo, atividade_id}
    onde inicio/fim ja estao em 'YYYY-MM-DD HH:MM' (formato do qualitor).
    Erro se a atividade nao tiver chamado vinculado.
    """
    _ensure_up()
    with _api() as c:
        r = c.get(f"/api/v1/atividade/{atividade_id}")
        r.raise_for_status()
        ativ = r.json()
    if not ativ.get("chamado_id"):
        raise ValueError(
            f"Atividade {atividade_id} sem chamado vinculado — nao da pra lancar."
        )
    chamado = jornada_resolver_chamado(chamado_id=ativ["chamado_id"])
    data = ativ["data_referencia"]
    ini = _hhmm(ativ.get("hora_inicio"))
    fim = _hhmm(ativ.get("hora_fim"))
    if not ini or not fim:
        raise ValueError(f"Atividade {atividade_id} sem hora_inicio/hora_fim.")
    return {
        "atividade_id": atividade_id,
        "numero": chamado["numero"],
        "chamado_titulo": chamado["titulo"],
        "inicio": f"{data} {ini}",
        "fim": f"{data} {fim}",
        "descricao": ativ["descricao"],
    }


@mcp.tool()
def jornada_marcar_lancado(atividade_id: int) -> dict[str, Any]:
    """Marca a atividade como `portal_status='lancado'`. Chamar SO depois de
    confirmar o lancamento no Qualitor (via qualitor_horas).
    """
    return jornada_atualizar_atividade(atividade_id, portal_status="lancado")


# ----------------------------------------------------------------------------
# 7. resumo do dia (leitura) — total vs meta + blocos + buracos
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_resumo_dia(
    data: str,
    meta_min_horas: float = 6.0,
    meta_max_horas: float = 7.5,
) -> dict[str, Any]:
    """Resumo de um dia: total de minutos vs meta (default 6h-7:30), blocos
    sequenciais e buracos entre eles. Leitura pura.

    Args:
        data: 'YYYY-MM-DD'.
        meta_min_horas: piso da meta em horas (default 6.0).
        meta_max_horas: teto da meta em horas (default 7.5).
    """
    with _db() as conn:
        rows = conn.execute(
            "SELECT a.id, a.hora_inicio, a.hora_fim, a.duracao_minutos, a.descricao, "
            "LOWER(a.portal_status) AS portal_status, c.numero AS chamado_numero "
            "FROM atividade a LEFT JOIN chamado c ON c.id = a.chamado_id "
            "WHERE a.data_referencia = ? ORDER BY a.hora_inicio",
            (data,),
        ).fetchall()
    blocos = []
    for r in rows:
        blocos.append({
            "id": r["id"],
            "hora_inicio": _hhmm(r["hora_inicio"]),
            "hora_fim": _hhmm(r["hora_fim"]),
            "duracao_minutos": r["duracao_minutos"],
            "portal_status": r["portal_status"],
            "chamado_numero": r["chamado_numero"],
            "descricao": r["descricao"],
        })
    total = sum(b["duracao_minutos"] for b in blocos)
    meta_min = int(round(meta_min_horas * 60))
    meta_max = int(round(meta_max_horas * 60))
    buracos = []
    for prev, nxt in zip(blocos, blocos[1:]):
        if prev["hora_fim"] and nxt["hora_inicio"] and nxt["hora_inicio"] > prev["hora_fim"]:
            buracos.append({"de": prev["hora_fim"], "ate": nxt["hora_inicio"]})
    return {
        "data": data,
        "total_minutos": total,
        "total_horas": round(total / 60, 2),
        "meta_min_minutos": meta_min,
        "meta_max_minutos": meta_max,
        "dentro_meta": meta_min <= total <= meta_max,
        "faltam_para_min": max(0, meta_min - total),
        "qtd_blocos": len(blocos),
        "buracos": buracos,
        "blocos": blocos,
    }


# ----------------------------------------------------------------------------
# 8. listar chamados (leitura)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_listar_chamados(
    numero: Optional[str] = None,
    titulo: Optional[str] = None,
    categoria_id: Optional[int] = None,
    status_id: Optional[int] = None,
    limite: int = 50,
) -> list[dict[str, Any]]:
    """Lista chamados do Jornada com filtros. `titulo` e busca parcial (LIKE).

    Args:
        numero: numero exato do Qualitor.
        titulo: trecho do titulo (case-insensitive).
        categoria_id / status_id: filtros exatos.
        limite: max de linhas (default 50).
    """
    where = []
    params: list[Any] = []
    if numero:
        where.append("ch.numero = ?")
        params.append(numero)
    if titulo:
        where.append("ch.titulo LIKE ?")
        params.append(f"%{titulo}%")
    if categoria_id is not None:
        where.append("ch.categoria_id = ?")
        params.append(categoria_id)
    if status_id is not None:
        where.append("ch.status_id = ?")
        params.append(status_id)
    sql = (
        "SELECT ch.id, ch.numero, ch.titulo, ch.descricao, ch.categoria_id, "
        "cat.nome AS categoria_nome, ch.status_id, st.nome AS status_nome "
        "FROM chamado ch "
        "LEFT JOIN chamado_categoria cat ON cat.id = ch.categoria_id "
        "LEFT JOIN chamado_status st ON st.id = ch.status_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY ch.id DESC LIMIT ?"
    params.append(limite)
    with _db() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ----------------------------------------------------------------------------
# 9. pendentes prontos pra lancar (leitura) — agrupados por dia, payload pronto
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_listar_pendentes_para_lancar() -> dict[str, list[dict[str, Any]]]:
    """Pendentes COM chamado vinculado, agrupados por dia, cada um ja com o
    payload pronto pro `qualitor_registrar_horas` (numero, inicio, fim, descricao
    em 'YYYY-MM-DD HH:MM'). Fecha o loop de relancar lotes. Leitura pura — nao
    chama o qualitor nem marca nada.
    """
    with _db() as conn:
        rows = conn.execute(
            "SELECT a.id, a.data_referencia, a.hora_inicio, a.hora_fim, a.descricao, "
            "c.numero AS chamado_numero, c.titulo AS chamado_titulo "
            "FROM atividade a JOIN chamado c ON c.id = a.chamado_id "
            "WHERE UPPER(a.portal_status) = 'PENDENTE' AND a.chamado_id IS NOT NULL "
            "AND a.hora_inicio IS NOT NULL AND a.hora_fim IS NOT NULL "
            "ORDER BY a.data_referencia, a.hora_inicio",
            (),
        ).fetchall()
    por_dia: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        data = r["data_referencia"]
        ini = _hhmm(r["hora_inicio"])
        fim = _hhmm(r["hora_fim"])
        por_dia.setdefault(data, []).append({
            "atividade_id": r["id"],
            "numero": r["chamado_numero"],
            "chamado_titulo": r["chamado_titulo"],
            "inicio": f"{data} {ini}",
            "fim": f"{data} {fim}",
            "descricao": r["descricao"],
        })
    return por_dia


# ----------------------------------------------------------------------------
# 10. ler expediente (leitura) — ponto batido (entrada/saida)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_ler_expediente(
    data: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Le registros de expediente (ponto). Informe `data` (um dia) OU um range
    `data_inicio`/`data_fim`. Sem nenhum, retorna os 30 mais recentes.
    """
    where = []
    params: list[Any] = []
    if data:
        where.append("data = ?")
        params.append(data)
    else:
        if data_inicio:
            where.append("data >= ?")
            params.append(data_inicio)
        if data_fim:
            where.append("data <= ?")
            params.append(data_fim)
    sql = "SELECT data, entrada_1, saida_1, entrada_2, saida_2 FROM expediente"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY data DESC"
    if not where:
        sql += " LIMIT 30"
    with _db() as conn:
        rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        for k in ("entrada_1", "saida_1", "entrada_2", "saida_2"):
            d[k] = _hhmm(d[k])
        out.append(d)
    return out


# ----------------------------------------------------------------------------
# 11. deletar atividade (escrita — via API)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_deletar_atividade(atividade_id: int) -> dict[str, Any]:
    """Apaga uma atividade. Irreversivel. Usa DELETE /api/v1/atividades/{id}."""
    _ensure_up()
    with _api() as c:
        r = c.delete(f"/api/v1/atividades/{atividade_id}")
        r.raise_for_status()
        return {"deletado": True, "atividade_id": atividade_id}


# ----------------------------------------------------------------------------
# 12. atualizar chamado (escrita — via API)
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_atualizar_chamado(
    chamado_id: int,
    numero: Optional[str] = None,
    titulo: Optional[str] = None,
    descricao: Optional[str] = None,
    categoria_id: Optional[int] = None,
    status_id: Optional[int] = None,
) -> dict[str, Any]:
    """PATCH parcial num chamado. So os campos informados sao alterados."""
    _ensure_up()
    body: dict[str, Any] = {}
    for k, v in {
        "numero": numero,
        "titulo": titulo,
        "descricao": descricao,
        "categoria_id": categoria_id,
        "status_id": status_id,
    }.items():
        if v is not None:
            body[k] = v
    if not body:
        raise ValueError("Nada pra atualizar: informe ao menos um campo.")
    with _api() as c:
        r = c.patch(f"/api/v1/chamados/{chamado_id}", json=body)
        r.raise_for_status()
        return r.json()


# ----------------------------------------------------------------------------
# 13. tarefas (quadro Kanban) — LEITURA via SQLite direto, ESCRITA via API
# ----------------------------------------------------------------------------
@mcp.tool()
def jornada_listar_tarefas(
    status: Optional[str] = None,
    prioridade: Optional[str] = None,
    chamado_id: Optional[int] = None,
    chamado_numero: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Lista tarefas do quadro Kanban com filtros (LEITURA — SQLite direto).

    Args:
        status: 'a_fazer' | 'em_andamento' | 'concluido' (opcional).
        prioridade: 'baixa' | 'media' | 'alta' | 'urgente' (opcional).
        chamado_id: id interno do Jornada (opcional).
        chamado_numero: numero visivel do Qualitor (opcional).
    """
    # status/prioridade sao gravados em MAIUSCULO no banco (igual portal_status
    # de atividade) mas a API aceita/retorna minusculo -- normalizar os dois lados.
    where = []
    params: list[Any] = []
    if status:
        where.append("UPPER(t.status) = ?")
        params.append(status.upper())
    if prioridade:
        where.append("UPPER(t.prioridade) = ?")
        params.append(prioridade.upper())
    if chamado_id is not None:
        where.append("t.chamado_id = ?")
        params.append(chamado_id)
    if chamado_numero:
        where.append("c.numero = ?")
        params.append(chamado_numero)
    sql = (
        "SELECT t.id, t.titulo, t.descricao, LOWER(t.status) AS status, "
        "LOWER(t.prioridade) AS prioridade, t.data_prazo, t.data_conclusao, "
        "t.chamado_id, c.numero AS chamado_numero, "
        "c.titulo AS chamado_titulo, t.created_at, t.updated_at "
        "FROM tarefa t LEFT JOIN chamado c ON c.id = t.chamado_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY t.updated_at DESC"
    with _db() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


@mcp.tool()
def jornada_board_tarefas() -> dict[str, list[dict[str, Any]]]:
    """Quadro Kanban (LEITURA — SQLite direto), espelhando tarefa_service.get_board_tarefas:
    agrupa em a_fazer / em_andamento / concluido_recentes (<=7 dias) / concluido_anteriores,
    ordenado por data_prazo (sem prazo ao final).
    """
    with _db() as conn:
        rows = conn.execute(
            "SELECT t.id, t.titulo, t.descricao, LOWER(t.status) AS status, "
            "LOWER(t.prioridade) AS prioridade, t.data_prazo, t.data_conclusao, "
            "t.chamado_id, c.numero AS chamado_numero, "
            "c.titulo AS chamado_titulo, t.updated_at "
            "FROM tarefa t LEFT JOIN chamado c ON c.id = t.chamado_id"
        ).fetchall()
    limite_7dias = (datetime.utcnow() - timedelta(days=7)).isoformat()
    board: dict[str, list[dict[str, Any]]] = {
        "a_fazer": [],
        "em_andamento": [],
        "concluido_recentes": [],
        "concluido_anteriores": [],
    }
    for r in rows:
        d = dict(r)
        if d["status"] == "a_fazer":
            board["a_fazer"].append(d)
        elif d["status"] == "em_andamento":
            board["em_andamento"].append(d)
        elif d["status"] == "concluido":
            ref = d["data_conclusao"] or d["updated_at"]
            if ref and str(ref) >= limite_7dias:
                board["concluido_recentes"].append(d)
            else:
                board["concluido_anteriores"].append(d)
    for grupo in board.values():
        grupo.sort(key=lambda t: (t["data_prazo"] is None, t["data_prazo"] or "9999-12-31"))
    return board


@mcp.tool()
def jornada_criar_tarefa(
    titulo: str,
    descricao: Optional[str] = None,
    status: Optional[str] = None,
    prioridade: Optional[str] = None,
    data_prazo: Optional[str] = None,
    chamado_id: Optional[int] = None,
) -> dict[str, Any]:
    """Cria uma tarefa no quadro Kanban (ESCRITA — via API).

    Args:
        titulo: obrigatorio.
        descricao: opcional.
        status: 'a_fazer' (default) | 'em_andamento' | 'concluido'.
        prioridade: 'baixa' | 'media' (default) | 'alta' | 'urgente'.
        data_prazo: 'YYYY-MM-DD' (opcional).
        chamado_id: id interno do Jornada (opcional, vincula a um chamado).
    """
    _ensure_up()
    body: dict[str, Any] = {"titulo": titulo}
    for k, v in {
        "descricao": descricao,
        "status": status,
        "prioridade": prioridade,
        "data_prazo": data_prazo,
        "chamado_id": chamado_id,
    }.items():
        if v is not None:
            body[k] = v
    with _api() as c:
        r = c.post("/api/v1/tarefas/", json=body)
        r.raise_for_status()
        return r.json()


@mcp.tool()
def jornada_atualizar_tarefa(
    tarefa_id: int,
    titulo: Optional[str] = None,
    descricao: Optional[str] = None,
    status: Optional[str] = None,
    prioridade: Optional[str] = None,
    data_prazo: Optional[str] = None,
    chamado_id: Optional[int] = None,
) -> dict[str, Any]:
    """PATCH parcial numa tarefa (ESCRITA — via API). So os campos informados sao alterados.
    Mudar `status` pra 'concluido' marca `data_conclusao` automaticamente no service;
    sair de 'concluido' limpa `data_conclusao`.
    """
    _ensure_up()
    body: dict[str, Any] = {}
    for k, v in {
        "titulo": titulo,
        "descricao": descricao,
        "status": status,
        "prioridade": prioridade,
        "data_prazo": data_prazo,
        "chamado_id": chamado_id,
    }.items():
        if v is not None:
            body[k] = v
    if not body:
        raise ValueError("Nada pra atualizar: informe ao menos um campo.")
    with _api() as c:
        r = c.patch(f"/api/v1/tarefas/{tarefa_id}", json=body)
        r.raise_for_status()
        return r.json()


@mcp.tool()
def jornada_deletar_tarefa(tarefa_id: int) -> dict[str, Any]:
    """Apaga uma tarefa. Irreversivel. Usa DELETE /api/v1/tarefas/{id}."""
    _ensure_up()
    with _api() as c:
        r = c.delete(f"/api/v1/tarefas/{tarefa_id}")
        r.raise_for_status()
        return {"deletado": True, "tarefa_id": tarefa_id}


if __name__ == "__main__":
    mcp.run()


