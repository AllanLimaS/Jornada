import unittest
from datetime import date, time
from sqlmodel import SQLModel, create_engine, Session
from fastapi import Request

from app.models import Atividade, AtividadePortalStatus
from app.services import atividade_service
from app.routers.atividades import _render_timeline, api_resumo_calendario

# In-memory SQLite database
sqlite_url = "sqlite:///:memory:"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

class TestNewFeatures(unittest.TestCase):
    def setUp(self):
        SQLModel.metadata.create_all(engine)
        self.session = Session(engine)

    def tearDown(self):
        self.session.close()
        SQLModel.metadata.drop_all(engine)

    def test_duration_in_timeline_html(self):
        # Activity 1: 30 min duration
        atv1 = Atividade(
            data_referencia=date(2026, 8, 5),
            hora_inicio=time(8, 0),
            hora_fim=time(8, 30),
            duracao_minutos=30,
            descricao="Atividade de teste 30m",
            portal_status=AtividadePortalStatus.PENDENTE
        )
        # Activity 2: 1h 30m duration
        atv2 = Atividade(
            data_referencia=date(2026, 8, 5),
            hora_inicio=time(9, 0),
            hora_fim=time(10, 30),
            duracao_minutos=90,
            descricao="Atividade de teste 90m",
            portal_status=AtividadePortalStatus.LANCADO
        )
        self.session.add(atv1)
        self.session.add(atv2)
        self.session.commit()

        # Dummy request for Jinja rendering
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
        response = _render_timeline(request, self.session, date(2026, 8, 5))
        
        content = response.body.decode('utf-8')
        
        self.assertIn("08:00 - 08:30", content)
        self.assertIn("(30 min)", content)
        self.assertIn("09:00 - 10:30", content)
        self.assertIn("(1h 30m)", content)

    def test_calendar_summary_service_and_api(self):
        d1 = date(2026, 8, 5)
        atv1 = Atividade(
            data_referencia=d1,
            hora_inicio=time(8, 0),
            hora_fim=time(8, 30),
            duracao_minutos=30,
            descricao="Atividade 1",
            portal_status=AtividadePortalStatus.PENDENTE
        )
        atv2 = Atividade(
            data_referencia=d1,
            hora_inicio=time(10, 0),
            hora_fim=time(12, 0),
            duracao_minutos=120,
            descricao="Atividade 2",
            portal_status=AtividadePortalStatus.PENDENTE
        )
        atv3 = Atividade(
            data_referencia=d1,
            hora_inicio=time(13, 0),
            hora_fim=time(14, 0),
            duracao_minutos=60,
            descricao="Atividade 3",
            portal_status=AtividadePortalStatus.LANCADO
        )
        self.session.add(atv1)
        self.session.add(atv2)
        self.session.add(atv3)
        self.session.commit()

        # Service level test
        resumo = atividade_service.get_resumo_atividades_por_periodo(self.session, date(2026, 8, 1), date(2026, 8, 31))
        self.assertIn("2026-08-05", resumo)
        self.assertEqual(resumo["2026-08-05"]["minutos"], 210) # 30 + 120 + 60 = 210 min
        self.assertEqual(resumo["2026-08-05"]["total_atividades"], 3)
        self.assertEqual(resumo["2026-08-05"]["nao_lancadas"], 2)

        # API endpoint function test
        data = api_resumo_calendario(year=2026, month=8, session=self.session)
        self.assertIn("2026-08-05", data)
        self.assertEqual(data["2026-08-05"]["minutos"], 210)
        self.assertEqual(data["2026-08-05"]["total_atividades"], 3)
        self.assertEqual(data["2026-08-05"]["nao_lancadas"], 2)

if __name__ == "__main__":
    unittest.main()
