from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =============================================================================
# Páginas avulsas (sem domínio específico)
# =============================================================================

@router.get("/sprint")
def page_sprint(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="pages/sprint.html", 
        context={
            "title": "Jornada - Sprint",
            "page_title": "Sprint",
            "active_page": "sprint"
        }
    )
