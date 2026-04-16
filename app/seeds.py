from sqlmodel import Session, select
from app.database import engine
from app import models

def init_seeds():
    """Insere dados iniciais se as tabelas estiverem vazias."""
    with Session(engine) as session:
        # Seeds de Status
        if not session.exec(select(models.ChamadoStatus)).first():
            status_seeds = [
                models.ChamadoStatus(nome="Em Atendimento", cor="#3B82F6"),
                models.ChamadoStatus(nome="Encerrado", cor="#10B981")
            ]
            session.add_all(status_seeds)
            print("Status padrão inseridos.")
        
        # Seeds de Categorias
        if not session.exec(select(models.ChamadoCategoria)).first():
            cat_seeds = [
                models.ChamadoCategoria(nome="Melhoria", cor="#8B5CF6"),
                models.ChamadoCategoria(nome="Projeto", cor="#F59E0B")
            ]
            session.add_all(cat_seeds)
            print("Categorias padrão inseridas.")
        
        # Seeds de Configurações
        if not session.exec(select(models.Configuracao)).first():
            config_seeds = [
                models.Configuracao(chave="expediente_horas_padrao", valor="8"),
                models.Configuracao(chave="expediente_tolerancia_minutos", valor="10"),
            ]
            session.add_all(config_seeds)
            print("Configurações padrão inseridas.")
        
        session.commit()
