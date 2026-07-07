# Leva Leve 🚗

Uma plataforma de transporte em tempo real que conecta clientes e motoristas. O projeto é composto por um frontend moderno em HTML/CSS/JavaScript e uma API robusta em Python com FastAPI.

## 📋 Sumário

- [Sobre o Projeto](#sobre-o-projeto)
- [Tecnologias](#tecnologias)
- [Requisitos](#requisitos)
- [Como Rodar Localmente](#como-rodar-localmente)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Contas de Teste](#contas-de-teste)
- [Deploy no Vercel](#deploy-no-vercel)

## 📖 Sobre o Projeto

**Leva Leve** é uma aplicação web que permite:

- **Clientes**: Solicitar transporte, rastrear motorista em tempo real, visualizar histórico de viagens
- **Motoristas**: Aceitar corridas, gerenciar ganhos, visualizar avaliações
- **Funcionalidades**: Autenticação, geolocalização, avaliações, histórico de transações

## 🛠️ Tecnologias

### Frontend
- **HTML5** - Estrutura
- **CSS3** (com Tailwind CSS) - Estilização
- **JavaScript (ES6+)** - Interatividade
- **API REST** - Comunicação com backend

### Backend
- **Python 3.10+**
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM para banco de dados
- **PostgreSQL** - Banco de dados
- **Pydantic** - Validação de dados
- **Gunicorn** - Servidor WSGI (produção)

## ✅ Requisitos

### Para rodar localmente:
- **Python 3.10+**
- **PostgreSQL 12+** (ou use Vercel Postgres)
- **pip** (gerenciador de pacotes Python)
- **Navegador moderno** (Chrome, Firefox, Safari, Edge)

### Opcional:
- **Live Server** (extensão VS Code) para desenvolvimento frontend
- **Git** para controle de versão

## 🚀 Como Rodar Localmente

### 1. Clone o Repositório

```bash
git clone <seu-repositorio>
cd "Leva Leve"
```

### 2. Configure o Banco de Dados

**Opção A: PostgreSQL Local**
```bash
# Crie um banco de dados
createdb leva_leve

# Defina a variável de ambiente (Windows PowerShell)
$env:DATABASE_URL = "postgresql://usuario:senha@localhost/leva_leve"

# Ou (Windows CMD)
set DATABASE_URL=postgresql://usuario:senha@localhost/leva_leve

# Ou (Linux/Mac)
export DATABASE_URL="postgresql://usuario:senha@localhost/leva_leve"
```

**Opção B: Vercel Postgres**
- Crie um banco em [vercel.com/storage/postgres](https://vercel.com/storage/postgres)
- Copie a `DATABASE_URL` fornecida e defina como variável de ambiente

### 3. Configure o Frontend (Opcional para Testes Locais)

Se quiser servir o frontend localmente:

```bash
# Opção 1: Use Live Server (VS Code)
# Abra frontend/index.html com a extensão Live Server

# Opção 2: Python HTTP Server
cd frontend
python -m http.server 5500
```

Acesse em: `http://localhost:5500`

### 4. Configure e Rode o Backend

```bash
# Navegue para a pasta backend
cd backend

# Crie um ambiente virtual (recomendado)
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Execute o seed (popula dados de teste)
python -m app.seed

# Inicie o servidor
uvicorn app.main:app --reload --port 8000
```

A API estará disponível em: `http://localhost:8000`

Documentação interativa (Swagger): `http://localhost:8000/docs`

## 📁 Estrutura do Projeto

```
Leva Leve/
├── frontend/                 # Interface do usuário
│   ├── index.html           # Landing page
│   ├── pages/               # Telas da jornada
│   │   ├── solicitar-transporte.html
│   │   ├── acompanhamento-corrida.html
│   │   ├── area-motorista.html
│   │   └── ... (demais páginas)
│   └── assets/              # Recursos estáticos
│       ├── css/             # Estilos
│       └── js/              # Scripts compartilhados
│           ├── api.js       # Chamadas à API
│           ├── auth-guard.js # Autenticação
│           ├── utils.js
│           └── header.js
│
├── backend/                  # API e lógica de negócio
│   ├── app/
│   │   ├── main.py          # Aplicação principal FastAPI
│   │   ├── models.py        # Modelos do banco (SQLAlchemy)
│   │   ├── schemas.py       # Schemas de validação (Pydantic)
│   │   ├── seed.py          # Dados de teste
│   │   ├── api/
│   │   │   └── routes/      # Endpoints da API
│   │   ├── core/
│   │   │   ├── config.py    # Configurações
│   │   │   └── security.py  # Autenticação/autorização
│   │   ├── db/
│   │   │   ├── base.py      # Configuração do banco
│   │   │   └── session.py   # Sessão do banco
│   │   ├── models/          # Modelos de domínio
│   │   ├── schemas/         # Schemas adicionais
│   │   └── services/        # Lógica de negócio
│   └── requirements.txt      # Dependências Python
│
├── api/                      # Serverless function para Vercel
│   └── index.py             # Entry point da API
│
├── scripts/                  # Scripts auxiliares
│   └── e2e_test.py         # Testes end-to-end
│
├── vercel.json              # Configuração Vercel
├── requirements.txt         # Dependências root
└── README.md               # Este arquivo
```

## 👥 Contas de Teste

Após rodar o seed, as seguintes contas estão disponíveis:

### Cliente
- **Email**: `cliente.teste@levaleve.com`
- **Senha**: `Cliente123!`

### Motorista
- **Email**: `motorista.teste@levaleve.com`
- **Senha**: `Motorista123!`

## 🌐 Deploy no Vercel

### Passos para Fazer Deploy

1. **Faça Push do Repositório**
   ```bash
   git add .
   git commit -m "Preparado para deploy"
   git push origin main
   ```

2. **Conecte ao Vercel**
   - Acesse [vercel.com](https://vercel.com)
   - Clique em "New Project"
   - Conecte seu repositório GitHub/GitLab/Bitbucket
   - Selecione este repositório

3. **Configure Variáveis de Ambiente**
   - No painel Vercel, vá para Settings → Environment Variables
   - Adicione `DATABASE_URL` com a URL do Vercel Postgres ou PostgreSQL externo

4. **Deploy**
   - Clique em "Deploy"
   - O Vercel buildará e deployará automaticamente

### Como Funciona o Deploy

- **Frontend**: Servido como static assets pelo FastAPI
- **Backend**: Executado como serverless function via `api/index.py`
- **Banco de Dados**: PostgreSQL (Vercel Postgres recomendado)

## 📝 Comandos Úteis

```bash
# Instalar dependências
pip install -r backend/requirements.txt

# Rodar servidor desenvolvimento
uvicorn app.main:app --reload

# Rodar servidor produção
gunicorn app.main:app

# Executar testes
python scripts/e2e_test.py

# Resetar banco de dados
# (Delete todos os dados e rerun seed.py)
```

## 🤝 Contribuindo

1. Crie uma branch: `git checkout -b feature/sua-feature`
2. Commit suas mudanças: `git commit -m "Adiciona sua feature"`
3. Push para a branch: `git push origin feature/sua-feature`
4. Abra um Pull Request

## 📄 Licença

Este projeto é de uso interno.

## 📞 Suporte

Para dúvidas ou problemas, consulte a documentação da API em `/docs` (quando o servidor estiver rodando).

https://github.com/EricBReinhardt/Leva-Leve---Web-app-de-mudancas
