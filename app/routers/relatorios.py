from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.database import get_session
from app.services import relatorio_service

router = APIRouter(prefix="/htmx/relatorios")
templates = Jinja2Templates(directory="app/templates")

@router.get("/total-hoje")
def htmx_total_hoje(request: Request, session: Session = Depends(get_session)):
    minutos = relatorio_service.get_total_minutos_hoje(session)
    total_formatado = relatorio_service.format_minutos_to_horas(minutos)
    return templates.TemplateResponse(
        "partials/relatorio_total.html",
        {"request": request, "total": total_formatado}
    )

@router.get("/total-semana")
def htmx_total_semana(request: Request, session: Session = Depends(get_session)):
    minutos = relatorio_service.get_total_minutos_semana(session)
    total_formatado = relatorio_service.format_minutos_to_horas(minutos)
    return templates.TemplateResponse(
        "partials/relatorio_total.html",
        {"request": request, "total": total_formatado}
    )

@router.get("/resumo-categorias")
def htmx_resumo_categorias(request: Request, session: Session = Depends(get_session)):
    resumo = relatorio_service.get_resumo_por_categoria(session)
    # Format minutes in the summary
    for item in resumo:
        item["total_formatado"] = relatorio_service.format_minutos_to_horas(item["total_minutos"])
        
    return templates.TemplateResponse(
        "partials/relatorio_categorias.html",
        {"request": request, "resumo": resumo}
    )
