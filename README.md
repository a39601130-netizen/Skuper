# 🤖 Life Manager Bot

Telegram бот для управления финансами и тренировками с AI-советником.

**Разработан для Артура Султанова**  
*Human Design: Эмоциональный Проектор 2/4*

---

## 📋 Модули

### 💰 Финансы
- Учёт доходов и расходов
- Балансы счетов
- Статистика по категориям

### 🏋️ Тренировки
- Отслеживание прогресса по программе
- Рекомендации веса (двойная прогрессия)
- Таймер отдыха
- Учёт энергии и самочувствия

### 🤖 AI Советник (DeepSeek)
- Анализ тренировок и финансов
- Персонализированные рекомендации
- Учёт Human Design профиля

---

## 🚀 Установка

### 1. Клонирование
```bash
git clone <your-repo>
cd life_manager_bot
```

### 2. Виртуальное окружение
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Зависимости
```bash
pip install -r requirements.txt
```

### 4. Конфигурация
```bash
cp .env.example .env
# Заполни .env своими данными
```

### 5. Google Credentials
Положи файл `google_credentials.json` в корень проекта.

### 6. Google Sheets
- Создай таблицу для тренировок (используй шаблон)
- Добавь Service Account email в доступ к таблице
- Скопируй ID таблицы в `.env`

---

## 🏃 Запуск

### Обычный запуск
```bash
python main.py
```

### В VS Code
Нажми `F5` для запуска с отладкой.

---

## 📁 Структура проекта

```
life_manager_bot/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── bot/
│   ├── states.py        # Состояния диалогов
│   ├── handlers/
│   │   ├── start.py     # /start, /help
│   │   ├── menu.py      # Главное меню
│   │   ├── finance/     # Модуль финансов
│   │   └── workout/     # Модуль тренировок
│   └── keyboards/       # Клавиатуры
├── services/
│   ├── sheets.py        # Google Sheets
│   ├── workout_sheets.py
│   └── ai_advisor.py    # DeepSeek
└── utils/
    └── formatters.py
```

---

## 🔧 Переменные окружения (.env)

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен от @BotFather |
| `TELEGRAM_USER_ID` | Твой Telegram ID |
| `GOOGLE_SHEETS_FINANCE_ID` | ID таблицы финансов |
| `GOOGLE_SHEETS_WORKOUT_ID` | ID таблицы тренировок |
| `DEEPSEEK_API_KEY` | Ключ API DeepSeek |
| `USER_TIMEZONE` | Часовой пояс (Europe/Minsk) |
| `USER_NAME` | Имя для приветствий |

---

## 📱 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/help` | Справка |
| `/workout` | Начать тренировку |
| `/weights` | Текущие веса |
| `/progress` | Прогресс |
| `/advisor` | AI советник |

---

## 🧘 Human Design интеграция

Бот учитывает твой профиль:

- ⏱️ **Ограничение времени** — напоминания о 45-60 минутах
- ⚡ **Энергия** — предупреждения при низком уровне
- 🌊 **Эмоциональная волна** — учёт при анализе
- 🛑 **Остановка ДО усталости** — рекомендации по завершению

---

*Создано с 💚 Январь 2025*
