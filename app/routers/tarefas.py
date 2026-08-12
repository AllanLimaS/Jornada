from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from typing import Optional, List
from datetime import date

from app.database import get_session
from app import schemas, models
from app.services import tarefa_service, chamado_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =============================================================================
# Páginas
# =============================================================================

@router.get("/tarefas")
def page_tarefas(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(
        request=request,
        name="pages/tarefas.html",
        context={
            "title": "Jornada - Tarefas",
            "page_title": "Tarefas",
            "active_page": "tarefas"
        }
    )

# =============================================================================
# API REST — /api/v1/tarefas
# =============================================================================

@router.post("/api/v1/tarefas/", response_model=schemas.TarefaRead)
def api_create_tarefa(tarefa: schemas.TarefaCreate, session: Session = Depends(get_session)):
    return tarefa_service.create_tarefa(session, tarefa)

@router.get("/api/v1/tarefas/", response_model=List[schemas.TarefaRead])
def api_list_tarefas(session: Session = Depends(get_session)):
    board = tarefa_service.get_board_tarefas(session)
    # Retorna todas as tarefas em lista única
    return board["a_fazer"] + board["em_andamento"] + board["concluido_recentes"] + board["concluido_anteriores"]

@router.get("/api/v1/tarefas/{tarefa_id}", response_model=schemas.TarefaRead)
def api_get_tarefa(tarefa_id: int, session: Session = Depends(get_session)):
    return tarefa_service.get_tarefa(session, tarefa_id)

@router.patch("/api/v1/tarefas/{tarefa_id}", response_model=schemas.TarefaRead)
def api_update_tarefa(tarefa_id: int, tarefa: schemas.TarefaUpdate, session: Session = Depends(get_session)):
    return tarefa_service.update_tarefa(session, tarefa_id, tarefa)

@router.delete("/api/v1/tarefas/{tarefa_id}")
def api_delete_tarefa(tarefa_id: int, session: Session = Depends(get_session)):
    return tarefa_service.delete_tarefa(session, tarefa_id)

# =============================================================================
# HTMX — /htmx/tarefas
# =============================================================================

@router.get("/htmx/tarefas/board")
def htmx_get_board(request: Request, session: Session = Depends(get_session)):
    board = tarefa_service.get_board_tarefas(session)
    return templates.TemplateResponse(
        request=request,
        name="partials/tarefas_board.html",
        context={"board": board, "today": date.today()}
    )

@router.get("/htmx/tarefas/form-new")
def htmx_form_new_tarefa(request: Request, session: Session = Depends(get_session)):
    chamados = chamado_service.get_chamados(session, limit=200)
    return templates.TemplateResponse(
        request=request,
        name="partials/tarefa_form_modal.html",
        context={
            "tarefa": None,
            "chamados": chamados,
            "statuses": [e.value for e in models.TarefaStatus],
            "prioridades": [e.value for e in models.TarefaPrioridade]
        }
    )

@router.get("/htmx/tarefas/{tarefa_id}/modal")
def htmx_form_edit_tarefa(tarefa_id: int, request: Request, session: Session = Depends(get_session)):
    tarefa = tarefa_service.get_tarefa(session, tarefa_id)
    chamados = chamado_service.get_chamados(session, limit=200)
    return templates.TemplateResponse(
        request=request,
        name="partials/tarefa_form_modal.html",
        context={
            "tarefa": tarefa,
            "chamados": chamados,
            "statuses": [e.value for e in models.TarefaStatus],
            "prioridades": [e.value for e in models.TarefaPrioridade]
        }
    )

@router.post("/htmx/tarefas")
def htmx_create_tarefa(
    request: Request,
    titulo: str = Form(...),
    descricao: Optional[str] = Form(None),
    status: str = Form("a_fazer"),
    prioridade: str = Form("media"),
    data_prazo: Optional[str] = Form(None),
    chamado_id: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    dt_prazo = date.fromisoformat(data_prazo) if data_prazo and data_prazo.strip() else None
    ch_id = int(chamado_id) if chamado_id and chamado_id.strip() else None

    tarefa_in = schemas.TarefaCreate(
        titulo=titulo.strip(),
        descricao=descricao.strip() if descricao and descricao.strip() else None,
        status=models.TarefaStatus(status),
        prioridade=models.TarefaPrioridade(prioridade),
        data_prazo=dt_prazo,
        chamado_id=ch_id
    )
    tarefa_service.create_tarefa(session, tarefa_in)

    board = tarefa_service.get_board_tarefas(session)
    return templates.TemplateResponse(
        request=request,
        name="partials/tarefas_board.html",
        context={"board": board, "today": date.today()}
    )

@router.post("/htmx/tarefas/{tarefa_id}/update")
def htmx_update_tarefa(
    tarefa_id: int,
    request: Request,
    titulo: str = Form(...),
    descricao: Optional[str] = Form(None),
    status: str = Form("a_fazer"),
    prioridade: str = Form("media"),
    data_prazo: Optional[str] = Form(None),
    chamado_id: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    dt_prazo = date.fromisoformat(data_prazo) if data_prazo and data_prazo.strip() else None
    ch_id = int(chamado_id) if chamado_id and chamado_id.strip() else None

    tarefa_in = schemas.TarefaUpdate(
        titulo=titulo.strip(),
        descricao=descricao.strip() if descricao and descricao.strip() else None,
        status=models.TarefaStatus(status),
        prioridade=models.TarefaPrioridade(prioridade),
        data_prazo=dt_prazo,
        chamado_id=ch_id
    )
    tarefa_service.update_tarefa(session, tarefa_id, tarefa_in)

    board = tarefa_service.get_board_tarefas(session)
    return templates.TemplateResponse(
        request=request,
        name="partials/tarefas_board.html",
        context={"board": board, "today": date.today()}
    )

@router.delete("/htmx/tarefas/{tarefa_id}")
def htmx_delete_tarefa(tarefa_id: int, request: Request, session: Session = Depends(get_session)):
    tarefa_service.delete_tarefa(session, tarefa_id)
    board = tarefa_service.get_board_tarefas(session)
    return templates.TemplateResponse(
        request=request,
        name="partials/tarefas_board.html",
        context={"board": board, "today": date.today()}
    )
