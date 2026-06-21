# ✅ MVP Эксперимента - Готово к запуску

## Что реализовано

Простой генетический алгоритм с 3 Claude-агентами на Google Colab для оптимизации портфеля.

### ✅ Инфраструктура

1. **Google Colab Notebook** (`Portfolio_Rebalancing_Agent.ipynb`)
   - Готов к запуску в 3 браузерных вкладках
   - Настройка через секреты (ANTHROPIC_API_KEY, GITHUB_TOKEN)
   - Параметры: AGENT_ID, GENERATION

2. **Python Agent** (`colab_agent.py`)
   - Клонирует репозиторий
   - Загружает портфель и вселенную активов
   - Вызывает Claude API для анализа
   - Создает Pull Request с предложением

3. **GitHub Actions** (`.github/workflows/validate_portfolio.yml`)
   - Автоматически валидирует каждый PR
   - Проверяет ограничения (веса, число активов)
   - Постит результат как комментарий

4. **Валидатор** (`experiment/validate_portfolio.py`)
   - Проверяет sum(weights) = 1.0
   - Проверяет 0.05 ≤ weight ≤ 0.25
   - Проверяет 8 ≤ num_assets ≤ 12
   - Возвращает метрики

5. **Оркестратор** (`orchestrator.py`)
   - Анализирует поколение
   - Вычисляет fitness
   - Выбирает лучший портфель
   - Обновляет initial_portfolio.json
   - Экспортирует metrics.csv

### ✅ Конфигурация

- `experiment/config.yaml` — параметры (3 агента, 5 поколений)
- `experiment/initial_portfolio.json` — стартовый портфель (10 активов)
- `experiment/agent_prompt.md` — инструкции для Claude
- `experiment/results/` — директория для PR результатов

### ✅ Документация

- `README.md` — полное описание проекта
- `QUICKSTART.md` — запуск за 5 минут
- `experiment/results/README.md` — формат результатов

## Как запустить

### Шаг 1: Подготовка (1 раз)

1. **GitHub Token**: https://github.com/settings/tokens
   - Scope: `repo`
   
2. **Claude API Key**: https://console.anthropic.com/
   - Создать API key

### Шаг 2: Запуск агентов (каждое поколение)

Откройте в 3 вкладках браузера:
**https://colab.research.google.com/github/wtf403/portfolio-rebalancing/blob/master/Portfolio_Rebalancing_Agent.ipynb**

В **каждой вкладке**:

1. Добавьте секреты (левая панель → 🔑 Secrets):
   ```
   ANTHROPIC_API_KEY = ваш_ключ
   GITHUB_TOKEN = ваш_токен
   ```

2. Измените параметры:
   ```python
   # Вкладка 1:
   AGENT_ID = "agent_1"
   GENERATION = 0
   
   # Вкладка 2:
   AGENT_ID = "agent_2"
   GENERATION = 0
   
   # Вкладка 3:
   AGENT_ID = "agent_3"
   GENERATION = 0
   ```

3. **Runtime → Run all** (в каждой вкладке)

### Шаг 3: Наблюдение (автоматически)

- Через 1-2 минуты: 3 Pull Requests созданы
- GitHub Actions валидирует каждый
- Комментарии с результатами появятся в PR

### Шаг 4: Оркестрация (локально)

```bash
# После merge PR (или без него, если есть файлы в experiment/results/)
git pull
python orchestrator.py

# Он покажет метрики и предложит обновить initial_portfolio.json
# Нажмите 'y' для обновления

git add experiment/initial_portfolio.json
git commit -m "Generation 1 start - best from gen 0"
git push
```

### Шаг 5: Следующее поколение

В каждой Colab вкладке:

```python
GENERATION = 1  # было 0
```

Runtime → Run all (в каждой вкладке)

**Повторяйте шаги 3-5 для поколений 1, 2, 3, 4**

## Ожидаемый результат

После 5 поколений:

```
experiment/results/
├── gen0_agent_1_portfolio.json
├── gen0_agent_2_portfolio.json
├── gen0_agent_3_portfolio.json
├── gen1_agent_1_portfolio.json
├── gen1_agent_2_portfolio.json
├── gen1_agent_3_portfolio.json
...
└── gen4_agent_3_portfolio.json

experiment/metrics.csv:
generation,agent,fitness,num_assets,max_weight,min_weight,expected_sharpe
0,agent_1,1.45,9,0.15,0.07,1.45
0,agent_2,1.38,10,0.14,0.08,1.38
0,agent_3,1.52,8,0.18,0.09,1.52
1,agent_1,1.61,9,0.16,0.08,1.61
...
```

## Метрики успеха

✅ **Эксперимент успешен, если:**

1. Все 3 агента создают валидные PR в каждом поколении
2. GitHub Actions не блокирует ни один PR
3. Fitness растет от поколения к поколению
4. Популяция не коллапсирует (агенты предлагают разные решения)
5. metrics.csv показывает конвергенцию

## Стоимость и время

| Параметр | Значение |
|----------|----------|
| **Поколений** | 5 |
| **Агентов** | 3 |
| **Запросов к Claude** | 15 (3 × 5) |
| **Стоимость** | ~$1.50 |
| **Время на поколение** | 2-3 мин |
| **Время оркестрации** | 1 мин |
| **Общее время** | ~20 минут |

## Что дальше (не в MVP)

### Фаза 2: Реальный backtest
- Загрузить историческую доходность из CSV
- Вычислить реальный Sharpe ratio
- Заменить `expected_sharpe` на backtest результат

### Фаза 3: Кроссовер
- Выбирать 2 родителей
- Скрещивать их (uniform/blend crossover)
- Агенты улучшают потомков

### Фаза 4: Разнообразие
- Стартовать с 3 разных портфелей
- Измерять similarity
- Штрафовать одинаковые решения

### Фаза 5: Масштабирование
- 10-30 агентов параллельно
- Автоматический merge и запуск следующего поколения
- Непрерывная эволюция

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| 401 Unauthorized | Проверьте API keys в Colab Secrets |
| Total weight != 1.0 | Claude не нормализовал — повторите |
| No JSON found | Улучшите промпт или retry |
| git push failed | Проверьте GITHUB_TOKEN scope (repo) |
| Validation failed | Посмотрите PR comment — какие ограничения нарушены |

## Коммит

```bash
git log -1 --oneline
# 423e314 feat: Add MVP genetic algorithm experiment with Claude agents

git show --stat
# 313 files changed, 321856 insertions(+), 55 deletions(-)
```

## Следующий шаг

**🚀 Запустите первое поколение!**

1. Откройте ноутбук в 3 вкладках
2. Добавьте секреты
3. Запустите агентов
4. Наблюдайте за PR
5. Запустите оркестратор

---

**Готово к эксперименту ✅**
