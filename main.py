from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from app.database import create_db_and_tables, engine
# Importante importar os modelos aqui para que o create_all do metadata saiba sobre eles
from app import models
from app.seeds import init_seeds
from app.routers import atividades, chamados, chamado_categorias, chamado_status, pages, expediente, sprint, configuracoes

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
app.include_router(configuracoes.router)
app.include_router(pages.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
