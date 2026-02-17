"""
Скрипт для синхронизации структуры Google Sheets с функционалом бота
Проверяет и обновляет все листы: Транзакции, Счета, Категории, Справочники
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config

# Эталонная структура данных (из кода бота)

# Типы транзакций
REQUIRED_TYPES = [
    "Доход",
    "Расход",
    "Перевод",
    "Обмен валюты"
]

# Категории доходов
INCOME_CATEGORIES = [
    "Зарплата",
    "Чаевые",
    "Подработка",
    "Другое"
]

# Категории расходов
EXPENSE_CATEGORIES = [
    "Продукты",
    "Кафе",
    "Транспорт",
    "Такси",
    "Досуг",
    "Покупки",
    "Здоровье и красота",
    "Аптека",
    "Ништяки",
    "Аренда",
    "Коммуналка",
    "Интернет и связь",
    "Кошки",
    "Долги",
    "Одежда",
    "Подарки"
]

# Валюты
CURRENCIES = ["BYN", "USD", "EUR", "RUB"]

# Структура колонок листа "Транзакции"
TRANSACTIONS_COLUMNS = [
    "День",           # A - день месяца (1-31)
    "Тип",            # B - Доход/Расход/Перевод/Обмен валюты
    "Счёт",           # C - счет списания
    "Категория",      # D - категория транзакции
    "Сумма",          # E - сумма в исходной валюте
    "Счёт Куда",      # F - счет зачисления
    "Комментарий",    # G - комментарий
    "Полная дата",    # H - формула для полной даты
    "Часы",           # I - часы работы (для чаевых)
    "Часы×6.5",       # J - формула расчета по ставке
    "Курс",           # K - курс обмена валюты
    "Сумма BYN",      # L - эквивалент в BYN / сумма зачисления
    "Валюта"          # M - валюта операции
]

# Структура колонок листа "Счета"
ACCOUNTS_COLUMNS = [
    "Название",       # A - название счета
    "Начальный",      # B - начальный баланс
    "Текущий",        # C - текущий баланс (формула)
    "Валюта"          # D - валюта счета
]

# Структура колонок листа "Категории"
CATEGORIES_COLUMNS = [
    "Тип",            # A - Доход/Расход
    "Категория",      # B - название категории
    "Бюджет",         # C - плановый бюджет
    "Потрачено",      # D - потрачено (формула)
    "Остаток",        # E - остаток (формула)
    "Прогресс"        # F - прогресс % (формула)
]


def connect_to_sheets():
    """Подключение к Google Sheets"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        config.GOOGLE_CREDENTIALS_FILE, scope
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(config.GOOGLE_SHEETS_ID)
    print(f"OK: Подключено к таблице: {spreadsheet.title}")
    return spreadsheet


def check_and_update_references(spreadsheet):
    """Проверка и обновление справочников"""
    print("\n" + "="*50)
    print("ЛИСТ 'Справочники'")
    print("="*50)

    sheet = spreadsheet.worksheet(config.SHEET_REFERENCES)
    data = sheet.get_all_values()

    # Извлекаем текущие данные (начиная с 4-й строки)
    current_types = []
    current_accounts = []
    current_categories = []

    for row in data[3:]:
        if len(row) > 0 and row[0].strip():
            current_types.append(row[0].strip())
        if len(row) > 1 and row[1].strip():
            current_accounts.append(row[1].strip())
        if len(row) > 2 and row[2].strip():
            current_categories.append(row[2].strip())

    print(f"\nТекущие типы: {current_types}")
    print(f"Текущие счета: {current_accounts}")
    print(f"Текущие категории: {current_categories}")

    # Проверяем типы транзакций
    missing_types = [t for t in REQUIRED_TYPES if t not in current_types]
    if missing_types:
        print(f"\nОТСУТСТВУЮТ типы: {missing_types}")
        add_to_column(sheet, data, 0, missing_types, "типы")
    else:
        print("\nOK: Все типы транзакций присутствуют")

    # Проверяем категории
    all_categories = INCOME_CATEGORIES + EXPENSE_CATEGORIES
    missing_categories = [c for c in all_categories if c not in current_categories]
    if missing_categories:
        print(f"\nОТСУТСТВУЮТ категории: {missing_categories}")
        add_to_column(sheet, data, 2, missing_categories, "категории")
    else:
        print("\nOK: Все категории присутствуют")


def add_to_column(sheet, data, col_idx, values, name):
    """Добавить значения в колонку справочников"""
    # Находим последнюю заполненную строку в колонке
    last_row = 3  # Начинаем с 4-й строки (индекс 3)
    for i, row in enumerate(data[3:], start=4):
        if len(row) > col_idx and row[col_idx].strip():
            last_row = i

    # Добавляем недостающие значения
    for i, value in enumerate(values):
        row_num = last_row + 1 + i
        sheet.update_cell(row_num, col_idx + 1, value)
        print(f"   Добавлено '{value}' в строку {row_num}")


