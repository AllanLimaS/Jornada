from datetime import date, time, datetime, timedelta
from sqlmodel import Session, select
from app.models import Expediente
from app.schemas import ExpedienteUpdate
from app.services import config_service

def get_or_create_expediente(session: Session, data_ref: date) -> Expediente:
    expediente = session.get(Expediente, data_ref)
    if not expediente:
        expediente = Expediente(data=data_ref)
        session.add(expediente)
        session.commit()
        session.refresh(expediente)
    return expediente

def update_expediente(session: Session, data_ref: date, data: ExpedienteUpdate) -> Expediente:
    expediente = get_or_create_expediente(session, data_ref)
    
    if data.entrada_1 is not None: expediente.entrada_1 = data.entrada_1
    if data.saida_1 is not None: expediente.saida_1 = data.saida_1
    if data.entrada_2 is not None: expediente.entrada_2 = data.entrada_2
    if data.saida_2 is not None: expediente.saida_2 = data.saida_2
    
    expediente.updated_at = datetime.utcnow()
    session.add(expediente)
    session.commit()
    session.refresh(expediente)
    return expediente

def calculate_stats(session: Session, exp: Expediente):
    """Retorna projeção de saída e tempos trabalhados."""
    def to_minutes(t: time):
        return t.hour * 60 + t.minute if t else 0

    def from_minutes(m: int):
        if m < 0: return "00:00"
        hours = m // 60
        mins = m % 60
        return f"{hours:02d}:{mins:02d}"

    # Busca configurações
    horas_padrao = int(config_service.get_config(session, "expediente_horas_padrao", "8"))
    tolerancia_minutos = int(config_service.get_config(session, "expediente_tolerancia_minutos", "10"))
    
    meta_minutos = horas_padrao * 60

    res = {
        "worked_morning": 0,
        "remaining_minutes": meta_minutos,
        "target_exit_minutes": None,
        "window_start": None,
        "window_end": None,
        "is_complete_morning": False,
        "meta_str": f"{horas_padrao:02d}:00h"
    }

    if exp.entrada_1 and exp.saida_1:
        e1 = to_minutes(exp.entrada_1)
        s1 = to_minutes(exp.saida_1)
        res["worked_morning"] = max(0, s1 - e1)
        res["is_complete_morning"] = True
        res["remaining_minutes"] = max(0, meta_minutos - res["worked_morning"])

    if res["is_complete_morning"] and exp.entrada_2:
        e2 = to_minutes(exp.entrada_2)
        target = e2 + res["remaining_minutes"]
        res["target_exit_minutes"] = target
        res["window_start"] = from_minutes(target - tolerancia_minutos)
        res["window_end"] = from_minutes(target + tolerancia_minutos)
        res["target_exit_str"] = from_minutes(target)
    
    return res
