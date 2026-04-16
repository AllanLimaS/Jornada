from sqlmodel import Session, select, or_, col, func
from fastapi import HTTPException
from app.models import Chamado, Atividade
from app.schemas import ChamadoCreate, ChamadoUpdate
from datetime import datetime, date
from typing import Optional, Dict

def create_chamado(session: Session, chamado_in: ChamadoCreate) -> Chamado:
    db_chamado = Chamado.model_validate(chamado_in)
    session.add(db_chamado)
    session.commit()
    session.refresh(db_chamado)
    return db_chamado

def get_chamados(session: Session, skip: int = 0, limit: int = 100):
    statement = select(Chamado).offset(skip).limit(limit)
    return session.exec(statement).all()

def get_chamado(session: Session, chamado_id: int) -> Chamado:
    chamado = session.get(Chamado, chamado_id)
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return chamado

def update_chamado(session: Session, chamado_id: int, chamado_in: ChamadoUpdate) -> Chamado:
    db_chamado = get_chamado(session, chamado_id)
    chamado_data = chamado_in.model_dump(exclude_unset=True)
    for key, value in chamado_data.items():
        setattr(db_chamado, key, value)
    db_chamado.updated_at = datetime.utcnow()
    session.add(db_chamado)
    session.commit()
    session.refresh(db_chamado)
    return db_chamado

def delete_chamado(session: Session, chamado_id: int):
    chamado = get_chamado(session, chamado_id)
    session.delete(chamado)
    session.commit()
    return {"ok": True}

def search_chamados(session: Session, 
                   query: Optional[str] = None, 
                   categoria_id: Optional[int] = None, 
                   status_id: Optional[int] = None,
                   limit: int = 100):
    """Busca chamados por número ou título, filtrando por categoria e status."""
    statement = select(Chamado)
    
    conditions = []
    if query and query.strip():
        conditions.append(or_(Chamado.numero.contains(query.strip()), Chamado.titulo.contains(query.strip())))
    
    if categoria_id:
        conditions.append(col(Chamado.categoria_id) == categoria_id)
    
    if status_id:
        conditions.append(col(Chamado.status_id) == status_id)
    
    if conditions:
        statement = statement.where(*conditions)
        
    statement = statement.order_by(Chamado.updated_at.desc()).limit(limit)
    return session.exec(statement).all()

def get_chamados_recentes(session: Session, limit: int = 10):
    """Retorna os chamados que têm atividades vinculadas, ordenados pela atividade mais recente."""
    # Subquery: IDs de chamados que possuem pelo menos 1 atividade, ordenados pela atividade mais recente
    statement = (
        select(Chamado)
        .where(
            col(Chamado.id).in_(
                select(Atividade.chamado_id)
                .where(Atividade.chamado_id.is_not(None))
                .distinct()
            )
        )
        .order_by(Chamado.updated_at.desc())
        .limit(limit)
    )
    return session.exec(statement).all()

def get_chamados_map(session: Session, chamado_ids: list) -> Dict[int, Chamado]:
    """Retorna um dicionário {id: Chamado} para uma lista de IDs."""
    if not chamado_ids:
        return {}
    statement = select(Chamado).where(col(Chamado.id).in_(chamado_ids))
    chamados = session.exec(statement).all()
    return {ch.id: ch for ch in chamados}

def get_ultima_atividade_map(session: Session) -> Dict[int, str]:
    """Retorna dict {chamado_id: data_referencia} com a data mais recente de atividade para cada chamado."""
    statement = (
        select(Atividade.chamado_id, func.max(Atividade.data_referencia).label("ultima_data"))
        .where(Atividade.chamado_id.is_not(None))
        .group_by(Atividade.chamado_id)
    )
    results = session.exec(statement).all()
    return {row[0]: row[1] for row in results}

def get_chamados_with_ultima_atv(
    session: Session, 
    query: Optional[str] = None, 
    categoria_id: Optional[int] = None,
    status_id: Optional[int] = None,
    limit: int = 100
):
    """Retorna lista de chamados com data da última atividade, aplicando filtros e ordenação."""
    ultimo_map = get_ultima_atividade_map(session)
    
    chamados = search_chamados(
        session, 
        query=query, 
        categoria_id=categoria_id, 
        status_id=status_id, 
        limit=limit
    )
    
    # Adiciona atributo extra e ordena por última atividade (desc), chamados sem atividade ficam por último
    result = []
    for ch in chamados:
        ch._ultima_atv = ultimo_map.get(ch.id)
        result.append(ch)
    
    result.sort(key=lambda c: (c._ultima_atv is not None, c._ultima_atv or date.min), reverse=True)
    return result
