from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from datetime import date as date_type, time
from typing import Optional, List

from app.database import get_session
from app import schemas, models
from app.services import atividade_service, chamado_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =============================================================================
# Páginas
# =============================================================================

@router.get("/")
def page_hoje(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/hoje.html", 
        context={
            "title": "Jornada - Hoje",
            "page_title": "Hoje",
            "active_page": "hoje",
            "hoje_date": date_type.today().strftime("%Y-%m-%d")
        }
    )

@router.get("/atividades-lista")
def page_atividades_lista(request: Request):
    """Página de listagem histórica de atividades (antigos acompanhamentos)."""
    return templates.TemplateResponse(
        request=request, 
        name="pages/atividades.html", 
        context={
            "title": "Jornada - Atividades",
            "page_title": "Atividades",
            "active_page": "atividades_lista"
        }
    )

@router.get("/calendario")
def page_calendario(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/calendario.html", 
        context={
            "title": "Jornada - Calendário",
            "page_title": "Calendário",
            "active_page": "calendario"
        }
    )

# =============================================================================
# API REST — /api/v1/atividades
# =============================================================================

@router.post("/api/v1/atividades/", response_model=schemas.AtividadeRead)
def api_create_atividade(atividade: schemas.AtividadeCreate, session: Session = Depends(get_session)):
    return atividade_service.create_atividade(session, atividade)

@router.get("/api/v1/atividades/{data_ref}", response_model=List[schemas.AtividadeRead])
def api_list_atividades_by_date(data_ref: date_type, session: Session = Depends(get_session)):
    return atividade_service.get_atividades_by_date(session, data_ref)

@router.get("/api/v1/atividade/{atividade_id}", response_model=schemas.AtividadeRead)
def api_get_atividade(atividade_id: int, session: Session = Depends(get_session)):
    return atividade_service.get_atividade(session, atividade_id)

@router.patch("/api/v1/atividades/{atividade_id}", response_model=schemas.AtividadeRead)
def api_update_atividade(atividade_id: int, atividade: schemas.AtividadeUpdate, session: Session = Depends(get_session)):
    return atividade_service.update_atividade(session, atividade_id, atividade)

@router.delete("/api/v1/atividades/{atividade_id}")
def api_delete_atividade(atividade_id: int, session: Session = Depends(get_session)):
    return atividade_service.delete_atividade(session, atividade_id)

# =============================================================================
# HTMX — /htmx/atividades
# =============================================================================

def _build_chamados_map(session: Session, atividades):
    """Helper: constrói mapa {chamado_id: Chamado} para exibir títulos."""
    ids = [atv.chamado_id for atv in atividades if atv.chamado_id]
    return chamado_service.get_chamados_map(session, ids) if ids else {}

def _render_timeline(request: Request, session: Session, data_ref: date_type):
    """Helper: renderiza a timeline de atividades de uma data específica."""
    atividades = atividade_service.get_atividades_by_date(session, data_ref)
    atividades.sort(key=lambda x: x.hora_inicio)
    total_minutos = sum(atv.duracao_minutos for atv in atividades)
    horas = total_minutos // 60
    minutos = total_minutos % 60
    chamados_map = _build_chamados_map(session, atividades)
    is_today = (data_ref == date_type.today())
    
    # Cálculo de horário dinâmico para a agenda (Mínimo 08h e Máximo 18h)
    min_h = 8
    max_h = 18
    for atv in atividades:
        if atv.hora_inicio.hour < min_h:
            min_h = atv.hora_inicio.hour
        if atv.hora_fim.hour >= max_h:
            max_h = atv.hora_fim.hour + 1
            
    return templates.TemplateResponse(
        request=request,
        name="partials/timeline_list.html",
        context={
            "atividades": atividades, 
            "total_horas": horas, 
            "total_minutos": minutos, 
            "chamados_map": chamados_map,
            "is_today": is_today,
            "min_h": min_h,
            "max_h": max_h
        }
    )

@router.get("/htmx/atividades/calendario")
def htmx_calendario_timeline(request: Request, data_ref: date_type, session: Session = Depends(get_session)):
    return _render_timeline(request, session, data_ref)

@router.get("/htmx/atividades/form-new")
def htmx_form_new_atividade(request: Request):
    return templates.TemplateResponse(
        "partials/atividade_form.html",
        {"request": request, "atividade": None, "hoje_date": date_type.today().strftime("%Y-%m-%d")}
    )

@router.get("/htmx/atividades/{id}/form-edit")
def htmx_form_edit_atividade(request: Request, id: int, edit_context: str = "hoje", session: Session = Depends(get_session)):
    atividade = session.get(models.Atividade, id)
    chamados_map = _build_chamados_map(session, [atividade]) if atividade else {}
    return templates.TemplateResponse(
        "partials/atividade_form.html",
        {"request": request, "atividade": atividade, "chamados_map": chamados_map, "edit_context": edit_context}
    )

