## 2026-06-18 — Start implementation of #20: PostgreSQL + SQLAlchemy + Docker setup

**Action:** Create feature branch feat/postgres-sqlalchemy-docker and begin implementing the database foundation: Docker Compose with PostgreSQL + pgvector, SQLAlchemy 2 async, Alembic migrations, Recipe model per architecture.md

**Rationale:** This is the foundational infrastructure that blocks all other issues (#8, #9, #10, #11, #12, #13, #14, #16). Must complete first.

**Trade-offs:** 
- Using SQLAlchemy 2 async (modern, better performance) vs sync (simpler)
- Docker Compose for local dev vs bare-metal PostgreSQL (Docker ensures consistency)
- pgvector HNSW index (better for production) vs IVFFlat (simpler) — will use HNSW
- Embedding dimension TBD pending OpenRouter model test — will make migration flexible