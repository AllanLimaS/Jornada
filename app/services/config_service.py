from sqlmodel import Session, select
from app.models import Configuracao

def get_config(session: Session, chave: str, default=None) -> str | None:
    config = session.get(Configuracao, chave)
    return config.valor if config else default

def set_config(session: Session, chave: str, valor: str) -> Configuracao:
    config = session.get(Configuracao, chave)
    if config:
        config.valor = valor
    else:
        config = Configuracao(chave=chave, valor=valor)
    
    session.add(config)
    session.commit()
    session.refresh(config)
    return config