def check_and_update_categories(spreadsheet):
    """Проверка и обновление листа категорий"""
    print("\n" + "="*50)
    print("ЛИСТ 'Категории'")
    print("="*50)

    sheet = spreadsheet.worksheet(config.SHEET_CATEGORIES)
    data = sheet.get_all_values()

    # Проверяем заголовки
    if len(data) > 0:
        headers = data[0]
        print(f"\nТекущие заголовки: {headers}")

        # Проверяем соответствие заголовков
        for i, expected in enumerate(CATEGORIES_COLUMNS):
            if i < len(headers):
                if headers[i] != expected:
                    print(f"   Колонка {chr(65+i)}: '{headers[i]}' -> '{expected}'")
            else:
                print(f"   Колонка {chr(65+i)}: ОТСУТСТВУЕТ -> '{expected}'")

    # Извлекаем существующие категории
    existing_categories = {}
    for row in data[1:]:
        if len(row) > 1 and row[1].strip():
            cat_type = row[0].strip() if row[0] else ""
            cat_name = row[1].strip()
            existing_categories[cat_name] = cat_type

    print(f"\nСуществующие категории: {list(existing_categories.keys())}")

    # Проверяем категории доходов
    for cat in INCOME_CATEGORIES:
        if cat not in existing_categories:
            print(f"   ОТСУТСТВУЕТ категория дохода: {cat}")
        elif existing_categories[cat] != "Доход":
            print(f"   НЕВЕРНЫЙ тип для '{cat}': {existing_categories[cat]} -> Доход")

    # Проверяем категории расходов
    for cat in EXPENSE_CATEGORIES:
        if cat not in existing_categories:
            print(f"   ОТСУТСТВУЕТ категория расхода: {cat}")
        elif existing_categories[cat] != "Расход":
            print(f"   НЕВЕРНЫЙ тип для '{cat}': {existing_categories[cat]} -> Расход")


def check_transactions_structure(spreadsheet):
    """Проверка структуры листа транзакций"""
    print("\n" + "="*50)
    print("ЛИСТ 'Транзакции'")
    print("="*50)

    sheet = spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
    data = sheet.get_all_values()

    # Строка 1 - настройки месяца/года
    if len(data) > 0:
        print(f"\nНастройки (строка 1): {data[0][:6]}")
        print(f"   Месяц (C1): {data[0][2] if len(data[0]) > 2 else 'НЕ ЗАДАН'}")
        print(f"   Год (E1): {data[0][4] if len(data[0]) > 4 else 'НЕ ЗАДАН'}")

    # Строка 3 - заголовки данных (обычно)
    headers_row = 2  # Индекс строки с заголовками (0-based)
    if len(data) > headers_row:
        headers = data[headers_row]
        print(f"\nЗаголовки (строка 3): {headers}")

        print("\nСоответствие колонок:")
        for i, expected in enumerate(TRANSACTIONS_COLUMNS):
            actual = headers[i] if i < len(headers) else "ОТСУТСТВУЕТ"
            status = "OK" if actual == expected else "НЕСООТВЕТСТВИЕ"
            print(f"   {chr(65+i)}: {actual:15} | Ожидается: {expected:15} | {status}")

    # Проверяем данные транзакций
    transactions_count = len(data) - 3  # Минус 3 строки настроек/заголовков
    print(f"\nВсего транзакций: {transactions_count}")

    # Проверяем использование новых колонок (Валюта, Курс)
    has_currency = False
    has_exchange_rate = False

    for row in data[3:]:
        if len(row) > 12 and row[12].strip():  # Колонка M - валюта
            has_currency = True
        if len(row) > 10 and row[10].strip():  # Колонка K - курс
            has_exchange_rate = True

    print(f"\nИспользование мультивалютности:")
    print(f"   Колонка 'Валюта' (M): {'Используется' if has_currency else 'Пуста'}")
    print(f"   Колонка 'Курс' (K): {'Используется' if has_exchange_rate else 'Пуста'}")


def check_accounts_structure(spreadsheet):
    """Проверка структуры листа счетов"""
    print("\n" + "="*50)
    print("ЛИСТ 'Счета'")
    print("="*50)

    sheet = spreadsheet.worksheet(config.SHEET_ACCOUNTS)
    data = sheet.get_all_values()

    # Проверяем заголовки (строка 3)
    if len(data) > 2:
        headers = data[2]
        print(f"\nЗаголовки (строка 3): {headers}")

        print("\nСоответствие колонок:")
        for i, expected in enumerate(ACCOUNTS_COLUMNS):
            actual = headers[i] if i < len(headers) else "ОТСУТСТВУЕТ"
            status = "OK" if actual == expected else "НЕСООТВЕТСТВИЕ"
            print(f"   {chr(65+i)}: {actual:15} | Ожидается: {expected:15} | {status}")

    # Список счетов
    print("\nСчета:")
    for row in data[3:]:
        if len(row) > 0 and row[0].strip():
            name = row[0]
            currency = row[3] if len(row) > 3 and row[3] else "BYN"
            current = row[2] if len(row) > 2 else "?"
            print(f"   {name}: {current} {currency}")


