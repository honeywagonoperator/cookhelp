## 2026-06-18 — Start implementation of #20: PostgreSQL + SQLAlchemy + Docker setup

**Action:** Create feature branch feat/postgres-sqlalchemy-docker and begin implementing the database foundation: Docker Compose with PostgreSQL + pgvector, SQLAlchemy 2 async, Alembic migrations, Recipe model per architecture.md

**Rationale:** This is the foundational infrastructure that blocks all other issues (#8, #9, #10, #11, #12, #13, #14, #16). Must complete first.

**Trade-offs:**
- Using SQLAlchemy 2 async (modern, better performance) vs sync (simpler)
- Docker Compose for local dev vs bare-metal PostgreSQL (Docker ensures consistency)
- pgvector HNSW index (better for production) vs IVFFlat (simpler) — will use HNSW
- Embedding dimension TBD pending OpenRouter model test — will make migration flexible


## 2026-06-18 — Completed #20: PostgreSQL + SQLAlchemy + Docker foundation

**Action:** Implemented complete database foundation and created draft PR #22

**Files Created:**
- docker-compose.yml — app + postgres (pgvector/pg16) services with health checks
- Dockerfile — Python 3.12 slim, optimized layers
- alembic.ini + alembic/env.py — async migration config
- alembic/versions/0001_initial_migration.py — recipes table with pgvector HNSW index
- init-db/01-init-extensions.sql — pgvector extension initialization
- app/core/config.py — Pydantic Settings with .env support
- app/database/connection.py — AsyncEngine, session factory, lifespan
- app/models/recipe.py — Recipe model per architecture.md spec
- app/repositories/recipe.py — RecipeRepository (CRUD + vector search)
- app/schemas/recipe.py — Pydantic schemas for validation
- app/services/recipe.py — RecipeService layer
- app/main.py — FastAPI app with /health, /health/db endpoints
- requirements.txt — all dependencies
- .env.example — environment template

**Key Decisions:**
- Embedding dimension set to 1024 (placeholder, will verify with nvidia/llama-nemotron-embed-vl-1b-v2:free)
- HNSW index on embedding column for cosine similarity
- JSONB for ingredients, steps, tags, source (flexible schema)
- Repository pattern: pure DB ops; Service layer: business logic + validation
- Health check endpoints for container orchestration

**PR:** https://github.com/honeywagonoperator/cookhelp/pull/22 (draft)

**Next:** Test Docker Compose locally, verify migration, test embedding dimension with OpenRouter model


## 2026-06-18 — Docker build & deployment fixes

**Action:** Fixed Docker build issues for Russian network environment

**Problems solved:**
1. Docker Hub blocked in Russia — switched to `dh-mirror.gitverse.ru` mirror
2. Python 3.12-slim pull failures — working mirror found
3. `faker==3.3.1` doesn't exist — changed to `faker>=30.0.0`
4. `lxml==5.2.2` conflicts with `trafilatura` — changed to `lxml<5.2.0,>=4.9.4`
5. Migration import error — `VECTOR` from `pgvector.sqlalchemy` not SQLAlchemy dialect

**Final working config:**
- Base image: `dh-mirror.gitverse.ru/library/python:3.12-slim`
- PGVector: `dh-mirror.gitverse.ru/pgvector/pgvector:pg16`
- All dependencies install successfully

**Verification:**
- Containers start healthy
- Migration runs: recipes table + alembic_version + pgvector extension + HNSW index
- Health endpoints: `/health` → `{"status":"ok"}`, `/health/db` → `{"status":"ok","database":"connected"}`


## 2026-06-18 — Next Steps (Plan)

### Ready to proceed with next issues:

| Priority | Issue | Description | Depends On |
|----------|-------|-------------|------------|
| **1** | **#11** | AI Service (OpenRouter): extract_recipe, classify_intent, edit_recipe, generate_embedding, generate_tags, rerank_search_results | ✅ #20 done |
| **2** | **#21** | Recipe CRUD Repository & Service — already implemented in #20! | ✅ Done in #20 |
| **3** | **#8** | Add recipe from text input (uses #11) | #11 |
| **4** | **#9** | Add recipe from website URL (uses #11 + trafilatura) | #11 |
| **5** | **#10** | Add recipe from YouTube (uses #11 + youtube-transcript-api) | #11 |
| **6** | **#19** | Telegram Bot setup (aiogram 3): main menu, FSM, commands | #20 |
| **7** | **#12** | Embeddings + pgvector (test `nvidia/llama-nemotron-embed-vl-1b-v2:free` dimension) | #11, #20 |
| **8** | **#13** | AI Search: query → embed → vector search → LLM rerank | #12, #19 |
| **9** | **#14** | AI Editing: load → LLM edit → re-normalize → re-embed → save | #11, #12, #19 |
| **10** | **#15** | Free Input: intent classification → route to handlers | #11, #19 |
| **11** | **#16** | List/Management: paginated list, delete, "последние рецепты" | #20, #19 |
| **12** | **#17** | Testing: pytest + pytest-asyncio, CI, >80% coverage | Core features |
| **13** | **#18** | Observability: structured logging, Sentry, rate limiting | Core features |

### Immediate next action:
**Start #11 (AI Service)** — implements all LLM functions needed for recipe creation, search, and editing. This unblocks #8, #9, #10, #12, #13, #14, #15.

### Note on embedding dimension:
Need to test `nvidia/llama-nemotron-embed-vl-1b-v2:free` via OpenRouter to confirm actual dimension (likely 1024 or 2048), then update migration if needed.


## 2026-06-18 — Started #19: Telegram bot setup with aiogram 3

**Action:** Created feature branch `feat/telegram-bot`, implemented bot foundation, created draft PR #24

**Files created:**
- `app/bot/__init__.py` — Bot + Dispatcher setup, polling/webhook, start/stop
- `app/bot/states.py` — FSM: CreateRecipeStates, SearchStates, FreeInputStates
- `app/bot/keyboards.py` — Main menu keyboard (4 buttons)
- `app/bot/handlers/start.py` — /start, /help, main menu
- `app/bot/handlers/create_recipe.py` — "Создать рецепт" FSM flow
- `app/bot/handlers/search.py` — "Найти рецепт" FSM flow
- `app/bot/handlers/free_input.py` — "Свободный ввод" FSM flow
- `app/bot/middlewares.py` — Logging + error handling middlewares

**Files modified:**
- `app/core/config.py` — Added `bot_use_webhook`, `bot_webhook_url`
- `app/main.py` — Bot lifecycle in FastAPI lifespan

**PR:** https://github.com/honeywagonoperator/cookhelp/pull/24 (draft)

**Next:** Need user approval → merge → proceed to #12 (Embeddings + pgvector)