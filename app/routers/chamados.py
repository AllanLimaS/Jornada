from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from typing import Optional, List

from app.database import get_session
from app import schemas, models
from app.services import chamado_service, chamado_categoria_service, chamado_status_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =============================================================================
# Páginas
# =============================================================================

@router.get("/chamados")
def page_chamados(request: Request, session: Session = Depends(get_session)):
    categorias = chamado_categoria_service.get_categorias(session)
    statuses = chamado_status_service.get_statuses(session)
    return templates.TemplateResponse(
        request=request, 
        name="pages/chamados.html", 
        context={
            "title": "Jornada - Chamados",
            "page_title": "Chamados",
            "active_page": "chamados",
            "categorias": categorias,
            "statuses": statuses
        }
    )

# =============================================================================
# API REST — /api/v1/chamados
# =============================================================================

@router.post("/api/v1/chamados/", response_model=schemas.ChamadoRead)
def api_create_chamado(chamado: schemas.ChamadoCreate, session: Session = Depends(get_session)):
    return chamado_service.create_chamado(session, chamado)

@router.get("/api/v1/chamados/", response_model=List[schemas.ChamadoRead])
def api_list_chamados(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    return chamado_service.get_chamados(session, skip=skip, limit=limit)

@router.get("/api/v1/chamados/{chamado_id}", response_model=schemas.ChamadoRead)
def api_get_chamado(chamado_id: int, session: Session = Depends(get_session)):
    return chamado_service.get_chamado(session, chamado_id)

@router.patch("/api/v1/chamados/{chamado_id}", response_model=schemas.ChamadoRead)
def api_update_chamado(chamado_id: int, chamado: schemas.ChamadoUpdate, session: Session = Depends(get_session)):
    return chamado_service.update_chamado(session, chamado_id, chamado)

@router.delete("/api/v1/chamados/{chamado_id}")
def api_delete_chamado(chamado_id: int, session: Session = Depends(get_session)):
    return chamado_service.delete_chamado(session, chamado_id)

# =============================================================================
# HTMX — /htmx/chamados
# =============================================================================

def _render_chamados_list(
    request: Request, 
    session: Session, 
    query: Optional[str] = None,
    categoria_id: Optional[int] = None,
    status_id: Optional[int] = None
):
    """Helper: renderiza a lista de chamados, com filtros opcionais."""
    chamados = chamado_service.get_chamados_with_ultima_atv(
        session, query=query, categoria_id=categoria_id, status_id=status_id
    )
    
    return templates.TemplateResponse(
        request=request, 
        name="partials/chamados_list.html", 
        context={
            "chamados": chamados
        }
    )

@router.get("/htmx/chamados/list")
def htmx_list_chamados(
    request: Request, 
    q: Optional[str] = None,
    categoria_id: Optional[str] = None,
    status_id: Optional[str] = None,
    session: Session = Depends(get_session)
):
    c_id = int(categoria_id) if categoria_id and categoria_id.isdigit() else None
    s_id = int(status_id) if status_id and status_id.isdigit() else None
    return _render_chamados_list(request, session, query=q, categoria_id=c_id, status_id=s_id)

@router.get("/htmx/chamados/search")
def htmx_search_chamados(
    request: Request, 
    q: str = "", 
    categoria_id: Optional[str] = None, 
    status_id: Optional[str] = None,
    session: Session = Depends(get_session)
):
    c_id = int(categoria_id) if categoria_id and categoria_id.isdigit() else None
    s_id = int(status_id) if status_id and status_id.isdigit() else None
    return _render_chamados_list(request, session, query=q, categoria_id=c_id, status_id=s_id)

@router.post("/htmx/chamados")
async def htmx_create_chamado(
    request: Request, 
    numero: str = Form(...), 
    titulo: str = Form(...), 
    descricao: str = Form(""),
    categoria_id: Optional[str] = Form(None), 
    status_id: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    c_id = None
    if categoria_id and categoria_id.strip():
        try: c_id = int(categoria_id)
        except ValueError: pass

    s_id = None
    if status_id and status_id.strip():
        try: s_id = int(status_id)
        except ValueError: pass

    chamado_in = schemas.ChamadoCreate(
        numero=numero, 
        titulo=titulo, 
        descricao=descricao if descricao else None,
        categoria_id=c_id, 
        status_id=s_id
    )
    chamado_service.create_chamado(session, chamado_in)
    return _render_chamados_list(request, session)

@router.get("/htmx/chamados/form-new")
def htmx_get_chamado_form_new(request: Request, session: Session = Depends(get_session)):
    """Retorna o formulário para criação de um novo chamado."""
    categorias = chamado_categoria_service.get_categorias(session)
    statuses = chamado_status_service.get_statuses(session)
    return templates.TemplateResponse(
        request=request,
        name="partials/chamado_form.html",
        context={
            "chamado": None,
            "categorias": categorias,
            "statuses": statuses
        }
    )

@router.get("/htmx/chamados/{chamado_id}/modal")
def htmx_get_chamado_modal(
    request: Request, 
    chamado_id: int, 
    session: Session = Depends(get_session)
):
    from app.services import atividade_service
    chamado = chamado_service.get_chamado(session, chamado_id)
    categorias = chamado_categoria_service.get_categorias(session)
    statuses = chamado_status_service.get_statuses(session)
    atividades = atividade_service.get_atividades_by_chamado(session, chamado_id)
    
    return templates.TemplateResponse(
        request=request, 
        name="partials/chamado_form.html", 
        context={
            "chamado": chamado,
            "categorias": categorias,
            "statuses": statuses,
            "atividades": atividades
        }
    )

@router.patch("/htmx/chamados/{chamado_id}")
async def htmx_update_chamado(
    request: Request,
    chamado_id: int,
    numero: str = Form(...),
    titulo: str = Form(...),
    descricao: str = Form(""),
    categoria_id: Optional[str] = Form(None),
    status_id: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    c_id = None
    if categoria_id and categoria_id.strip():
        try: c_id = int(categoria_id)
        except ValueError: pass

    s_id = None
    if status_id and status_id.strip():
        try: s_id = int(status_id)
        except ValueError: pass

    update_data = schemas.ChamadoUpdate(
        numero=numero,
        titulo=titulo,
        descricao=descricao if descricao else None,
        categoria_id=c_id,
        status_id=s_id
    )
    chamado_service.update_chamado(session, chamado_id, update_data)
    return _render_chamados_list(request, session)

@router.get("/htmx/chamados/{chamado_id}/delete-confirm")
def htmx_delete_chamado_confirm(request: Request, chamado_id: int):
    """Poderia ser um modal de confirmação, mas usaremos hx-confirm nativo por enquanto."""
    pass

@router.delete("/htmx/chamados/{chamado_id}")
def htmx_delete_chamado(request: Request, chamado_id: int, session: Session = Depends(get_session)):
    chamado_service.delete_chamado(session, chamado_id)
    return _render_chamados_list(request, session)
