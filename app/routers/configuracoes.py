from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.database import get_session
from app.services import config_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/configuracoes", response_class=HTMLResponse)
async def get_configuracoes_page(request: Request, session: Session = Depends(get_session)):
    horas_padrao = config_service.get_config(session, "expediente_horas_padrao", "8")
    tolerancia = config_service.get_config(session, "expediente_tolerancia_minutos", "10")
    
    return templates.TemplateResponse(
        "pages/configuracoes.html",
        {
            "request": request,
            "active_page": "configuracoes",
            "horas_padrao": horas_padrao,
            "tolerancia": tolerancia
        }
    )

@router.post("/htmx/configuracoes/expediente")
async def save_expediente_config(
    request: Request,
    horas_padrao: str = Form(...),
    tolerancia: str = Form(...),
    session: Session = Depends(get_session)
):
    config_service.set_config(session, "expediente_horas_padrao", horas_padrao)
    config_service.set_config(session, "expediente_tolerancia_minutos", tolerancia)
    
    return HTMLResponse(content='<div class="expediente-saved-msg visible">Configurações salvas ✓</div>')
