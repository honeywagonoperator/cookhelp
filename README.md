# CookHelp — Telegram Bot для хранения и поиска рецептов

Персональный Telegram‑бот на AI для хранения, редактирования и поиска рецептов. Работает через **OpenRouter** (Claude, GPT, Llama), хранит всё в **PostgreSQL + pgvector**.

## Возможности

| Функция | Как работает |
|---------|-------------|
| **Добавление текстом** | Пришли текст рецепта → AI извлекает название, ингредиенты, шаги, теги |
| **Добавление по URL** | Ссылка на сайт → парсинг → AI-нормализация → сохранение |
| **Поиск по смыслу** | "что приготовить из курицы" → embedding + векторный поиск + LLM rerank |
| **AI-редактирование** | "сделай менее острым" → AI меняет ингредиенты и шаги |
| **Free‑input mode** | Любое сообщение → AI понимает намерение и маршрутизирует |
| **Список рецептов** | Пагинированный список с удалением |

## Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/honeywagonoperator/cookhelp.git
cd cookhelp

# 2. Настроить окружение
cp .env.example .env
# → Заполнить OPENROUTER_API_KEY и BOT_TOKEN

# 3. Запустить Docker
docker compose up --build -d

# 4. Миграция БД
docker compose exec app alembic upgrade head
```

### Или локально (без Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.main
```

## Технологии

- **Python 3.12**, FastAPI, aiogram 3
- **PostgreSQL 16 + pgvector** — векторный поиск
- **SQLAlchemy 2** (async) + Alembic
- **OpenRouter** — единый API для Claude, GPT, Llama
- **Embeddings** — `nvidia/llama-nemotron-embed-vl-1b-v2:free` (2048 dim), HNSW index

## Архитектура

```
TG Bot → Handlers → AI Service → OpenRouter
                  → Recipe Service → Repository → PostgreSQL
                                     → AI Service → Embedding → pgvector
```

## Переменные окружения (`.env`)

| Переменная | Описание |
|-----------|----------|
| `DATABASE_URL` | postgresql+asyncpg://user:pass@host:5432/db |
| `OPENROUTER_API_KEY` | Ключ OpenRouter (openrouter.ai/keys) |
| `BOT_TOKEN` | Токен Telegram бота (@BotFather) |
| `EMBEDDING_MODEL` | Модель эмбеддингов (по умолч. `nvidia/llama-nemotron-embed-vl-1b-v2:free`) |
| `EMBEDDING_DIMENSION` | Размерность вектора (2048) |
| `BOT_USE_WEBHOOK` | `true` для webhook (по умолч. polling) |

## Тестирование

```bash
python -m pytest tests/ -v
```

## Лицензия

MIT