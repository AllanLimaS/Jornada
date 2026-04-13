from sqlmodel import Session, select
from app import models, schemas
from typing import List

def get_categorias(session: Session, skip: int = 0, limit: int = 100) -> List[models.ChamadoCategoria]:
    statement = select(models.ChamadoCategoria).offset(skip).limit(limit)
    return session.exec(statement).all()

def create_categoria(session: Session, categoria_in: schemas.ChamadoCategoriaCreate) -> models.ChamadoCategoria:
    db_categoria = models.ChamadoCategoria.model_validate(categoria_in)
    session.add(db_categoria)
    session.commit()
    session.refresh(db_categoria)
    return db_categoria

def delete_categoria(session: Session, categoria_id: int):
    categoria = session.get(models.ChamadoCategoria, categoria_id)
    if categoria:
        session.delete(categoria)
        session.commit()
