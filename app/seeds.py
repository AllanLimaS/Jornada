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
        
        # Seeds de Tarefas
        if not session.exec(select(models.Tarefa)).first():
            from datetime import date, datetime, timedelta
            hoje = date.today()
            agora = datetime.utcnow()
            
            tarefa_seeds = [
                models.Tarefa(
                    titulo="Revisar documentação do módulo de relatórios",
                    descricao="Revisar se todos os filtros e exportações CSV/PDF foram descritos adequadamente.",
                    status=models.TarefaStatus.A_FAZER,
                    prioridade=models.TarefaPrioridade.ALTA,
                    data_prazo=hoje
                ),
                models.Tarefa(
                    titulo="Atualizar dependências do projeto",
                    descricao="Atualizar pacotes do requirements.txt para garantir compatibilidade com Python 3.14.",
                    status=models.TarefaStatus.A_FAZER,
                    prioridade=models.TarefaPrioridade.MEDIA,
                    data_prazo=hoje + timedelta(days=1)
                ),
                models.Tarefa(
                    titulo="Corrigir bug no cálculo de horas extras",
                    descricao="Ajustar lógica no service do expediente que estava duplicando intervalo.",
                    status=models.TarefaStatus.EM_ANDAMENTO,
                    prioridade=models.TarefaPrioridade.URGENTE,
                    data_prazo=hoje
                ),
                models.Tarefa(
                    titulo="Implementar endpoint de exportação CSV",
                    descricao="Criar rota HTMX para baixar relatório em formato CSV.",
                    status=models.TarefaStatus.EM_ANDAMENTO,
                    prioridade=models.TarefaPrioridade.ALTA,
                    data_prazo=hoje + timedelta(days=1)
                ),
                models.Tarefa(
                    titulo="Deploy da versão 2.3.1",
                    descricao="Publicar versão de correção de instabilidade nos gráficos.",
                    status=models.TarefaStatus.CONCLUIDO,
                    prioridade=models.TarefaPrioridade.MEDIA,
                    data_prazo=hoje - timedelta(days=2),
                    data_conclusao=agora - timedelta(days=2)
                ),
                models.Tarefa(
                    titulo="Configuração inicial do servidor",
                    descricao="Setup de ambiente e banco SQLite.",
                    status=models.TarefaStatus.CONCLUIDO,
                    prioridade=models.TarefaPrioridade.ALTA,
                    data_prazo=hoje - timedelta(days=10),
                    data_conclusao=agora - timedelta(days=10)
                )
            ]
            session.add_all(tarefa_seeds)
            print("Tarefas padrão inseridas.")
        
        session.commit()

