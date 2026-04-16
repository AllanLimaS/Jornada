from sqlmodel import Session, select
from fastapi import HTTPException
from datetime import datetime, date
from app.models import Atividade
from app.schemas import AtividadeCreate, AtividadeUpdate

def calculate_duration(hora_inicio, hora_fim) -> int:
    if not hora_inicio or not hora_fim:
        return 0
    dt1 = datetime.combine(datetime.today(), hora_inicio)
    dt2 = datetime.combine(datetime.today(), hora_fim)
    if dt2 < dt1:
        raise ValueError("Hora fim não pode ser menor que hora início")
    delta = dt2 - dt1
    return int(delta.total_seconds() / 60)

def create_atividade(session: Session, atividade_in: AtividadeCreate) -> Atividade:
    try:
        duracao = calculate_duration(atividade_in.hora_inicio, atividade_in.hora_fim)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    db_atividade = Atividade.model_validate(atividade_in)
    db_atividade.duracao_minutos = duracao
    session.add(db_atividade)
    session.commit()
    session.refresh(db_atividade)
    return db_atividade

def get_atividades_by_date(session: Session, data_ref: date):
    statement = select(Atividade).where(Atividade.data_referencia == data_ref)
    return session.exec(statement).all()

def get_atividade(session: Session, atividade_id: int) -> Atividade:
    atividade = session.get(Atividade, atividade_id)
    if not atividade:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    return atividade

def update_atividade(session: Session, atividade_id: int, atividade_in: AtividadeUpdate) -> Atividade:
    db_atividade = get_atividade(session, atividade_id)
    atividade_data = atividade_in.model_dump(exclude_unset=True)
    
    for key, value in atividade_data.items():
        setattr(db_atividade, key, value)
        
    if "hora_inicio" in atividade_data or "hora_fim" in atividade_data:
        try:
            # Pega valores atuais do BD caso um deles não tenha sido enviado no PATCH
            h_ini = db_atividade.hora_inicio
            h_fim = db_atividade.hora_fim
            duracao = calculate_duration(h_ini, h_fim)
            db_atividade.duracao_minutos = duracao
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    db_atividade.updated_at = datetime.utcnow()
    session.add(db_atividade)
    session.commit()
    session.refresh(db_atividade)
    return db_atividade

def get_atividades_by_status(session: Session, aba: str = "todos"):
    """Retorna atividades filtradas por status do portal (para tela de Acompanhamentos)."""
    statement = select(Atividade)
    if aba == "pendentes":
        statement = statement.where(Atividade.portal_status == "pendente")
    elif aba == "lancados":
        statement = statement.where(Atividade.portal_status == "lancado")
    statement = statement.order_by(Atividade.hora_inicio.desc())
    return session.exec(statement).all()

def get_atividades_by_chamado(session: Session, chamado_id: int, limit: int = 10):
    """Retorna as últimas atividades vinculadas a um chamado específico."""
    statement = (
        select(Atividade)
        .where(Atividade.chamado_id == chamado_id)
        .order_by(Atividade.data_referencia.desc(), Atividade.hora_inicio.desc())
        .limit(limit)
    )
    return session.exec(statement).all()

def delete_atividade(session: Session, atividade_id: int):
    atividade = get_atividade(session, atividade_id)
    session.delete(atividade)
    session.commit()
    return {"ok": True}
