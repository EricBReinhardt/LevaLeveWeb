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

API em Python com FastAPI. O frontend e a API rodam juntos no Vercel no mesmo repositório.

### Estrutura

- `backend/app/main.py`: API principal
- `backend/app/models.py`: modelos do banco
- `backend/app/schemas.py`: schemas de entrada e saida
- `backend/app/seed.py`: contas e dados de teste
- `backend/requirements.txt`: dependencias Python

### Como executar

1. Crie o banco PostgreSQL ou use o Vercel Postgres e defina `DATABASE_URL`.
2. Instale as dependencias com `pip install -r backend/requirements.txt`.
3. Rode a API com `uvicorn app.main:app --reload` dentro da pasta `backend/`.

## Deploy no Vercel

1. A raiz do projeto no Vercel deve apontar para este repositório inteiro.
2. O projeto usa a API Python em `api/index.py`, que carrega o app principal.
3. Defina `DATABASE_URL` nas variaveis de ambiente do projeto.
4. O frontend e os assets sao servidos pelo proprio FastAPI a partir da pasta `frontend/`.

## Contas de teste

- Cliente: `cliente.teste@levaleve.com` / `Cliente123!`
- Motorista: `motorista.teste@levaleve.com` / `Motorista123!`

## Repositorio

https://github.com/EricBReinhardt/Leva-Leve---Web-app-de-mudancas
