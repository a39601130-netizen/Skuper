import { useEffect, useState } from 'react';
import { getWeeklySummary } from '../api/client';
import type { WeeklySummary } from '../types';

const CATEGORY_EMOJI: Record<string, string> = {
  'Продукты': '🛒', 'Кафе': '☕', 'Транспорт': '🚌', 'Такси': '🚕',
  'Досуг': '🎮', 'Покупки': '🛍️', 'Здоровье и красота': '💅',
  'Аптека': '💊', 'Ништяки': '🍫', 'Аренда': '🏠', 'Коммуналка': '🔌',
  'Интернет и связь': '📱', 'Кошки': '🐱', 'Долги': '💳', 'Одежда': '👕',
  'Подарки': '🎁',
};

export default function WeeklyReportPage() {
  const [report, setReport] = useState<WeeklySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [daysBack, setDaysBack] = useState(7);

  const load = (days: number) => {
    setLoading(true);
    getWeeklySummary(days)
      .then(setReport)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(daysBack); }, [daysBack]);

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;
  if (!report) return <div className="page"><div className="empty"><div className="empty-icon">📊</div>Нет данных</div></div>;

  const sortedCategories = Object.entries(report.expense_by_category)
    .sort(([, a], [, b]) => b - a);

  const maxCat = sortedCategories.length > 0 ? sortedCategories[0][1] : 1;

  return (
    <div className="page">
      <h1 className="page-title">Отчёт</h1>

      {/* Period selector */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {[7, 14, 30].map((d) => (
          <button key={d}
            className={`btn ${daysBack === d ? 'btn-primary' : 'btn-ghost'}`}
            style={{ flex: 1 }}
            onClick={() => setDaysBack(d)}>
            {d} дн
          </button>
        ))}
      </div>

      {/* Period info */}
      <div className="card">
        <div className="stat-label">{report.from_date} — {report.to_date}</div>
        <div className="stat-label">{report.transaction_count} транзакций</div>
      </div>

      {/* Totals */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Доходы</div>
          <div className="stat-value amount income">{report.total_income.toFixed(2)}</div>
        </div>
        <div className="card">
          <div className="card-title">Расходы</div>
          <div className="stat-value amount expense">{report.total_expense.toFixed(2)}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Баланс</div>
        <div className={`stat-value amount ${report.balance >= 0 ? 'income' : 'expense'}`}>
          {report.balance >= 0 ? '+' : ''}{report.balance.toFixed(2)} BYN
        </div>
      </div>

      {/* Expense by category */}
      {sortedCategories.length > 0 && (
        <div className="card">
          <div className="card-title">Расходы по категориям</div>
          {sortedCategories.map(([cat, amount]) => {
            const pct = (amount / maxCat) * 100;
            return (
              <div key={cat} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span>{CATEGORY_EMOJI[cat] || '📦'} {cat}</span>
                  <span className="amount expense">{amount.toFixed(2)}</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill warn" style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
