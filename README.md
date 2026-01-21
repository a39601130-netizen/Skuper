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

## 🚀 Деплой на сервер

### Docker (рекомендуется)

```bash
# 1. Скопировать проект на сервер
scp -r budget_bot user@server:/opt/

# 2. Создать .env файл
cd /opt/budget_bot
cp .env.example .env
nano .env  # Заполнить данные

# 3. Скопировать google_credentials.json
scp google_credentials.json user@server:/opt/budget_bot/

# 4. Запустить
docker-compose up -d

# Логи
docker-compose logs -f

# Перезапуск
docker-compose restart

# Остановка
docker-compose down
```

### Systemd (без Docker)

```bash
# 1. Создать пользователя
sudo useradd -r -s /bin/false budget_bot

# 2. Установить проект
sudo mkdir /opt/budget_bot
sudo cp -r * /opt/budget_bot/
sudo chown -R budget_bot:budget_bot /opt/budget_bot

# 3. Виртуальное окружение
cd /opt/budget_bot
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 4. Настроить .env
sudo -u budget_bot cp .env.example .env
sudo -u budget_bot nano .env

# 5. Установить сервис
sudo cp budget_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable budget_bot
sudo systemctl start budget_bot

# Логи
sudo journalctl -u budget_bot -f
```

---

*Создано с 💚 Январь 2025*
