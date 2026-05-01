from __future__ import annotations
from pydantic import BaseModel, Field

from datetime import date, time, datetime
from typing import Optional
from app.models import (
    ChamadoBase, AtividadeBase, ChamadoCategoriaBase, 
    ChamadoStatusBase, AtividadePortalStatus
)

# --- Status de Chamado ---
class ChamadoStatusCreate(ChamadoStatusBase):
    pass

class ChamadoStatusRead(ChamadoStatusBase):
    id: int

class ChamadoStatusUpdate(BaseModel):
    nome: str | None = Field(default=None)
    cor: str | None = Field(default=None)

# --- Categorias de Chamado ---
class ChamadoCategoriaCreate(ChamadoCategoriaBase):
    pass

class ChamadoCategoriaRead(ChamadoCategoriaBase):
    id: int

class ChamadoCategoriaUpdate(BaseModel):
    nome: str | None = Field(default=None)
    cor: str | None = Field(default=None)

# --- Chamados ---
class ChamadoCreate(ChamadoBase):
    pass

class ChamadoRead(ChamadoBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ChamadoUpdate(BaseModel):
    numero: str | None = Field(default=None)
    titulo: str | None = Field(default=None)
    descricao: str | None = Field(default=None)
    categoria_id: int | None = Field(default=None)
    status_id: int | None = Field(default=None)

# --- Atividades ---
class AtividadeCreate(AtividadeBase):
    pass

class AtividadeRead(AtividadeBase):
    id: int
    created_at: datetime
    updated_at: datetime

class AtividadeUpdate(BaseModel):
    data_referencia: date | None = Field(default=None)
    hora_inicio: time | None = Field(default=None)
    hora_fim: time | None = Field(default=None)
    descricao: str | None = Field(default=None)
    portal_status: AtividadePortalStatus | None = Field(default=None)
    chamado_id: int | None = Field(default=None)
    chamado_status_id: int | None = Field(default=None)

# --- Expediente ---
class ExpedienteCreate(BaseModel):
    data: date
    entrada_1: time | None = None
    saida_1: time | None = None
    entrada_2: time | None = None
    saida_2: time | None = None

class ExpedienteRead(ExpedienteCreate):
    created_at: datetime
    updated_at: datetime

class ExpedienteUpdate(BaseModel):
    entrada_1: time | None = None
    saida_1: time | None = None
    entrada_2: time | None = None
    saida_2: time | None = None

# --- Sprints ---
class SprintCreate(BaseModel):
    nome: str
    data_inicio: date
    data_fim: date
    conteudo_markdown: str = ""

class SprintRead(BaseModel):
    id: int
    nome: str
    data_inicio: date
    data_fim: date
    conteudo_markdown: str
    created_at: datetime
    updated_at: datetime

class SprintUpdate(BaseModel):
    nome: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    conteudo_markdown: str | None = None
