from sqlmodel import Session, select, func, and_
from datetime import date, timedelta, datetime
from app.models import Atividade, Chamado, ChamadoCategoria
from typing import List, Dict, Any

def get_total_minutos_hoje(session: Session) -> int:
    hoje = date.today()
    statement = select(func.sum(Atividade.duracao_minutos)).where(Atividade.data_referencia == hoje)
    result = session.exec(statement).one()
    return result if result else 0

def get_total_minutos_semana(session: Session) -> int:
    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    
    statement = select(func.sum(Atividade.duracao_minutos)).where(
        and_(
            Atividade.data_referencia >= inicio_semana,
            Atividade.data_referencia <= fim_semana
        )
    )
    result = session.exec(statement).one()
    return result if result else 0

def get_resumo_por_categoria(session: Session) -> List[Dict[str, Any]]:
    # Join Atividade -> Chamado -> ChamadoCategoria
    statement = (
        select(
            ChamadoCategoria.nome,
            ChamadoCategoria.cor,
            func.sum(Atividade.duracao_minutos).label("total_minutos")
        )
        .join(Chamado, Atividade.chamado_id == Chamado.id)
        .join(ChamadoCategoria, Chamado.categoria_id == ChamadoCategoria.id)
        .group_by(ChamadoCategoria.id)
    )
    results = session.exec(statement).all()
    
    resumo = []
    for nome, cor, total in results:
        resumo.append({
            "categoria": nome,
            "cor": cor,
            "total_minutos": total
        })
        
    # Atividades sem chamado ou chamados sem categoria
    # (Simplificando para apenas o que tem categoria por enquanto, 
    # ou podemos adicionar um "Outros")
    
    return resumo

def format_minutos_to_horas(minutos: int) -> str:
    horas = minutos // 60
    restante = minutos % 60
    return f"{horas}h {restante}m"
