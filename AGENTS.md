# CookHelp — AGENTS.md

## Project Overview

**CookHelp** — персональный Telegram-бот для хранения, редактирования и поиска рецептов с использованием LLM.

**Стэк:** Python 3.12+, FastAPI, aiogram 3, PostgreSQL + pgvector, SQLAlchemy 2, Alembic, OPENROUTER API

Архитектура: `architecture.md`
UX/Флоу: `telegram-userflow.md`

---

## Session Logging

Все действия и решения агента записываются в `SESSION.md` в корне проекта.

**Запись добавляется перед каждым значимым действием:**
```
## <timestamp> — <что делаем>

**Action:** <что именно делаем>
**Rationale:** <почему делаем именно так>
**Trade-offs:** <какие альтернативы рассматривали, почему выбрали эту>
```

Прочитать последние записи: `read("SESSION.md")`

Перед каждым шагом воркфлоу — **сначала запиши действие в SESSION.md**, потом выполняй.

---

## Skills

| Skill | Назначение |
|---|---|
| `load skill vibe-coding` | Воркфлоу кодинга — когда использовать context7, sequential-thinking, serena |
| `load skill github` | GitHub workflow — ветки, PR, issues, code review |

---

## Workflow

### 1. Анализ запроса

→ записать в `SESSION.md`

**Новый запрос / идея / фича:**
- `github_create_issue` — создать issue с Acceptance Criteria, labels, assignee

**Запрос на выполнение существующей фичи:**
- `github_search_issues` / `github_get_issue` — прочитать issue
- Если issue не найдено — уточнить у пользователя, создать новое

### 2. Создание feature branch + Draft PR

`load skill github`:

```
github_create_branch({ branch: "feat/<name>", from_branch: "main" })
github_create_pull_request({ head: "feat/<name>", base: "main", draft: true })
```

**Жизненно важно:** каждая фича — отдельная ветка. Никаких коммитов в main.

> **Note:** GitHub MCP server не работает — используй встроенные tools `github_create_branch`, `github_push_files`, `github_create_pull_request` напрямую, `load skill github` не требуется.

### 3. Планирование

→ записать в `SESSION.md`
`load skill vibe-coding` → **sequential-thinking**:

- Разобрать задачу на шаги
- Оценить сложность, риски, зависимости
- Если не хватает контекста — **задать уточняющие вопросы пользователю**

> **Пользователь — менеджер проекта, не разработчик.** Агент обязан:
> - Предлагать лучшие engineering-решения, даже если они противоречат первоначальной идее
> - Объяснять trade-offs простым языком
> - Направлять, а не просто исполнять
> - Не соглашаться на технический компромисс без явного осознанного решения

### 4. Реализация (код)

→ записать в `SESSION.md`
`load skill vibe-coding`:

- **context7** — для документации библиотек (если нужен новый пакет или API)
- **serena** — для навигации по коду и редактирования
- Писать код в соответствии с архитектурой проекта (см. `architecture.md`)
- Коммиты через `load skill github` → `github_push_files` (формат сообщений — в github skill)

### 5. Тестирование

→ записать в `SESSION.md`

- Юнит-тесты для новой логики
- Интеграционное/функциональное тестирование (если нужно)
- Прогнать тесты, убедиться что всё зелёное
- Фреймворк: pytest + pytest-asyncio 0.24.0
- Команда: `python -m pytest tests/ -v` (см. Known Issues про pytest-asyncio)

### 6. Подтверждение

→ записать в `SESSION.md`

Показать пользователю **diff изменений** (summary ключевых файлов):

- Какие файлы добавлены/изменены
- Ключевые моменты реализации
- Trade-offs, если были

Получить approval перед merge. Если пользователь просит изменить — вернуться к шагу 4.

### 7. Merge

→ записать в `SESSION.md`
`load skill github`:

```
github_merge_pull_request({ merge_method: "squash" })
```

### 8. Rollback (если что-то пошло не так)

→ записать в `SESSION.md`
Если после мержа обнаружена проблема:

1. `github_create_branch({ branch: "fix/rollback-<description>", from_branch: "main" })`
2. Откатить изменения (revert коммит через `github_push_files`)
3. `github_create_pull_request({ ... })` → `github_merge_pull_request`
4. Создать новый issue на исправление проблемы

---

## Guiding Principles

1. **Quality over speed** — цель не «сделать быстро», а «сделать правильно»
2. **Challenge the user** — менеджер может ошибаться в технических решениях; аргументированно предлагай лучшее
3. **Skills first** — coding → `load skill vibe-coding`, git → `load skill github`
4. **Ask, don't assume** — если не хватает контекста или требования противоречивы — уточни
5. **Each feature = one branch** — никаких исключений
6. **Architecture-aware** — все изменения должны соответствовать data model и pipeline из `architecture.md`
7. **Russian-only recipes** — все рецепты хранятся только на русском; оригинальный текст не сохраняется, только URL источника

---

## Implementation Plan (from architecture.md)

1. PostgreSQL + SQLAlchemy
2. CRUD рецептов
3. Telegram Bot
4. Добавление рецептов текстом
5. Добавление рецептов по URL
6. Импорт из YouTube
7. AI-нормализация
8. Embeddings + pgvector
9. AI-поиск
10. AI-редактирование

*Не пытаться реализовать весь проект одной итерацией.*