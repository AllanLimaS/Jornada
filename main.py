from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from app.database import create_db_and_tables, engine
# Importante importar os modelos aqui para que o create_all do metadata saiba sobre eles
from app import models
from app.routers import atividades, chamados, chamado_categorias, chamado_status, pages, expediente, sprint

def init_seeds():
    """Insere dados iniciais se as tabelas estiverem vazias."""
    with Session(engine) as session:
        # Seeds de Status
        if not session.exec(select(models.ChamadoStatus)).first():
            status_seeds = [
                models.ChamadoStatus(nome="Em Atendimento", cor="#3B82F6"),
                models.ChamadoStatus(nome="Encerrado", cor="#10B981")
            ]
            session.add_all(status_seeds)
            print("Status padrão inseridos.")
        
        # Seeds de Categorias
        if not session.exec(select(models.ChamadoCategoria)).first():
            cat_seeds = [
                models.ChamadoCategoria(nome="Melhoria", cor="#8B5CF6"),
                models.ChamadoCategoria(nome="Projeto", cor="#F59E0B")
            ]
            session.add_all(cat_seeds)
            print("Categorias padrão inseridas.")
        
        session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    init_seeds()
    yield

app = FastAPI(
    title="Jornada API",
    description="Aplicativo simples para gestão de chamados e horas diárias trabalhadas",
    version="0.1.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(atividades.router)
app.include_router(chamados.router)
app.include_router(chamado_categorias.router)
app.include_router(chamado_status.router)
app.include_router(expediente.router)
app.include_router(sprint.router)
app.include_router(pages.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
