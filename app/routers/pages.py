from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =============================================================================
# Páginas avulsas (sem domínio específico)
# =============================================================================

@router.get("/relatorios")
def page_relatorios(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/relatorios.html", 
        context={
            "title": "Jornada - Relatórios",
            "page_title": "Relatórios",
            "active_page": "relatorios"
        }
    )
