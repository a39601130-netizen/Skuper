"""
Скрипт для обновления категорий в Google Sheets
Заменяет "Зарплата/Чаевые" на две отдельные категории
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config

def update_categories():
    # Подключение к Google Sheets
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

    print("OK: Подключено к Google Sheets")

    # 1. Обновляем лист "Справочники"
    print("\nОбновление листа 'Справочники'...")
    refs_sheet = spreadsheet.worksheet(config.SHEET_REFERENCES)
    data = refs_sheet.get_all_values()

    # Ищем "Зарплата/Чаевые" в колонке категорий (C)
    found_row = None
    for i, row in enumerate(data[3:], start=4):  # Пропускаем заголовки
        if len(row) > 2 and row[2] == "Зарплата/Чаевые":
            found_row = i
            print(f"   Найдена строка {found_row}: Зарплата/Чаевые")
            break

    if found_row:
        # Заменяем на "Зарплата"
        refs_sheet.update_cell(found_row, 3, "Зарплата")
        print(f"   OK: Строка {found_row} обновлена на 'Зарплата'")

        # Ищем первую пустую строку для добавления "Чаевые"
        empty_row = None
        for i, row in enumerate(data[3:], start=4):
            if len(row) <= 2 or not row[2].strip():
                empty_row = i
                break

        if not empty_row:
            empty_row = len(data) + 1

        refs_sheet.update_cell(empty_row, 3, "Чаевые")
        print(f"   OK: Добавлена 'Чаевые' в строку {empty_row}")
    else:
        print("   WARNING:  'Зарплата/Чаевые' не найдена в справочниках")

    # 2. Обновляем лист "Категории"
    print("\nОбновление листа 'Категории'...")
    cat_sheet = spreadsheet.worksheet(config.SHEET_CATEGORIES)
    cat_data = cat_sheet.get_all_values()

    # Ищем "Зарплата/Чаевые" в категориях (колонка B)
    found_cat_row = None
    for i, row in enumerate(cat_data[1:], start=2):  # Пропускаем заголовок
        if len(row) > 1 and row[1] == "Зарплата/Чаевые":
            found_cat_row = i
            old_budget = row[2] if len(row) > 2 else ""
            print(f"   Найдена строка {found_cat_row}: Зарплата/Чаевые (бюджет: {old_budget})")
            break

    if found_cat_row:
        # Заменяем на "Зарплата"
        cat_sheet.update_cell(found_cat_row, 2, "Зарплата")
        print(f"   OK: Строка {found_cat_row} обновлена на 'Зарплата'")

        # Находим первую пустую строку для "Чаевые"
        empty_cat_row = None
        for i, row in enumerate(cat_data[1:], start=2):
            if len(row) <= 1 or not row[1].strip():
                empty_cat_row = i
                break

        if not empty_cat_row:
            empty_cat_row = len(cat_data) + 1

        # Добавляем "Чаевые" с тем же типом "Доход" и бюджетом 0
        cat_sheet.update_cell(empty_cat_row, 1, "Доход")  # Тип
        cat_sheet.update_cell(empty_cat_row, 2, "Чаевые")  # Название
        cat_sheet.update_cell(empty_cat_row, 3, 0)  # Бюджет
        print(f"   OK: Добавлена 'Чаевые' в строку {empty_cat_row}")
    else:
        print("   WARNING:  'Зарплата/Чаевые' не найдена в категориях")

    print("\nOK: Обновление завершено!")

if __name__ == "__main__":
    update_categories()
