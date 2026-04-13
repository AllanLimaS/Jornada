# Jornada - Contexto do Projeto

Este arquivo serve como guia de contexto para assistentes de IA (como o Gemini) entenderem a estrutura, tecnologias e convenções deste projeto.

## Visão Geral do Projeto
A **Jornada** é uma aplicação local projetada para a gestão diária de registros de horas (atividades) e acompanhamento de chamados. O objetivo principal é simplificar o log de tempo gasto em tarefas específicas e vinculá-las a chamados ou categorias de trabalho.

### Tecnologias Principais
- **Backend:** Python 3.10+ com **FastAPI**.
- **Banco de Dados:** **SQLite** gerenciado via **SQLModel** (que une SQLAlchemy e Pydantic).
- **Frontend:** **Jinja2** para templates, **HTMX** para interatividade assíncrona e **Vanilla CSS** para estilização.
- **Ambiente:** Gerenciado por `.venv` e dependências em `requirements.txt`.

## Estrutura de Diretórios
- `main.py`: Ponto de entrada da aplicação FastAPI, configuração de rotas e ciclo de vida (lifespan).
- `app/`: Diretório principal do código-fonte.
    - `models.py`: Definições das tabelas do banco de dados (SQLModel).
    - `schemas.py`: Esquemas Pydantic para validação de entrada/saída (API).
    - `database.py`: Configuração da engine SQLite e gerenciamento de sessões.
    - `routers/`: Módulos de rotas (Atividades, Chamados, Categorias, Páginas).
    - `services/`: Camada de lógica de negócio (cálculos, operações complexas de DB).
    - `static/`: Arquivos estáticos (CSS, JS).
    - `templates/`: Templates HTML organizados em `pages/` (páginas completas) e `partials/` (fragmentos HTMX).

## Fluxo de Desenvolvimento e Convenções

### Camada de Serviço (Services)
Toda a lógica que não seja puramente transporte de dados (como cálculos de duração, filtros complexos ou validações de negócio) deve residir em `app/services/`. Os routers devem apenas chamar os serviços.

### Interatividade com HTMX
O projeto evita frameworks JavaScript pesados. A interatividade (como atualizar listas, abrir modais ou deletar itens sem recarregar a página) é feita via **HTMX**. 
- Rotas HTMX geralmente retornam fragmentos HTML localizados em `app/templates/partials/`.
- Verifique `app/routers/atividades.py` para exemplos de como as rotas HTMX coexistem com rotas de API REST.

### Banco de Dados
- O arquivo de banco de dados padrão é `jornada.db`.
- A criação das tabelas ocorre automaticamente na inicialização da aplicação (`lifespan` em `main.py`).
- Use `SQLModel` para definir novos modelos e garantir que eles sejam importados em `main.py` antes da criação das tabelas.

## Comandos Úteis

### Rodar o Projeto (Windows)
```bash
run.bat
```
*(O script automatiza a criação do venv, instalação de dependências e sobe o servidor)*

### Rodar o Projeto (Manual)
1. **Ativar Venv:** `.\.venv\Scripts\activate` (Windows) ou `source .venv/bin/activate` (Linux/Mac)
2. **Instalar:** `pip install -r requirements.txt`
3. **Servidor:** `uvicorn main:app --reload`

### Documentação da API
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **Redoc:** `http://127.0.0.1:8000/redoc`

## Regras de Ouro para a IA
1. **Mantenha a Simplicidade:** O projeto preza por ser leve e local.
2. **HTMX Primeiro:** Se precisar adicionar interatividade no front, prefira HTMX retornando um partial em vez de escrever JavaScript personalizado.
3. **Validação:** Sempre utilize os schemas em `app/schemas.py` para dados vindos do cliente.
4. **Surgical Edits:** Ao modificar modelos, lembre-se de atualizar os schemas correspondentes.
