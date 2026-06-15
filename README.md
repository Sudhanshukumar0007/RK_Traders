# Supreme Hardware Store

Full-stack e-commerce platform for hardware & plumbing supplies (UPVC fittings, pipes, etc.).

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI (Python), SQLAlchemy (async), Alembic |
| Database | PostgreSQL 16 |
| Search | PostgreSQL FTS + RapidFuzz fuzzy fallback |
| Auth | JWT (access + refresh tokens), bcrypt |
| Shipping | Shiprocket (Phase 5) |
| Payments | Razorpay (Phase 6) |

## Project Structure

```
/
├── frontend/          # Next.js 14 App Router
├── backend/           # FastAPI
│   ├── app/
│   │   ├── core/      # config, database, security
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── routers/   # API route modules
│   │   └── services/  # Business logic
│   ├── alembic/       # DB migrations
│   ├── tests/
│   └── requirements.txt
├── docker-compose.yml
└── .env.example
```

## Getting Started

### 1. Prerequisites

- Docker Desktop (for PostgreSQL)
- Python 3.12+
- Node.js 20+
- npm

### 2. Environment Setup

```bash
# Copy and fill in your environment variables
cp .env.example backend/.env
cp .env.example frontend/.env.local   # only NEXT_PUBLIC_* vars needed here
```

### 3. Start the Database

```bash
docker-compose up -d
# Postgres will be available at localhost:5432
```

### 4. Start the Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

Backend available at: http://localhost:8000  
API docs: http://localhost:8000/docs

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:3000

### 6. Verify the Stack

Open http://localhost:3000 — the frontend should call `GET /health` and receive:
```json
{ "status": "ok", "api": "ok", "db": "connected" }
```

## Build Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Scaffolding & Architecture | 🔄 In Progress |
| 1 | Database Schema & Product Catalog | ⏳ Pending |
| 2 | Backend API — Products, Categories, Search | ⏳ Pending |
| 3 | Backend API — Cart, Auth, Orders | ⏳ Pending |
| 4 | Frontend Storefront UI | ⏳ Pending |
| 5 | Shipping & Logistics (Shiprocket) | ⏳ Pending |
| 6 | Payments (Razorpay) | ⏳ Pending |
| 7 | Admin Dashboard | ⏳ Pending |
