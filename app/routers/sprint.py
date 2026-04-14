from fastapi import APIRouter, Request, Depends, Query, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session
from app.database import get_session
from app.services import sprint_service
from app.schemas import SprintCreate, SprintUpdate
from datetime import date
import markdown

router = APIRouter(prefix="/htmx/sprint")
templates = Jinja2Templates(directory="app/templates")

@router.get("/list")
def htmx_sprint_list(request: Request, session: Session = Depends(get_session)):
    sprints = sprint_service.get_sprints(session)
    return templates.TemplateResponse(
        "partials/sprint_list.html",
        {"request": request, "sprints": sprints}
    )

@router.get("/new")
def htmx_sprint_new(request: Request):
    return templates.TemplateResponse(
        "partials/sprint_create_modal.html",
        {"request": request, "hoje_date": date.today().strftime("%Y-%m-%d")}
    )

@router.post("/generate")
def htmx_sprint_generate(
    request: Request,
    data_inicio: date = Form(...),
    data_fim: date = Form(...),
    incluir_horas: bool = Form(False),
    session: Session = Depends(get_session)
):
    nome = f"Sprint {data_inicio.strftime('%d/%m/%Y')}"
    conteudo = sprint_service.generate_markdown_template(session, data_inicio, data_fim, incluir_horas)
    
    return templates.TemplateResponse(
        "partials/sprint_editor.html",
        {
            "request": request,
            "nome": nome,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "conteudo_markdown": conteudo,
            "sprint_id": None
        }
    )

@router.post("/save")
def htmx_sprint_save(
    request: Request,
    nome: str = Form(...),
    data_inicio: date = Form(...),
    data_fim: date = Form(...),
    conteudo_markdown: str = Form(...),
    sprint_id: int | None = Form(None),
    session: Session = Depends(get_session)
):
    if sprint_id:
        db_sprint = sprint_service.get_sprint_by_id(session, sprint_id)
        if not db_sprint:
            raise HTTPException(status_code=404, detail="Sprint não encontrada")
        sprint_service.update_sprint(session, db_sprint, SprintUpdate(
            nome=nome, data_inicio=data_inicio, data_fim=data_fim, conteudo_markdown=conteudo_markdown
        ))
    else:
        sprint_service.create_sprint(session, SprintCreate(
            nome=nome, data_inicio=data_inicio, data_fim=data_fim, conteudo_markdown=conteudo_markdown
        ))
    
    # Após salvar, recarrega a página principal de listagem
    # Note: O usuário queria que após gerar abrisse a tela, e aqui após salvar voltamos para a lista.
    sprints = sprint_service.get_sprints(session)
    return templates.TemplateResponse(
        "partials/sprint_list.html",
        {"request": request, "sprints": sprints, "message": "Sprint salva com sucesso!"}
    )

@router.get("/edit/{sprint_id}")
def htmx_sprint_edit(request: Request, sprint_id: int, session: Session = Depends(get_session)):
    sprint = sprint_service.get_sprint_by_id(session, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint não encontrada")
    
    return templates.TemplateResponse(
        "partials/sprint_editor.html",
        {
            "request": request,
            "nome": sprint.nome,
            "data_inicio": sprint.data_inicio,
            "data_fim": sprint.data_fim,
            "conteudo_markdown": sprint.conteudo_markdown,
            "sprint_id": sprint.id
        }
    )

@router.delete("/delete/{sprint_id}")
def htmx_sprint_delete(request: Request, sprint_id: int, session: Session = Depends(get_session)):
    sprint = sprint_service.get_sprint_by_id(session, sprint_id)
    if sprint:
        sprint_service.delete_sprint(session, sprint)
    
    sprints = sprint_service.get_sprints(session)
    return templates.TemplateResponse(
        "partials/sprint_list.html",
        {"request": request, "sprints": sprints}
    )

@router.post("/preview", response_class=HTMLResponse)
def htmx_sprint_preview(request: Request, conteudo_markdown: str = Form("")):
    html_content = markdown.markdown(conteudo_markdown, extensions=['extra', 'codehilite'])
    return html_content
