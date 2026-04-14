from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database import get_session
from app import schemas
from app.services import chamado_categoria_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =============================================================================
# Páginas
# =============================================================================

@router.get("/categorias-chamado")
def page_categorias_chamado(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/chamado_categorias.html", 
        context={
            "title": "Jornada - Categorias de Chamado",
            "page_title": "Categorias de Chamado",
            "active_page": "categorias_chamado"
        }
    )

# =============================================================================
# HTMX
# =============================================================================

def _render_categorias_list(request: Request, session: Session):
    """Helper: renderiza a lista de categorias."""
    categorias = chamado_categoria_service.get_categorias(session)
    return templates.TemplateResponse(
        "partials/chamado_categorias_list.html",
        {"request": request, "categorias": categorias}
    )

@router.get("/htmx/categorias-chamado/list")
def htmx_list_categorias(request: Request, session: Session = Depends(get_session)):
    return _render_categorias_list(request, session)

@router.post("/htmx/categorias-chamado")
async def htmx_create_categoria(
    request: Request,
    nome: str = Form(...),
    cor: str = Form("#333333"),
    session: Session = Depends(get_session)
):
    cat_in = schemas.ChamadoCategoriaCreate(nome=nome, cor=cor)
    chamado_categoria_service.create_categoria(session, cat_in)
    return _render_categorias_list(request, session)

@router.get("/htmx/categorias-chamado/form-new")
def htmx_get_new_categoria_form(request: Request):
    return templates.TemplateResponse("partials/categoria_form.html", {"request": request, "categoria": None})

@router.get("/htmx/categorias-chamado/{categoria_id}/form-edit")
def htmx_get_categoria_form(request: Request, categoria_id: int, session: Session = Depends(get_session)):
    import app.models as models
    categoria = session.get(models.ChamadoCategoria, categoria_id)
    return templates.TemplateResponse("partials/categoria_form.html", {"request": request, "categoria": categoria})

@router.patch("/htmx/categorias-chamado/{categoria_id}")
async def htmx_update_categoria(
    request: Request,
    categoria_id: int,
    nome: str = Form(...),
    cor: str = Form("#333333"),
    session: Session = Depends(get_session)
):
    cat_update = schemas.ChamadoCategoriaUpdate(nome=nome, cor=cor)
    chamado_categoria_service.update_categoria(session, categoria_id, cat_update)
    return _render_categorias_list(request, session)

@router.delete("/htmx/categorias-chamado/{categoria_id}")
def htmx_delete_categoria(request: Request, categoria_id: int, session: Session = Depends(get_session)):
    chamado_categoria_service.delete_categoria(session, categoria_id)
    return _render_categorias_list(request, session)
