# Архитектура проекта: cookhelp

## Цель проекта

Персональный Telegram-бот для хранения, редактирования и поиска рецептов с использованием LLM.

Проект рассчитан на одного пользователя.

Разворачивается локально на домашнем сервере.

Интерфейс взаимодействия — исключительно Telegram.

---

# Основные сценарии

## Добавление рецепта

Пользователь отправляет:

- текст рецепта;
- URL сайта с рецептом.

Система:

1. Извлекает содержимое.
2. Преобразует в структурированный рецепт.
3. Переводит на русский язык при необходимости.
4. Нормализует структуру.
5. Генерирует embedding.
6. Сохраняет рецепт в БД.

---

## AI-редактирование

Примеры запросов:

- Сделай рецепт менее острым
- Замени курицу на индейку
- Сделай вегетарианскую версию
- Сократи время приготовления

Система:

1. Загружает рецепт.
2. Передаёт рецепт и инструкцию в LLM.
3. Получает обновлённую версию.
4. Пересчитывает embedding.
5. Сохраняет изменения.

---

## AI-поиск

Примеры:

- Что приготовить из курицы и картофеля?
- Найди быстрый ужин до 30 минут
- Покажи азиатские блюда
- Что можно приготовить без мяса?

Система:

1. Создаёт embedding запроса.
2. Выполняет поиск по pgvector.
3. Передаёт найденные кандидаты в LLM.
4. LLM ранжирует результаты.
5. Пользователю возвращаются наиболее подходящие рецепты.

---

## Свободный ввод

Поддерживаемые интенты:

- ADD_RECIPE
- SEARCH_RECIPE
- EDIT_RECIPE
- SHOW_RECIPE
- LIST_RECIPES
- HELP

---

# Технологический стек

## Backend

- Python 3.12+
- FastAPI

## Telegram

- aiogram 3

## Database

- PostgreSQL
- pgvector

## ORM

- SQLAlchemy 2

## Migrations

- Alembic

## AI

- OPENROUTER API

Используется для:

- извлечения рецептов;
- нормализации;
- перевода;
- классификации интентов;
- поиска;
- редактирования рецептов.

---

# Инфраструктура

Использовать Docker Compose.

Система состоит из двух контейнеров:

- app
- postgres

## Docker Compose

### app

- FastAPI
- Aiogram
- SQLAlchemy
- OpenAI Client

### postgres

- PostgreSQL
- pgvector

Использовать persistent volume для хранения данных PostgreSQL.

---

# Структура проекта

```text
project-root/
│
├── app/
│   ├── api/
│   ├── bot/
│   ├── database/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── ai/
│   ├── parsers/
│   └── core/
│
├── alembic/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env
```

---

# Слои приложения

## Bot Layer

Отвечает за Telegram.

Не содержит бизнес-логики.

## Service Layer

Основная бизнес-логика.

Сервисы:

- RecipeService
- SearchService
- ImportService
- AiService

## Repository Layer

Работа с БД.

## AI Layer

Функции:

- extract_recipe()
- translate_recipe()
- normalize_recipe()
- classify_intent()
- edit_recipe()
- rerank_search_results()
- generate_embedding()

## Parser Layer

### Website Parser

Инструменты:

- trafilatura
- beautifulsoup4



---

# База данных

## Основная таблица recipes

Структура рецепта:

```json
{
  "id": "uuid",
  "title": "Пад Тай",
  "description": "Тайская жареная лапша с креветками",
  "ingredients": [
    "рисовая лапша",
    "креветки",
    "яйцо"
  ],
  "steps": [
    "Замочить лапшу",
    "Обжарить креветки",
    "Добавить яйцо"
  ],
  "tags": [
    "тайская кухня",
    "лапша",
    "ужин"
  ],
  "source": {
    "type": "website",
    "url": "https://example.com/recipe..."
  },
  "embedding": [],
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

Поля таблицы:

- id
- title
- description
- ingredients (JSONB)
- steps (JSONB)
- tags (JSONB)
- source (JSONB)
- embedding (VECTOR)
- created_at
- updated_at

Принципы:

- Теги генерируются автоматически через LLM.
- Все рецепты хранятся только на русском языке.
- Оригинальный текст рецепта не сохраняется.
- Сохраняется только ссылка на источник.
- Отдельные таблицы recipe_sources и recipe_versions в MVP не используются.

---

# Векторный поиск

Использовать pgvector.

Схема:

Название + описание + ингредиенты + теги
→ Embedding
→ recipes.embedding

Поиск:

Запрос
→ Embedding
→ Top-K поиск через pgvector
→ LLM reranking
→ Ответ пользователю

---

# Требования к данным

Все рецепты должны храниться исключительно на русском языке.

Если источник не на русском:

Источник
→ Перевод
→ Нормализация
→ Сохранение

Оригинальный текст не хранить.

Сохранять только URL источника.

---

# Планы в дальнейшем

1. Создание функционала списка покупок
2. Подключение внешнего API (к примеру, spooncacular)

---

# План реализации

1. PostgreSQL + SQLAlchemy
2. CRUD рецептов
3. Telegram Bot
4. Добавление рецептов текстом
5. Добавление рецептов по URL
6. ~~Импорт из YouTube~~ (отменено)
7. AI-нормализация
8. Embeddings + pgvector
9. AI-поиск
10. AI-редактирование

Не пытаться реализовать весь проект одной итерацией.
