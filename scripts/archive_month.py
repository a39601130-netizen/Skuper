#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт архивации месяца.

Выполняет:
1. Создаёт лист "Архив" (если не существует)
2. Копирует все транзакции текущего месяца в Архив
3. Очищает лист Транзакции (оставляя настройки и заголовки)
4. Обновляет месяц в настройках на следующий

Запуск: python scripts/archive_month.py
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from google.oauth2.service_account import Credentials
import config


ARCHIVE_SHEET_NAME = "Архив"


def connect_to_sheets():
    """Подключение к Google Sheets"""
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(
        config.GOOGLE_CREDENTIALS_FILE, scopes=scopes
    )
    client = gspread.authorize(creds)
    return client.open_by_key(config.GOOGLE_SHEETS_ID)


def get_or_create_archive_sheet(spreadsheet):
    """Получить или создать лист Архив"""
    try:
        archive = spreadsheet.worksheet(ARCHIVE_SHEET_NAME)
        print(f"[OK] Лист '{ARCHIVE_SHEET_NAME}' найден")
        return archive
    except gspread.exceptions.WorksheetNotFound:
        print(f"Создаю лист '{ARCHIVE_SHEET_NAME}'...")

        # Получаем структуру из листа Транзакции
        transactions = spreadsheet.worksheet(config.SHEET_TRANSACTIONS)

        # Создаём новый лист
        archive = spreadsheet.add_worksheet(
            title=ARCHIVE_SHEET_NAME,
            rows=1000,
            cols=15
        )

        # Копируем заголовки (строка 3)
        headers = transactions.row_values(3)
        if headers:
            archive.update('A1', [headers])

        print(f"[OK] Лист '{ARCHIVE_SHEET_NAME}' создан с заголовками")
        return archive


def archive_current_month(spreadsheet):
    """Архивировать текущий месяц"""
    transactions = spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
    data = transactions.get_all_values()

    if len(data) < 4:
        print("[ERROR] Нет данных для архивации")
        return False

    # Читаем настройки
    try:
        month = int(data[0][2]) if data[0][2] else 1
        year = int(data[0][4]) if data[0][4] else 2026
    except (ValueError, IndexError):
        print("[ERROR] Не удалось прочитать месяц/год")
        return False

    print(f"Архивирую: {month:02d}.{year}")

    # Получаем транзакции (строки 4+)
    transactions_data = data[3:]

    # Фильтруем пустые строки
    valid_rows = [row for row in transactions_data if row[0] and row[0].strip()]

    if not valid_rows:
        print("[WARN] Нет транзакций для архивации")
        return False

    print(f"Найдено {len(valid_rows)} транзакций")

    # Получаем или создаём лист Архив
    archive = get_or_create_archive_sheet(spreadsheet)

    # Добавляем метку месяца к каждой строке (в колонку H если пустая)
    month_label = f"{month:02d}.{year}"
    for row in valid_rows:
        # Если колонка H пустая, заполняем полной датой
        if len(row) > 7 and not row[7]:
            try:
                day = int(row[0])
                row[7] = f"{day:02d}.{month:02d}.{year}"
            except ValueError:
                pass

    # Находим последнюю заполненную строку в архиве
    archive_data = archive.get_all_values()
    next_row = len(archive_data) + 1

    # Добавляем транзакции в архив
    if valid_rows:
        # Batch update для эффективности
        cell_range = f"A{next_row}:M{next_row + len(valid_rows) - 1}"
        archive.update(cell_range, valid_rows)
        print(f"[OK] Добавлено {len(valid_rows)} строк в архив (строки {next_row}-{next_row + len(valid_rows) - 1})")

    return True


def clear_transactions(spreadsheet):
    """Очистить транзакции (оставить настройки и заголовки)"""
    transactions = spreadsheet.worksheet(config.SHEET_TRANSACTIONS)

    # Получаем количество строк
    data = transactions.get_all_values()
    total_rows = len(data)

    if total_rows <= 3:
        print("[OK] Транзакции уже пусты")
        return True

    # Очищаем строки 4 и далее
    # Формируем диапазон для очистки
    clear_range = f"A4:M{total_rows}"

    # Создаём пустые строки
    empty_rows = [[""] * 13 for _ in range(total_rows - 3)]

    transactions.update(clear_range, empty_rows)
    print(f"[OK] Очищено {total_rows - 3} строк транзакций")

    return True


def update_month_settings(spreadsheet, new_month, new_year):
    """Обновить месяц и год в настройках"""
    transactions = spreadsheet.worksheet(config.SHEET_TRANSACTIONS)

    # C1 = месяц, E1 = год
    transactions.update_acell('C1', new_month)
    transactions.update_acell('E1', new_year)

    print(f"[OK] Установлен период: {new_month:02d}.{new_year}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Архивация месяца')
    parser.add_argument('--yes', '-y', action='store_true', help='Автоматическое подтверждение')
    parser.add_argument('--no-clear', action='store_true', help='Не очищать транзакции после архивации')
    args = parser.parse_args()

    print("=" * 50)
    print("Архивация месяца")
    print("=" * 50)

    try:
        spreadsheet = connect_to_sheets()
        print(f"[OK] Подключено к: {spreadsheet.title}")
    except Exception as e:
        print(f"[ERROR] Ошибка подключения: {e}")
        return

    # Читаем текущий месяц
    transactions = spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
    data = transactions.get_all_values()

    try:
        current_month = int(data[0][2]) if data[0][2] else 1
        current_year = int(data[0][4]) if data[0][4] else 2026
    except (ValueError, IndexError):
        print("[ERROR] Не удалось прочитать текущий месяц/год")
        return

    # Вычисляем следующий месяц
    if current_month == 12:
        next_month = 1
        next_year = current_year + 1
    else:
        next_month = current_month + 1
        next_year = current_year

    # Считаем транзакции
    transactions_count = len([r for r in data[3:] if r[0] and r[0].strip()])

    print(f"\nТекущий период: {current_month:02d}.{current_year}")
    print(f"Транзакций: {transactions_count}")
    print(f"Следующий период: {next_month:02d}.{next_year}")

    print("\nЭтот скрипт:")
    print(f"  1. Скопирует {transactions_count} транзакций в лист 'Архив'")
    if not args.no_clear:
        print("  2. Очистит лист Транзакции")
        print(f"  3. Установит новый период: {next_month:02d}.{next_year}")

    if not args.yes:
        confirm = input("\nПродолжить? (да/нет): ").strip().lower()
        if confirm not in ["да", "yes", "y", "д"]:
            print("Отменено")
            return

    # Выполняем
    print("\n" + "-" * 50)

    if not archive_current_month(spreadsheet):
        print("[ERROR] Ошибка архивации")
        return

    if not args.no_clear:
        clear_transactions(spreadsheet)
        update_month_settings(spreadsheet, next_month, next_year)

    print("\n" + "=" * 50)
    print("ГОТОВО!")
    print("=" * 50)
    print(f"""
Транзакции за {current_month:02d}.{current_year} сохранены в листе 'Архив'.
{"Лист Транзакции очищен." if not args.no_clear else ""}
{"Новый период: " + f"{next_month:02d}.{next_year}" if not args.no_clear else ""}

Можешь продолжать добавлять транзакции через бота.
""")


if __name__ == "__main__":
    main()
