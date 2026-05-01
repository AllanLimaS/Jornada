from sqlmodel import SQLModel, create_engine, Session

sqlite_file_name = "jornada.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False é necessário para SQLite e FastAPI
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

from sqlmodel import text

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
    # Migração automática simples
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT chamado_status_id FROM atividade LIMIT 1"))
        except Exception:
            try:
                conn.execute(text("ALTER TABLE atividade ADD COLUMN chamado_status_id INTEGER REFERENCES chamado_status(id)"))
                conn.commit()
            except Exception as e:
                print(f"Erro ao adicionar coluna chamado_status_id: {e}")

def get_session():
    with Session(engine) as session:
        yield session
