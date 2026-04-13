# Jornada Backend

Uma aplicação local para gestão diária de registro de horas e chamados da "Jornada".
Construído com extrema simplicidade utilizando FastAPI, SQLModel e SQLite.

## Stack
- Python + FastAPI
- SQLModel + SQLite
- Jinja2 + HTMX (para o Front, com respostas via rotas de View)

## Como Rodar Localmente

1. **Crie e Ative um Ambiente Virtual (opcional mas recomendado):**
   ```bash
   python -m venv venv
   
   # No Windows:
   .\venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Suba o Servidor (Uvicorn):**
   ```bash
   uvicorn main:app --reload
   ```

## Acesso e Banco
- A aplicação principal responderá em: http://127.0.0.1:8000
- O banco de dados `database.db` será gerado automaticamente na raiz assim que rodar o comando pela primeira vez.
- Visualize as rotas automatizadas em: http://127.0.0.1:8000/docs
