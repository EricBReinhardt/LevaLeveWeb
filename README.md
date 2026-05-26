# Leva Leve

Projeto separado em `frontend/` e `backend/`.

## Frontend

Interface em HTML + Tailwind CSS com as telas do fluxo de cliente e motorista.

### Estrutura

- `frontend/index.html`: landing page
- `frontend/pages/`: demais telas da jornada
- `frontend/assets/`: logo, favicons e scripts compartilhados

### Como executar

1. Abra `frontend/index.html` no navegador, ou use Live Server apontando para a pasta `frontend/`.

## Backend

API em Python com FastAPI e PostgreSQL.

### Estrutura

- `backend/app/main.py`: API principal
- `backend/app/models.py`: modelos do banco
- `backend/app/schemas.py`: schemas de entrada e saida
- `backend/app/seed.py`: contas e dados de teste
- `backend/requirements.txt`: dependencias Python

### Como executar

1. Crie o banco PostgreSQL e ajuste `backend/.env` a partir de `backend/.env.example`.
2. Instale as dependencias com `pip install -r backend/requirements.txt`.
3. Rode a API com `uvicorn app.main:app --reload` dentro da pasta `backend/`.

## Contas de teste

- Cliente: `cliente.teste@levaleve.com` / `Cliente123!`
- Motorista: `motorista.teste@levaleve.com` / `Motorista123!`

## Repositorio

https://github.com/EricBReinhardt/Leva-Leve---Web-app-de-mudancas
