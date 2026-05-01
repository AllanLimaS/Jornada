from __future__ import annotations
from enum import Enum
from datetime import date, time, datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, Any
from sqlalchemy.orm import relationship as sa_relationship

# --- Enums ---

class AtividadePortalStatus(str, Enum):
    PENDENTE = "pendente"
    LANCADO = "lancado"

# --- Models Base (Utilizados por Schemas e outros Modelos) ---

class ChamadoCategoriaBase(SQLModel):
    nome: str
    cor: Optional[str] = Field(default="#333333")

class ChamadoStatusBase(SQLModel):
    nome: str
    cor: Optional[str] = Field(default="#3B82F6")

class ChamadoBase(SQLModel):
    numero: str = Field(index=True)
    titulo: str
    descricao: Optional[str] = Field(default=None)
    categoria_id: Optional[int] = Field(default=None, foreign_key="chamado_categoria.id")
    status_id: Optional[int] = Field(default=None, foreign_key="chamado_status.id")

class AtividadeBase(SQLModel):
    data_referencia: date
    hora_inicio: Optional[time] = Field(default=None)
    hora_fim: Optional[time] = Field(default=None)
    duracao_minutos: int = Field(default=0)
    descricao: str
    portal_status: AtividadePortalStatus = Field(default=AtividadePortalStatus.PENDENTE)
    chamado_id: Optional[int] = Field(default=None, foreign_key="chamado.id")
    chamado_status_id: Optional[int] = Field(default=None, foreign_key="chamado_status.id")

# --- Modelos de Tabela (DB) ---

class ChamadoCategoria(ChamadoCategoriaBase, table=True):
    __tablename__ = "chamado_categoria"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relacionamentos via sa_relationship para máxima estabilidade no Python 3.14
    chamados: List["Chamado"] = Relationship(
        sa_relationship=sa_relationship("Chamado", back_populates="categoria")
    )

class ChamadoStatus(ChamadoStatusBase, table=True):
    __tablename__ = "chamado_status"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    chamados: List["Chamado"] = Relationship(
        sa_relationship=sa_relationship("Chamado", back_populates="status")
    )

class Chamado(ChamadoBase, table=True):
    __tablename__ = "chamado"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    categoria: Optional["ChamadoCategoria"] = Relationship(
        sa_relationship=sa_relationship("ChamadoCategoria", back_populates="chamados")
    )
    status: Optional["ChamadoStatus"] = Relationship(
        sa_relationship=sa_relationship("ChamadoStatus", back_populates="chamados")
    )
    atividades: List["Atividade"] = Relationship(
        sa_relationship=sa_relationship("Atividade", back_populates="chamado")
    )

class Atividade(AtividadeBase, table=True):
    __tablename__ = "atividade"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    chamado: Optional["Chamado"] = Relationship(
        sa_relationship=sa_relationship("Chamado", back_populates="atividades")
    )
    chamado_status: Optional["ChamadoStatus"] = Relationship(
        sa_relationship=sa_relationship("ChamadoStatus")
    )

class Expediente(SQLModel, table=True):
    __tablename__ = "expediente"
    data: date = Field(primary_key=True)
    entrada_1: Optional[time] = Field(default=None)
    saida_1: Optional[time] = Field(default=None)
    entrada_2: Optional[time] = Field(default=None)
    saida_2: Optional[time] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Sprint(SQLModel, table=True):
    __tablename__ = "sprint"
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    data_inicio: date
    data_fim: date
    conteudo_markdown: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Configuracao(SQLModel, table=True):
    __tablename__ = "configuracao"
    chave: str = Field(primary_key=True)
    valor: str
