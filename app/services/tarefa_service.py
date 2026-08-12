from sqlmodel import Session, select, col
from fastapi import HTTPException
from app.models import Tarefa, TarefaStatus
from app.schemas import TarefaCreate, TarefaUpdate
from datetime import datetime, timedelta
from typing import Optional, Dict, List

def create_tarefa(session: Session, tarefa_in: TarefaCreate) -> Tarefa:
    db_tarefa = Tarefa.model_validate(tarefa_in)
    if db_tarefa.status == TarefaStatus.CONCLUIDO and not db_tarefa.data_conclusao:
        db_tarefa.data_conclusao = datetime.utcnow()
    session.add(db_tarefa)
    session.commit()
    session.refresh(db_tarefa)
    return db_tarefa

def get_tarefa(session: Session, tarefa_id: int) -> Tarefa:
    tarefa = session.get(Tarefa, tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return tarefa

def get_board_tarefas(session: Session) -> Dict[str, List[Tarefa]]:
    """
    Retorna as tarefas organizadas para a visão Kanban:
    - a_fazer
    - em_andamento
    - concluido_recentes (concluídos nos últimos 7 dias)
    - concluido_anteriores (concluídos há mais de 7 dias)
    """
    statement = select(Tarefa).order_by(Tarefa.updated_at.desc())
    all_tarefas = session.exec(statement).all()
    
    agora = datetime.utcnow()
    limite_7dias = agora - timedelta(days=7)

    board = {
        "a_fazer": [],
        "em_andamento": [],
        "concluido_recentes": [],
        "concluido_anteriores": []
    }

    for t in all_tarefas:
        if t.status == TarefaStatus.A_FAZER:
            board["a_fazer"].append(t)
        elif t.status == TarefaStatus.EM_ANDAMENTO:
            board["em_andamento"].append(t)
        elif t.status == TarefaStatus.CONCLUIDO:
            dt_ref = t.data_conclusao or t.updated_at
            if dt_ref >= limite_7dias:
                board["concluido_recentes"].append(t)
            else:
                board["concluido_anteriores"].append(t)

    return board

def update_tarefa(session: Session, tarefa_id: int, tarefa_in: TarefaUpdate) -> Tarefa:
    db_tarefa = get_tarefa(session, tarefa_id)
    old_status = db_tarefa.status

    tarefa_data = tarefa_in.model_dump(exclude_unset=True)
    for key, value in tarefa_data.items():
        setattr(db_tarefa, key, value)

    # Se o status mudou para concluído, atualiza a data de conclusão
    if db_tarefa.status == TarefaStatus.CONCLUIDO and old_status != TarefaStatus.CONCLUIDO:
        db_tarefa.data_conclusao = datetime.utcnow()
    elif db_tarefa.status != TarefaStatus.CONCLUIDO:
        db_tarefa.data_conclusao = None

    db_tarefa.updated_at = datetime.utcnow()
    session.add(db_tarefa)
    session.commit()
    session.refresh(db_tarefa)
    return db_tarefa

def delete_tarefa(session: Session, tarefa_id: int):
    tarefa = get_tarefa(session, tarefa_id)
    session.delete(tarefa)
    session.commit()
    return {"ok": True}
