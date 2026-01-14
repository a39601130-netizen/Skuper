"""
Сервис для работы с Google Sheets
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import Optional, Dict, List, Any
from functools import wraps
import time
import logging
import config

logger = logging.getLogger(__name__)


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Декоратор для повторных попыток при ошибках API"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except gspread.exceptions.APIError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (attempt + 1)
                        logger.warning(f"API error in {func.__name__}, retry {attempt + 1}/{max_retries} in {wait_time}s: {e}")
                        time.sleep(wait_time)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Error in {func.__name__}, retry {attempt + 1}/{max_retries}: {e}")
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def safe_float(value, default=0.0) -> float:
    """
    Безопасное преобразование строки в float.
    Обрабатывает европейский формат с запятой (140,82)
    """
    if value is None or value == "" or value == "-":
        return default
    
    if isinstance(value, (int, float)):
        return float(value)
    
    try:
        # Убираем пробелы и заменяем запятую на точку
        cleaned = str(value).strip().replace(" ", "").replace(",", ".")
        return float(cleaned)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0) -> int:
    """Безопасное преобразование в int"""
    if value is None or value == "":
        return default

    try:
        # Сначала преобразуем в float (на случай "1,0"), потом в int
        return int(safe_float(value, default))
    except (ValueError, TypeError):
        return default


class BaseSheetsService:
    """Базовый класс для работы с Google Sheets"""

    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        self._last_connect = 0
        self._connect()

    def _connect(self):
        """Подключение к Google Sheets"""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                config.GOOGLE_CREDENTIALS_FILE, scope
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            self._last_connect = time.time()
            logger.info(f"Connected to Google Sheets: {self.spreadsheet_id}")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise

    def _ensure_connection(self):
        """Переподключение если соединение устарело (>30 мин)"""
        if time.time() - self._last_connect > 1800:
            logger.info("Reconnecting to Google Sheets (connection expired)")
            self._connect()

    def get_sheet(self, sheet_name: str) -> gspread.Worksheet:
        """Получить лист по имени"""
        self._ensure_connection()
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            logger.error(f"Sheet not found: {sheet_name}")
            raise

    def get_all_records(self, sheet_name: str) -> List[Dict]:
        """Получить все записи с листа как список словарей"""
        sheet = self.get_sheet(sheet_name)
        return sheet.get_all_records()

    def append_row(self, sheet_name: str, row: List[Any]) -> int:
        """Добавить строку в конец листа, вернуть номер строки"""
        sheet = self.get_sheet(sheet_name)
        sheet.append_row(row, value_input_option='USER_ENTERED')
        return len(sheet.get_all_values())

    def update_cell(self, sheet_name: str, row: int, col: int, value: Any):
        """Обновить конкретную ячейку"""
        sheet = self.get_sheet(sheet_name)
        sheet.update_cell(row, col, value)

    def update_row(self, sheet_name: str, row_num: int, values: List[Any]):
        """Обновить целую строку"""
        sheet = self.get_sheet(sheet_name)
        end_col = gspread.utils.rowcol_to_a1(1, len(values))[0]
        range_str = f"A{row_num}:{end_col}{row_num}"
        sheet.update(range_str, [values], value_input_option='USER_ENTERED')

    def find_row_by_value(self, sheet_name: str, column: int, value: Any) -> Optional[int]:
        """Найти номер строки по значению в колонке"""
        sheet = self.get_sheet(sheet_name)
        try:
            cell = sheet.find(str(value), in_column=column)
            return cell.row if cell else None
        except gspread.CellNotFound:
            return None

    def get_last_row_number(self, sheet_name: str) -> int:
        """Получить номер последней непустой строки"""
        sheet = self.get_sheet(sheet_name)
        values = sheet.get_all_values()
        return len(values)

    def batch_update(self, sheet_name: str, updates: List[Dict[str, Any]]):
        """
        Пакетное обновление ячеек

        Args:
            sheet_name: Имя листа
            updates: Список словарей вида [{'range': 'A1', 'value': 123}, ...]
        """
        if not updates:
            return

        sheet = self.get_sheet(sheet_name)

        # Формируем данные для batch_update
        data = []
        for upd in updates:
            range_name = upd['range']
            value = upd['value']
            data.append({
                'range': range_name,
                'values': [[value]]
            })

        # Выполняем batch update
        sheet.batch_update(data, value_input_option='USER_ENTERED')

    def delete_row(self, sheet_name: str, row_num: int):
        """Удалить строку по номеру"""
        sheet = self.get_sheet(sheet_name)
        sheet.delete_rows(row_num)


class GoogleSheetsService:
    """Сервис для работы с Google Sheets таблицей бюджета"""

    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self._last_connect = 0
        # Кэш для справочников (уменьшает запросы к API)
        self._references_cache = None
        self._references_cache_time = 0
        self._cache_ttl = 300  # 5 минут
        self._connect()

    def _connect(self):
        """Подключение к Google Sheets"""
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            config.GOOGLE_CREDENTIALS_FILE, scope
        )
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(config.GOOGLE_SHEETS_ID)
        self._last_connect = time.time()

    def _ensure_connection(self):
        """Переподключение если соединение устарело (>30 мин)"""
        if time.time() - self._last_connect > 1800:
            logger.info("Reconnecting to Google Sheets (connection expired)")
            self._connect()
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_references(self, force_refresh: bool = False) -> Dict[str, List[str]]:
        """
        Получить справочники (типы, счета, категории)

        Args:
            force_refresh: Принудительное обновление кэша
        """
        # Проверяем кэш
        if not force_refresh and self._references_cache:
            if time.time() - self._references_cache_time < self._cache_ttl:
                return self._references_cache

        self._ensure_connection()
        sheet = self.spreadsheet.worksheet(config.SHEET_REFERENCES)
        data = sheet.get_all_values()

        # Парсим данные начиная с 4-й строки (индекс 3)
        types = []
        accounts = []
        categories = []

        for row in data[3:]:  # Пропускаем заголовки
            if row[0] and row[0].strip():
                types.append(row[0].strip())
            if row[1] and row[1].strip():
                accounts.append(row[1].strip())
            if row[2] and row[2].strip():
                categories.append(row[2].strip())

        # Сохраняем в кэш
        self._references_cache = {
            "types": types,
            "accounts": accounts,
            "categories": categories
        }
        self._references_cache_time = time.time()

        return self._references_cache

    @retry_on_error(max_retries=3, delay=1.0)
    def ensure_exchange_type_exists(self) -> bool:
        """Добавить тип 'Обмен валюты' в справочник если его нет"""
        try:
            self._ensure_connection()
            refs = self.get_references()

            if "Обмен валюты" in refs["types"]:
                return True  # Уже есть

            # Находим первую пустую ячейку в колонке A после заголовков
            sheet = self.spreadsheet.worksheet(config.SHEET_REFERENCES)
            data = sheet.get_all_values()

            # Ищем первую пустую строку в колонке типов (A)
            row_to_insert = 4  # Начинаем с 4-й строки
            for i, row in enumerate(data[3:], start=4):
                if not row[0] or not row[0].strip():
                    row_to_insert = i
                    break
                row_to_insert = i + 1

            # Добавляем тип
            sheet.update_cell(row_to_insert, 1, "Обмен валюты")
            logger.info(f"Добавлен тип 'Обмен валюты' в справочник (строка {row_to_insert})")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления типа в справочник: {e}")
            return False

    @retry_on_error(max_retries=3, delay=1.0)
    def get_accounts_balance(self) -> List[Dict[str, Any]]:
        """Получить балансы всех счетов"""
        self._ensure_connection()
        sheet = self.spreadsheet.worksheet(config.SHEET_ACCOUNTS)
        data = sheet.get_all_values()
        
        accounts = []
        for row in data[3:]:  # Пропускаем заголовки
            if row[0] and row[0].strip():
                accounts.append({
                    "name": row[0].strip(),
                    "initial": safe_float(row[1]) if row[1] else 0,
                    "current": safe_float(row[2]) if row[2] else 0,
                    "currency": row[3] if len(row) > 3 and row[3] else "BYN"
                })
        
        return accounts
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_categories_budget(self) -> List[Dict[str, Any]]:
        """Получить бюджеты и расходы по категориям"""
        self._ensure_connection()
        sheet = self.spreadsheet.worksheet(config.SHEET_CATEGORIES)
        data = sheet.get_all_values()
        
        categories = []
        for row in data[1:]:  # Пропускаем заголовок
            if row[1] and row[1].strip():
                categories.append({
                    "type": row[0].strip(),
                    "name": row[1].strip(),
                    "budget": safe_float(row[2]) if row[2] else 0,
                    "spent": safe_float(row[3]) if row[3] else 0,
                    "remaining": safe_float(row[4]) if row[4] else 0,
                    "progress": safe_float(row[5]) if row[5] else 0
                })
        
        return categories
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_current_month_settings(self) -> Dict[str, int]:
        """Получить текущий месяц и год из настроек таблицы"""
        self._ensure_connection()
        sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        data = sheet.get_all_values()
        
        # Настройки в первой строке: C1 = месяц, E1 = год
        month = safe_int(data[0][2], datetime.now().month)
        year = safe_int(data[0][4], datetime.now().year)
        
        return {"month": month, "year": year}
    
    @retry_on_error(max_retries=3, delay=1.0)
    def add_transaction(
        self,
        day: int,
        trans_type: str,
        account: str,
        category: Optional[str],
        amount: float,
        to_account: Optional[str] = None,
        comment: Optional[str] = None,
        hours: Optional[float] = None,
        exchange_rate: Optional[float] = None,
        amount_to: Optional[float] = None,
        currency: str = "BYN"
    ) -> bool:
        """
        Добавить транзакцию в таблицу

        Args:
            day: День месяца (1-31)
            trans_type: Тип (Доход, Расход, Перевод, Обмен валюты)
            account: Счёт списания
            category: Категория (для Доходов и Расходов)
            amount: Сумма списания
            to_account: Счёт зачисления (для Переводов и Обмена)
            comment: Комментарий
            hours: Количество часов (для расчета зарплаты)
            exchange_rate: Курс обмена (для валютных операций)
            amount_to: Сумма зачисления (для обмена валюты)
            currency: Валюта операции (BYN, USD, EUR, RUB)

        Returns:
            bool: Успех операции
        """
        try:
            self._ensure_connection()
            sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)

            # Формируем строку данных
            # A: Дата, B: Тип, C: Счёт, D: Категория, E: Сумма,
            # F: Счёт Куда, G: Комментарий, H: (формула), I: Часы, J: Часы×6.5
            # K: Курс, L: Сумма зачисления, M: Валюта
            row_data = [
                day,                           # A: Дата (день)
                trans_type,                    # B: Тип
                account,                       # C: Счёт
                category or "",                # D: Категория
                amount,                        # E: Сумма
                to_account or "",              # F: Счёт Куда
                comment or "",                 # G: Комментарий
                "",                            # H: Полная дата (формула в таблице)
                hours if hours else "",        # I: Часы
                "",                            # J: Часы×6.5 (формула)
                exchange_rate if exchange_rate else "",  # K: Курс
                amount_to if amount_to else "",          # L: Сумма зачисления
                currency                                  # M: Валюта
            ]

            # Добавляем в конец таблицы
            sheet.append_row(row_data, value_input_option='USER_ENTERED')

            return True

        except Exception as e:
            print(f"Ошибка записи в Google Sheets: {e}")
            return False
    
    def get_monthly_summary(self) -> Dict[str, Any]:
        """Получить сводку за текущий месяц"""
        categories = self.get_categories_budget()
        accounts = self.get_accounts_balance()

        # Считаем доходы напрямую из листа "Транзакции"
        # так как формулы в листе "Категории" могут не работать
        self._ensure_connection()
        sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        data = sheet.get_all_values()

        total_income = 0.0
        income_by_category = {}

        # Проходим по всем транзакциям (пропускаем первые 3 строки - настройки и заголовки)
        for row in data[3:]:
            if row[0] and row[0].strip() and len(row) > 4:
                trans_type = row[1].strip() if row[1] else ""
                category = row[3].strip() if len(row) > 3 and row[3] else ""
                amount_str = row[4].strip() if row[4] else "0"

                # Подсчитываем только доходы
                if trans_type == "Доход":
                    try:
                        amount = float(amount_str.replace(",", ".").replace(" ", ""))
                        total_income += amount

                        # Группируем по категориям
                        if category:
                            income_by_category[category] = income_by_category.get(category, 0.0) + amount
                    except (ValueError, AttributeError):
                        continue

        logger.info(f"Total income from transactions: {total_income}")
        logger.info(f"Income by category: {income_by_category}")

        # Расходы берем из категорий (там формулы работают)
        total_expense = sum(c["spent"] for c in categories if c["type"] == "Расход")
        total_balance = sum(a["current"] for a in accounts if a["currency"] == "BYN")

        # Обновляем категории доходов с реальными данными из транзакций
        for cat in categories:
            if cat["type"] == "Доход":
                cat["spent"] = income_by_category.get(cat["name"], 0.0)

        # Категории с превышением бюджета
        over_budget = [
            c for c in categories 
            if c["type"] == "Расход" and c["budget"] > 0 and c["spent"] > c["budget"]
        ]
        
        # Категории близкие к лимиту (>80%)
        near_limit = [
            c for c in categories 
            if c["type"] == "Расход" and c["budget"] > 0 
            and c["progress"] >= 0.8 and c["progress"] < 1
        ]
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "total_on_accounts": total_balance,
            "accounts": accounts,
            "categories": categories,
            "over_budget": over_budget,
            "near_limit": near_limit
        }
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить последние транзакции"""
        self._ensure_connection()
        sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        data = sheet.get_all_values()

        transactions = []
        for idx, row in enumerate(data[3:], start=4):  # Пропускаем настройки и заголовки, начинаем с 4-й строки
            if row[0] and row[0].strip():
                transactions.append({
                    "row_index": idx,  # Номер строки в таблице (1-based)
                    "day": row[0],
                    "type": row[1],
                    "account": row[2],
                    "category": row[3],
                    "amount": row[4],
                    "to_account": row[5],
                    "comment": row[6],
                    "full_date": row[7] if len(row) > 7 else "",
                    "hours": row[8] if len(row) > 8 else "",
                    "exchange_rate": row[10] if len(row) > 10 else "",
                    "amount_to": row[11] if len(row) > 11 else "",
                    "currency": row[12] if len(row) > 12 else "BYN"
                })

        return transactions[-limit:][::-1]  # Последние N, в обратном порядке

    @retry_on_error(max_retries=3, delay=1.0)
    def delete_transaction(self, row_index: int) -> bool:
        """
        Удалить транзакцию из таблицы

        Args:
            row_index: Номер строки в таблице (1-based)

        Returns:
            bool: Успех операции
        """
        try:
            self._ensure_connection()
            sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
            sheet.delete_rows(row_index)
            return True

        except Exception as e:
            print(f"Ошибка удаления транзакции: {e}")
            return False

    @retry_on_error(max_retries=3, delay=1.0)
    def get_income_by_days(self) -> Dict[str, Any]:
        """Получить доходы по дням с детализацией"""
        self._ensure_connection()
        sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        data = sheet.get_all_values()

        # Группируем доходы по дням
        income_by_day = {}

        for row in data[3:]:  # Пропускаем настройки и заголовки
            if row[0] and row[0].strip() and len(row) > 1:
                if row[1] == "Доход":  # Только доходы
                    day = row[0]
                    amount = safe_float(row[4])
                    category = row[3] if len(row) > 3 else ""
                    comment = row[6] if len(row) > 6 else ""
                    hours = safe_float(row[8]) if len(row) > 8 else 0

                    if day not in income_by_day:
                        income_by_day[day] = {
                            "total": 0,
                            "tips": 0,
                            "hours": 0,
                            "other": 0,
                            "entries": []
                        }

                    income_by_day[day]["total"] += amount

                    # Разделяем на чаевые и другое
                    if category == "Зарплата/Чаевые":
                        income_by_day[day]["tips"] += amount
                        income_by_day[day]["hours"] += hours
                    else:
                        income_by_day[day]["other"] += amount

                    income_by_day[day]["entries"].append({
                        "amount": amount,
                        "category": category,
                        "comment": comment,
                        "hours": hours
                    })

        # Сортируем по дням
        sorted_days = sorted(income_by_day.keys(), key=lambda x: int(x) if x.isdigit() else 0)

        return {
            "by_day": income_by_day,
            "sorted_days": sorted_days,
            "total_income": sum(d["total"] for d in income_by_day.values()),
            "total_tips": sum(d["tips"] for d in income_by_day.values()),
            "total_hours": sum(d["hours"] for d in income_by_day.values())
        }

    @retry_on_error(max_retries=3, delay=1.0)
    def get_account_expenses(self, account_name: str, exclude_categories: List[str] = None) -> float:
        """
        Получить сумму расходов по счету за текущий месяц

        Args:
            account_name: Название счета
            exclude_categories: Категории для исключения из подсчета

        Returns:
            float: Сумма расходов
        """
        self._ensure_connection()
        sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        data = sheet.get_all_values()

        if exclude_categories is None:
            exclude_categories = []

        total_expenses = 0.0

        for row in data[3:]:  # Пропускаем настройки и заголовки
            if row[0] and row[0].strip() and len(row) > 4:
                trans_type = row[1]  # Тип транзакции
                account = row[2].strip()  # Счёт
                category = row[3].strip() if len(row) > 3 else ""  # Категория
                amount = safe_float(row[4])  # Сумма

                # Считаем только расходы с указанного счета, исключая определенные категории
                if trans_type == "Расход" and account == account_name:
                    if category not in exclude_categories:
                        total_expenses += amount

        return total_expenses

    @retry_on_error(max_retries=3, delay=1.0)
    def get_weekly_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Получить сводку за последние N дней

        Args:
            days_back: Количество дней назад (по умолчанию 7 - неделя)

        Returns:
            Dict с данными за неделю: доходы, расходы, по категориям
        """
        self._ensure_connection()
        sheet = self.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        data = sheet.get_all_values()

        # Определяем диапазон дней
        today = datetime.now().day
        # Вычисляем начало недели (days_back дней назад)
        start_day = max(1, today - days_back + 1)

        # Собираем транзакции за период
        total_income = 0
        total_expense = 0
        total_hours = 0

        # Группировка по категориям
        income_by_category = {}
        expense_by_category = {}

        for row in data[3:]:  # Пропускаем настройки и заголовки
            if row[0] and row[0].strip() and len(row) > 1:
                try:
                    day = int(row[0])
                except (ValueError, TypeError):
                    continue

                # Проверяем, входит ли день в диапазон
                if start_day <= day <= today:
                    trans_type = row[1]
                    category = row[3] if len(row) > 3 else ""
                    amount = safe_float(row[4])
                    hours = safe_float(row[8]) if len(row) > 8 else 0

                    # Получаем валюту (колонка M) и сумму в BYN (колонка L)
                    currency = row[12] if len(row) > 12 else "BYN"
                    amount_byn = safe_float(row[11]) if len(row) > 11 and row[11] else amount

                    # Если валюта не BYN, используем эквивалент в BYN (колонка L)
                    if currency and currency != "BYN":
                        amount_to_count = amount_byn
                    else:
                        amount_to_count = amount

                    if trans_type == "Доход":
                        total_income += amount_to_count
                        total_hours += hours
                        if category:
                            income_by_category[category] = income_by_category.get(category, 0) + amount_to_count

                    elif trans_type == "Расход":
                        total_expense += amount_to_count
                        if category:
                            expense_by_category[category] = expense_by_category.get(category, 0) + amount_to_count

        # Сортируем категории по сумме (по убыванию)
        income_by_category = dict(sorted(income_by_category.items(), key=lambda x: x[1], reverse=True))
        expense_by_category = dict(sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True))

        return {
            "start_day": start_day,
            "end_day": today,
            "days_count": days_back,
            "total_income": total_income,
            "total_expense": total_expense,
            "total_hours": total_hours,
            "balance": total_income - total_expense,
            "income_by_category": income_by_category,
            "expense_by_category": expense_by_category
        }


# Создаем глобальный экземпляр
sheets_service = None

def get_sheets_service() -> GoogleSheetsService:
    """Получить экземпляр сервиса (singleton)"""
    global sheets_service
    if sheets_service is None:
        sheets_service = GoogleSheetsService()
    return sheets_service
