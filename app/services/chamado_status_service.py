from sqlmodel import Session, select
from app import models, schemas
from typing import List

def get_statuses(session: Session, skip: int = 0, limit: int = 100) -> List[models.ChamadoStatus]:
    statement = select(models.ChamadoStatus).offset(skip).limit(limit)
    return session.exec(statement).all()

def create_status(session: Session, status_in: schemas.ChamadoStatusCreate) -> models.ChamadoStatus:
    db_status = models.ChamadoStatus.model_validate(status_in)
    session.add(db_status)
    session.commit()
    session.refresh(db_status)
    return db_status

def delete_status(session: Session, status_id: int):
    status = session.get(models.ChamadoStatus, status_id)
    if status:
        session.delete(status)
        session.commit()
