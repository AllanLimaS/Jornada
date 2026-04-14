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

def update_categoria(session: Session, categoria_id: int, categoria_in: schemas.ChamadoCategoriaUpdate) -> models.ChamadoCategoria:
    db_categoria = session.get(models.ChamadoCategoria, categoria_id)
    if not db_categoria:
        return None
    
    categoria_data = categoria_in.model_dump(exclude_unset=True)
    for key, value in categoria_data.items():
        setattr(db_categoria, key, value)
    
    session.add(db_categoria)
    session.commit()
    session.refresh(db_categoria)
    return db_categoria