def generate_update_recommendations(spreadsheet):
    """Генерация рекомендаций по обновлению"""
    print("\n" + "="*50)
    print("РЕКОМЕНДАЦИИ ПО ОБНОВЛЕНИЮ")
    print("="*50)

    recommendations = []

    # Проверяем справочники
    sheet = spreadsheet.worksheet(config.SHEET_REFERENCES)
    data = sheet.get_all_values()

    current_types = [row[0].strip() for row in data[3:] if len(row) > 0 and row[0].strip()]
    current_categories = [row[2].strip() for row in data[3:] if len(row) > 2 and row[2].strip()]

    missing_types = [t for t in REQUIRED_TYPES if t not in current_types]
    if missing_types:
        recommendations.append(f"Добавить типы в справочник: {missing_types}")

    all_categories = INCOME_CATEGORIES + EXPENSE_CATEGORIES
    missing_categories = [c for c in all_categories if c not in current_categories]
    if missing_categories:
        recommendations.append(f"Добавить категории в справочник: {missing_categories}")

    # Проверяем лист категорий
    cat_sheet = spreadsheet.worksheet(config.SHEET_CATEGORIES)
    cat_data = cat_sheet.get_all_values()

    existing_cat_names = [row[1].strip() for row in cat_data[1:] if len(row) > 1 and row[1].strip()]

    for cat in INCOME_CATEGORIES:
        if cat not in existing_cat_names:
            recommendations.append(f"Добавить категорию дохода '{cat}' в лист Категории")

    for cat in EXPENSE_CATEGORIES:
        if cat not in existing_cat_names:
            recommendations.append(f"Добавить категорию расхода '{cat}' в лист Категории")

    # Проверяем колонку валюты в счетах
    acc_sheet = spreadsheet.worksheet(config.SHEET_ACCOUNTS)
    acc_data = acc_sheet.get_all_values()

    if len(acc_data) > 2:
        headers = acc_data[2]
        if len(headers) < 4 or headers[3] != "Валюта":
            recommendations.append("Добавить колонку 'Валюта' (D) в лист Счета")

    if recommendations:
        print("\nНеобходимые изменения:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("\nТаблица полностью соответствует функционалу бота!")

    return recommendations


def apply_updates(spreadsheet, auto_apply=True):
    """Применить обновления к таблице"""
    print("\n" + "="*50)
    print("ПРИМЕНЕНИЕ ОБНОВЛЕНИЙ")
    print("="*50)

    # 1. Обновляем справочники
    print("\n1. Обновление справочников...")
    refs_sheet = spreadsheet.worksheet(config.SHEET_REFERENCES)
    refs_data = refs_sheet.get_all_values()

    current_types = [row[0].strip() for row in refs_data[3:] if len(row) > 0 and row[0].strip()]
    current_categories = [row[2].strip() for row in refs_data[3:] if len(row) > 2 and row[2].strip()]

    # Добавляем недостающие типы
    for t in REQUIRED_TYPES:
        if t not in current_types:
            add_to_column(refs_sheet, refs_data, 0, [t], "тип")
            refs_data = refs_sheet.get_all_values()  # Обновляем данные

    # Добавляем недостающие категории
    all_categories = INCOME_CATEGORIES + EXPENSE_CATEGORIES
    for c in all_categories:
        if c not in current_categories:
            add_to_column(refs_sheet, refs_data, 2, [c], "категория")
            refs_data = refs_sheet.get_all_values()

    # 2. Обновляем лист категорий
    print("\n2. Обновление листа категорий...")
    cat_sheet = spreadsheet.worksheet(config.SHEET_CATEGORIES)
    cat_data = cat_sheet.get_all_values()

    existing_cats = {row[1].strip(): row[0].strip() for row in cat_data[1:] if len(row) > 1 and row[1].strip()}

    # Находим последнюю строку
    last_row = len(cat_data)

    # Добавляем недостающие категории доходов
    for cat in INCOME_CATEGORIES:
        if cat not in existing_cats:
            last_row += 1
            cat_sheet.update(f"A{last_row}:C{last_row}", [["Доход", cat, 0]], value_input_option='USER_ENTERED')
            print(f"   Добавлена категория дохода: {cat}")

    # Добавляем недостающие категории расходов
    for cat in EXPENSE_CATEGORIES:
        if cat not in existing_cats:
            last_row += 1
            cat_sheet.update(f"A{last_row}:C{last_row}", [["Расход", cat, 0]], value_input_option='USER_ENTERED')
            print(f"   Добавлена категория расхода: {cat}")

    print("\nOK: Обновления применены!")


def main():
    """Главная функция"""
    print("="*50)
    print("СИНХРОНИЗАЦИЯ GOOGLE SHEETS С БОТОМ")
    print("="*50)

    try:
        spreadsheet = connect_to_sheets()

        # Проверяем все листы
        check_transactions_structure(spreadsheet)
        check_accounts_structure(spreadsheet)
        check_and_update_categories(spreadsheet)
        check_and_update_references(spreadsheet)

        # Генерируем рекомендации
        recommendations = generate_update_recommendations(spreadsheet)

        # Предлагаем применить обновления
        if recommendations:
            apply_updates(spreadsheet)

    except Exception as e:
        print(f"\nОШИБКА: {e}")
        raise


if __name__ == "__main__":
    main()
