from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database import get_session
from app import schemas, models
from app.services import chamado_status_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =============================================================================
# Páginas
# =============================================================================

@router.get("/status-chamado")
def page_status_chamado(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/chamado_status.html", 
        context={
            "title": "Jornada - Status de Chamado",
            "page_title": "Status de Chamado",
            "active_page": "status_chamado"
        }
    )

# =============================================================================
# HTMX
# =============================================================================

def _render_status_list(request: Request, session: Session):
    """Helper: renderiza a lista de status."""
    statuses = chamado_status_service.get_statuses(session)
    return templates.TemplateResponse(
        "partials/chamado_status_list.html",
        {"request": request, "statuses": statuses}
    )

@router.get("/htmx/status-chamado/list")
def htmx_list_status(request: Request, session: Session = Depends(get_session)):
    return _render_status_list(request, session)

@router.post("/htmx/status-chamado")
async def htmx_create_status(
    request: Request,
    nome: str = Form(...),
    cor: str = Form("#3B82F6"),
    session: Session = Depends(get_session)
):
    status_in = schemas.ChamadoStatusCreate(nome=nome, cor=cor)
    chamado_status_service.create_status(session, status_in)
    return _render_status_list(request, session)

@router.delete("/htmx/status-chamado/{status_id}")
def htmx_delete_status(request: Request, status_id: int, session: Session = Depends(get_session)):
    chamado_status_service.delete_status(session, status_id)
    return _render_status_list(request, session)
