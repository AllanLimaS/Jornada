from __future__ import annotations
from enum import Enum

from datetime import date, time, datetime
from sqlmodel import SQLModel, Field

# --- Enums ---

class AtividadePortalStatus(str, Enum):
    PENDENTE = "pendente"
    LANCADO = "lancado"

# (Removido Enum ChamadoStatus anterior para usar tabela dinâmica)

# --- Models Base (Tabelas do BD) ---

class ChamadoCategoriaBase(SQLModel):
    nome: str
    cor: str | None = Field(default="#333333")

class ChamadoCategoria(ChamadoCategoriaBase, table=True):
    __tablename__ = "chamado_categoria"
    id: int | None = Field(default=None, primary_key=True)

class ChamadoStatusBase(SQLModel):
    nome: str
    cor: str | None = Field(default="#3B82F6")

class ChamadoStatus(ChamadoStatusBase, table=True):
    __tablename__ = "chamado_status"
    id: int | None = Field(default=None, primary_key=True)

class ChamadoBase(SQLModel):
    numero: str = Field(index=True)
    titulo: str
    descricao: str | None = Field(default=None)
    categoria_id: int | None = Field(default=None, foreign_key="chamado_categoria.id")
    status_id: int | None = Field(default=None, foreign_key="chamado_status.id")

class Chamado(ChamadoBase, table=True):
    __tablename__ = "chamado"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AtividadeBase(SQLModel):
    data_referencia: date
    hora_inicio: time
    hora_fim: time
    duracao_minutos: int = Field(default=0)  # Deve ser calculada no Service
    descricao: str
    portal_status: AtividadePortalStatus = Field(default=AtividadePortalStatus.PENDENTE)
    chamado_id: int | None = Field(default=None, foreign_key="chamado.id")

class Atividade(AtividadeBase, table=True):
    __tablename__ = "atividade"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
