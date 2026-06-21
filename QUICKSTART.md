# Quick Start Guide

Быстрый запуск эксперимента за 5 минут.

## Шаг 1: Подготовка GitHub

1. **Fork репозиторий** (или используйте свой)
2. **Создайте GitHub Token**:
   - Идите на https://github.com/settings/tokens
   - "Generate new token (classic)"
   - Выберите scope: `repo` (полный доступ)
   - Скопируйте token

## Шаг 2: Получите Claude API Key

1. Идите на https://console.anthropic.com/
2. Создайте API key
3. Скопируйте ключ

## Шаг 3: Запуск 3 агентов на Colab

### Агент 1

1. Откройте: https://colab.research.google.com/github/wtf403/portfolio-rebalancing/blob/master/Portfolio_Rebalancing_Agent.ipynb
2. Добавьте секреты (левая панель → 🔑):
   - `ANTHROPIC_API_KEY` = ваш Claude key
   - `GITHUB_TOKEN` = ваш GitHub token
3. Установите в коде:
   ```python
   AGENT_ID = "agent_1"
   GENERATION = 0
   ```
4. Runtime → Run all

### Агент 2

1. Откройте ноутбук в **новой вкладке** (не копируйте в Drive!)
2. Те же секреты
3. Установите:
   ```python
   AGENT_ID = "agent_2"
   GENERATION = 0
   ```
4. Runtime → Run all

### Агент 3

1. Откройте ноутбук в **третьей вкладке**
2. Те же секреты
3. Установите:
   ```python
   AGENT_ID = "agent_3"
   GENERATION = 0
   ```
4. Runtime → Run all

## Шаг 4: Наблюдайте результаты

Через 1-2 минуты:

1. Идите на https://github.com/wtf403/portfolio-rebalancing/pulls
2. Увидите 3 Pull Request от агентов
3. GitHub Actions автоматически валидирует каждый
4. Посмотрите комментарии с результатами валидации

## Шаг 5: Следующее поколение

После того как увидели результаты:

1. **Локально запустите оркестратор**:
   ```bash
   git pull
   python orchestrator.py
   ```

2. Он покажет метрики всех агентов и предложит обновить initial_portfolio.json

3. **Закоммитьте изменения**:
   ```bash
   git add experiment/initial_portfolio.json
   git commit -m "Generation 1 start - best from gen 0"
   git push
   ```

4. **В каждом Colab измените**:
   ```python
   GENERATION = 1  # было 0
   ```

5. **Запустите агентов снова** (Runtime → Run all в каждой вкладке)

## Повторяйте

Делайте 5-10 поколений. После каждого:
- `orchestrator.py` показывает прогресс
- `experiment/metrics.csv` хранит всю историю
- Лучший портфель становится базой для следующего поколения

## Результат

После 5 поколений у вас будет:
- 15 портфелей (3 агента × 5 поколений)
- Метрики эволюции fitness
- Понимание, какие стратегии работают
- Данные для анализа конвергенции GA

---

**Время:** ~30 минут на весь эксперимент (5 поколений)  
**Стоимость:** ~$1.50 (15 запусков Claude Sonnet)  
**Сложность:** 🟢 Легко