@router.get("/htmx/atividades/timeline")
def htmx_timeline_today(request: Request, session: Session = Depends(get_session)):
    return _render_timeline(request, session, date_type.today())

@router.post("/htmx/atividades")
async def htmx_create_atividade(
    request: Request,
    data_referencia: date_type = Form(...),
    hora_inicio: time = Form(...),
    hora_fim: time = Form(...),
    descricao: str = Form(...),
    portal_status: str = Form("pendente"),
    chamado_id: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    c_id = None
    if chamado_id and chamado_id.strip():
        try: c_id = int(chamado_id)
        except ValueError: pass

    try:
        atividade_in = schemas.AtividadeCreate(
            data_referencia=data_referencia,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            descricao=descricao,
            portal_status=models.AtividadePortalStatus(portal_status),
            chamado_id=c_id
        )
        atividade_service.create_atividade(session, atividade_in)
    except HTTPException as e:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(str(e.detail), status_code=400)

    response = _render_timeline(request, session, data_referencia)
    response.headers["HX-Trigger"] = "closeModal"
    return response

@router.patch("/htmx/atividades/{atividade_id}")
async def htmx_edit_atividade(
    request: Request,
    atividade_id: int,
    data_referencia: date_type = Form(...),
    hora_inicio: time = Form(...),
    hora_fim: time = Form(...),
    descricao: str = Form(...),
    portal_status: str = Form("pendente"),
    chamado_id: Optional[str] = Form(None),
    edit_context: str = Form("hoje"),
    session: Session = Depends(get_session)
):
    c_id = None
    if chamado_id and chamado_id.strip():
        try: c_id = int(chamado_id)
        except ValueError: pass

    try:
        update_data = schemas.AtividadeUpdate(
            data_referencia=data_referencia,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            descricao=descricao,
            portal_status=models.AtividadePortalStatus(portal_status),
            chamado_id=c_id
        )
        atividade_service.update_atividade(session, atividade_id, update_data)
    except HTTPException as e:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(str(e.detail), status_code=400)
    
    # Retorna o conteúdo correto dependendo do contexto da edição
    if edit_context == "atividades":
        response = htmx_atividades_lista_content(request, "todos", session)
    else:
        response = _render_timeline(request, session, data_referencia)
    
    response.headers["HX-Trigger"] = "closeModal"
    return response

@router.delete("/htmx/atividades/{atividade_id}")
def htmx_delete_atividade(request: Request, atividade_id: int, session: Session = Depends(get_session)):
    atv = atividade_service.get_atividade(session, atividade_id)
    if atv:
        data_ref = atv.data_referencia
        atividade_service.delete_atividade(session, atividade_id)
        return _render_timeline(request, session, data_ref)
    return "Removido"

@router.patch("/htmx/atividades/{atividade_id}/status")
async def htmx_update_atividade_status(
    request: Request, 
    atividade_id: int, 
    status: str = Form(...), 
    aba: str = Form("todos"),
    session: Session = Depends(get_session)
):
    atividade = atividade_service.get_atividade(session, atividade_id)
    if atividade:
        update_data = schemas.AtividadeUpdate(portal_status=models.AtividadePortalStatus(status))
        atividade_service.update_atividade(session, atividade_id, update_data)
    return htmx_atividades_lista_content(request, aba, session)

@router.get("/htmx/atividades/lista")
def htmx_atividades_lista_content(request: Request, aba: str = "todos", session: Session = Depends(get_session)):
    atividades = atividade_service.get_atividades_by_status(session, aba)
    chamados_map = _build_chamados_map(session, atividades)
    return templates.TemplateResponse(
        "partials/atividades_list.html",
        {"request": request, "atividades": atividades, "aba": aba, "chamados_map": chamados_map}
    )

# --- Chamado Picker (popup de seleção de chamado no formulário) ---

@router.get("/htmx/chamado-picker")
def htmx_chamado_picker(request: Request, session: Session = Depends(get_session)):
    """Retorna o conteúdo inicial do picker: 10 chamados recentes com atividades."""
    chamados = chamado_service.get_chamados_recentes(session, limit=10)
    return templates.TemplateResponse(
        "partials/chamado_picker_results.html",
        {"request": request, "chamados": chamados, "is_search": False}
    )

@router.get("/htmx/chamado-picker/search")
def htmx_chamado_picker_search(request: Request, q: str = "", session: Session = Depends(get_session)):
    """Busca chamados por título/número para o picker."""
    if q.strip():
        chamados = chamado_service.search_chamados(session, query=q.strip(), limit=10)
    else:
        chamados = chamado_service.get_chamados_recentes(session, limit=10)
    return templates.TemplateResponse(
        "partials/chamado_picker_results.html",
        {"request": request, "chamados": chamados, "is_search": bool(q.strip())}
    )
