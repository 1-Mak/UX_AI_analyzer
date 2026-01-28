# UX AI Audit System

Автоматическая система для выявления проблем юзабилити, доступности (Accessibility) и эмоционального отклика в веб-интерфейсах с использованием AI агентов.

## Описание

Система реализует смешанный метод исследования (Mixed-Methods), объединяя:

- **Module A (The Eye)**: Визуальный инспектор на основе GPT-5-mini Vision
- **Module B (The Hand)**: Поведенческий агент-симулятор с ReAct паттерном
- **Module C (The Structure)**: Аудитор доступности (axe-core + WCAG)
- **Module D (The Heart)**: Анализ эмоций и точек фрустрации (DeepSeek)
- **Module E (The Brain)**: Синтезатор итоговых отчетов

### Целевой контекст
Система оптимизирована для аудита образовательных сайтов (университеты, школы) с тремя ключевыми персонами:
- **Студент** - активный пользователь, ищет расписание и материалы
- **Абитуриент** - новичок на сайте, изучает условия поступления
- **Преподаватель** - публикует материалы и работает с оценками

## Требования

- Python 3.10+
- **OpenAI API ключ** (обязательно) - [получить здесь](https://platform.openai.com/api-keys)
- **DeepSeek API ключ** (опционально) - [получить здесь](https://platform.deepseek.com/api_keys)
- Windows/Linux/MacOS

### LLM архитектура

Система использует двухуровневую LLM архитектуру:

| Модель | Роль | Задачи |
|--------|------|--------|
| **GPT-5-mini** | Основная | Мультимодальный анализ скриншотов, визуальные эвристики, симуляция поведения |
| **DeepSeek** | Вспомогательная | Быстрый анализ тональности, парсинг JSON, валидация выводов |

## Установка

### Шаг 1: Клонирование и создание виртуального окружения

```bash
git clone https://github.com/1-Mak/UX_AI_analyzer.git
cd UX_AI_analyzer

# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### Шаг 2: Установка зависимостей

```bash
# Установите зависимости
pip install -r requirements.txt

# Установите браузеры Playwright
playwright install chromium
```

### Шаг 3: Настройка API ключей

```bash
# Скопируйте шаблон конфигурации
copy .env.example .env   # Windows
# или
cp .env.example .env     # Linux/Mac

# Откройте .env и добавьте ваши API ключи
```

Пример `.env`:
```env
# ===== LLM API Configuration =====

# OpenAI (Обязательно)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-5-mini

# DeepSeek (Опционально, для Module D)
DEEPSEEK_API_KEY=your-deepseek-api-key-here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### Шаг 4: Проверка установки

```bash
# Проверьте конфигурацию
python src/config.py

# Запустите демо Playwright
python src/utils/playwright_helper.py
```

## Использование

### Базовый запуск

```bash
python main.py
```

### Настройка задачи через input.json

Создайте файл `input.json` в корне проекта:

```json
{
  "url": "https://www.hse.ru",
  "task": "Найти расписание занятий для бакалавриата",
  "persona": "student"
}
```

Доступные персоны (образовательный контекст):

- **`student`** - Студент (20 лет, высокий tech level)
  - Цели: быстро найти расписание, скачать материалы, сдать работу онлайн
  - Особенности: многозадачность, ограниченное время между парами

- **`applicant`** - Абитуриент (17 лет, средний tech level)
  - Цели: узнать проходные баллы, найти информацию о поступлении
  - Особенности: первый раз на сайте, стресс от выбора

- **`teacher`** - Преподаватель (45 лет, средний tech level)
  - Цели: загрузить оценки, опубликовать материалы
  - Особенности: много административной работы, ценит эффективность

## Структура проекта

```
UX_AI_Audit/
├── main.py                 # Точка входа и оркестратор
├── requirements.txt        # Зависимости
├── .env.example           # Шаблон конфигурации
├── input.json             # Входные данные для аудита
│
├── src/
│   ├── config.py          # Централизованная конфигурация
│   ├── models.py          # Pydantic модели (персоны, шаги)
│   │
│   ├── modules/           # AI модули
│   │   ├── module_a/      # Visual Inspector (GPT-5-mini Vision)
│   │   ├── module_b/      # Behavioral Agent (ReAct loop)
│   │   ├── module_c/      # Accessibility Auditor (axe-core)
│   │   ├── module_d/      # Sentiment Analyzer (DeepSeek)
│   │   └── module_e/      # Report Synthesizer
│   │
│   └── utils/             # Утилиты
│       ├── playwright_helper.py    # Браузерная автоматизация
│       ├── image_processor.py      # Обработка скриншотов
│       ├── openai_helper.py        # OpenAI API интеграция
│       └── deepseek_helper.py      # DeepSeek API интеграция
│
├── data/
│   ├── screenshots/       # Скриншоты сессий
│   └── reports/          # Итоговые отчеты
│
└── tests/                # Тесты
```

## Текущий статус

### Реализовано

**Module A - Visual Inspector:**
- Анализ скриншотов с GPT-5-mini Vision
- Оценка по 10 эвристикам Нильсена
- Определение критичности проблем (Critical/High/Medium/Low)
- Координатная сетка для точной локализации

**Module B - Behavioral Agent:**
- ReAct-based симуляция поведения пользователя
- Поддержка персон (student, applicant, teacher)
- Действия: click, type, scroll, wait, go_back, go_to
- Отслеживание эмоционального состояния
- Лог поведения в JSON формате

**Module C - Accessibility Auditor:**
- Интеграция с axe-core через axe-playwright-python
- Поддержка уровней WCAG (A, AA, AAA)
- Мульти-страничное сканирование по логу Module B
- Группировка проблем по impact (critical, serious, moderate, minor)

**Инфраструктура:**
- Модульная архитектура с Pydantic моделями
- Playwright helper для браузерной автоматизации
- Image processor с координатной сеткой
- Централизованная конфигурация через .env

### В разработке

- **Module D**: Анализ тональности через DeepSeek API (план готов)
- **Module E**: Генерация PDF отчетов (Jinja2 + WeasyPrint)

## Примеры вывода

### Module A - Visual Analysis
```
  ────────────────────────────────────
  MODULE A: VISUAL ANALYSIS SUMMARY
  ────────────────────────────────────
    Total Issues: 8
    Critical: 2 | High: 3 | Medium: 2 | Low: 1

    Overall Assessment:
    The interface has significant navigation and
    visibility issues that impact user experience...
```

### Module B - Behavioral Simulation
```
  ────────────────────────────────────
  MODULE B: BEHAVIORAL LOG SUMMARY
  ────────────────────────────────────
    Total Steps: 7
    Task Status: completed
    Emotional Trend: declining
```

### Module C - Accessibility Audit
```
  ────────────────────────────────────
  MODULE C: ACCESSIBILITY SUMMARY
  ────────────────────────────────────
    WCAG Level: AA
    Total Issues: 4 (67 affected nodes)

    By Impact:
      critical: 0
      serious: 2 (63 nodes)
      moderate: 1 (3 nodes)
      minor: 1 (1 node)
```
