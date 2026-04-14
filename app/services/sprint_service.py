from sqlmodel import Session, select, func, and_
from datetime import date, datetime
from app.models import Atividade, Chamado, ChamadoCategoria, Sprint
from app.schemas import SprintCreate, SprintUpdate
from typing import List, Dict, Any, Optional

def get_sprint_data(session: Session, data_inicio: date, data_fim: Optional[date] = None) -> List[Dict[str, Any]]:
    if not data_fim:
        data_fim = date.today()
        
    statement = (
        select(Atividade, Chamado, ChamadoCategoria)
        .join(Chamado, Atividade.chamado_id == Chamado.id)
        .join(ChamadoCategoria, Chamado.categoria_id == ChamadoCategoria.id)
        .where(
            and_(
                Atividade.data_referencia >= data_inicio,
                Atividade.data_referencia <= data_fim
            )
        )
        .order_by(ChamadoCategoria.nome, Chamado.titulo, Atividade.data_referencia.desc())
    )
    
    results = session.exec(statement).all()
    
    data = {}
    for atividade, chamado, categoria in results:
        if categoria.id not in data:
            data[categoria.id] = {
                "id": categoria.id,
                "nome": categoria.nome,
                "cor": categoria.cor,
                "total_minutos": 0,
                "chamados": {}
            }
        
        cat_group = data[categoria.id]
        if chamado.id not in cat_group["chamados"]:
            cat_group["chamados"][chamado.id] = {
                "id": chamado.id,
                "titulo": chamado.titulo,
                "numero": chamado.numero,
                "total_minutos": 0,
                "atividades": []
            }
        
        cham_group = cat_group["chamados"][chamado.id]
        cham_group["atividades"].append({
            "id": atividade.id,
            "descricao": atividade.descricao,
            "duracao_minutos": atividade.duracao_minutos,
            "duracao_formatada": format_minutos_to_horas(atividade.duracao_minutos),
            "data": atividade.data_referencia.strftime("%d/%m/%Y")
        })
        
        cham_group["total_minutos"] += atividade.duracao_minutos
        cat_group["total_minutos"] += atividade.duracao_minutos

    final_list = []
    for cat_id, cat in data.items():
        cat["total_formatado"] = format_minutos_to_horas(cat["total_minutos"])
        chamados_list = []
        for cham_id, cham in cat["chamados"].items():
            cham["total_formatado"] = format_minutos_to_horas(cham["total_minutos"])
            chamados_list.append(cham)
        cat["chamados"] = chamados_list
        final_list.append(cat)
        
    return final_list

def generate_markdown_template(session: Session, data_inicio: date, data_fim: date, incluir_horas: bool = False) -> str:
    dados = get_sprint_data(session, data_inicio, data_fim)
    
    md = f"# Relatório de Sprint ({data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')})\n\n"
    
    if not dados:
        md += "_Nenhuma atividade encontrada para este período._\n"
        return md

    for cat in dados:
        md += f"## {cat['nome']}\n"
        for cham in cat['chamados']:
            horas_chamado = f" ({cham['total_formatado']})" if incluir_horas else ""
            md += f"### {cham['numero']} - {cham['titulo']}{horas_chamado}\n"
            for act in cham['atividades']:
                horas_act = f" [{act['duracao_formatada']}]" if incluir_horas else ""
                md += f"- {act['descricao']}{horas_act}\n"
            md += "\n"
        md += "\n"
        
    return md

def format_minutos_to_horas(minutos: int) -> str:
    horas = minutos // 60
    restante = minutos % 60
    return f"{horas}h {restante:02d}m"

# CRUD Operations
def create_sprint(session: Session, sprint_data: SprintCreate) -> Sprint:
    db_sprint = Sprint.model_validate(sprint_data)
    session.add(db_sprint)
    session.commit()
    session.refresh(db_sprint)
    return db_sprint

def get_sprints(session: Session) -> List[Sprint]:
    return session.exec(select(Sprint).order_by(Sprint.data_inicio.desc())).all()

def get_sprint_by_id(session: Session, sprint_id: int) -> Optional[Sprint]:
    return session.get(Sprint, sprint_id)

def update_sprint(session: Session, db_sprint: Sprint, sprint_data: SprintUpdate) -> Sprint:
    data = sprint_data.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_sprint, key, value)
    db_sprint.updated_at = datetime.utcnow()
    session.add(db_sprint)
    session.commit()
    session.refresh(db_sprint)
    return db_sprint

def delete_sprint(session: Session, db_sprint: Sprint):
    session.delete(db_sprint)
    session.commit()
