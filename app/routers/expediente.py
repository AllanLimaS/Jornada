from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from datetime import date as date_type, time
from typing import Optional

from app.database import get_session
from app import schemas, models
from app.services import expediente_service

router = APIRouter(prefix="/htmx/expediente", tags=["expediente"])
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def htmx_get_expediente(
    request: Request, 
    data_ref: Optional[date_type] = None, 
    session: Session = Depends(get_session)
):
    if not data_ref:
        data_ref = date_type.today()
    
    exp = expediente_service.get_or_create_expediente(session, data_ref)
    stats = expediente_service.calculate_stats(session, exp)
    return templates.TemplateResponse(
        "partials/expediente_card.html",
        {"request": request, "exp": exp, "stats": stats}
    )

@router.post("/update")
def htmx_update_expediente(
    request: Request,
    data_ref: date_type = Form(...),
    entrada_1: Optional[str] = Form(None),
    saida_1: Optional[str] = Form(None),
    entrada_2: Optional[str] = Form(None),
    saida_2: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    def parse_time(t_str):
        if not t_str: return None
        try:
            return time.fromisoformat(t_str)
        except:
            return None

    data_update = schemas.ExpedienteUpdate(
        entrada_1=parse_time(entrada_1),
        saida_1=parse_time(saida_1),
        entrada_2=parse_time(entrada_2),
        saida_2=parse_time(saida_2)
    )
    
    exp = expediente_service.update_expediente(session, data_ref, data_update)
    stats = expediente_service.calculate_stats(session, exp)
    
    response = templates.TemplateResponse(
        "partials/expediente_card.html",
        {"request": request, "exp": exp, "stats": stats, "is_update": True}
    )
    response.headers["HX-Trigger"] = "showExpedienteFeedback"
    return response
