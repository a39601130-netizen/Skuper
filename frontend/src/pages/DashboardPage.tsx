import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMonthlySummary } from '../api/client';
import type { MonthlySummary } from '../types';

function formatMoney(value: number, currency = 'BYN'): string {
  return `${value.toFixed(2)} ${currency}`;
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    getMonthlySummary()
      .then(setSummary)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;
  if (error) return <div className="page"><div className="empty">{error}</div></div>;
  if (!summary) return null;

  const expenseCategories = summary.categories
    .filter((c) => c.type === 'Расход' && c.spent > 0)
    .sort((a, b) => b.spent - a.spent);

  return (
    <div className="page">
      <h1 className="page-title">Финансы</h1>

      {/* Сводка */}
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Доходы</div>
          <div className="stat-value amount income">{formatMoney(summary.total_income)}</div>
        </div>
        <div className="card">
          <div className="card-title">Расходы</div>
          <div className="stat-value amount expense">{formatMoney(summary.total_expense)}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Баланс</div>
        <div className="stat-value">{formatMoney(summary.balance)}</div>
        <div className="stat-label">На счетах: {formatMoney(summary.total_on_accounts)}</div>
      </div>

      {/* Счета */}
      <div className="card">
        <div className="card-title">Счета</div>
        {summary.accounts.map((acc) => (
          <div className="list-item" key={acc.name}>
            <span className="list-item-icon">{acc.emoji || '💳'}</span>
            <div className="list-item-content">
              <div className="list-item-title">{acc.name}</div>
            </div>
            <div className="list-item-right">
              <span className="amount">{formatMoney(acc.current, acc.currency)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Категории расходов с бюджетами */}
      {expenseCategories.length > 0 && (
        <div className="card">
          <div className="card-title">Расходы по категориям</div>
          {expenseCategories.map((cat) => {
            const pct = cat.budget > 0 ? Math.min(cat.progress * 100, 100) : 0;
            const status = cat.progress >= 1 ? 'over' : cat.progress >= 0.8 ? 'warn' : 'ok';
            return (
              <div key={cat.name} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span>{cat.emoji} {cat.name}</span>
                  <span className="amount expense">
                    {cat.spent.toFixed(0)}
                    {cat.budget > 0 && <span className="stat-label"> / {cat.budget.toFixed(0)}</span>}
                  </span>
                </div>
                {cat.budget > 0 && (
                  <div className="progress-bar">
                    <div className={`progress-fill ${status}`} style={{ width: `${pct}%` }} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Быстрое добавление */}
      <button className="btn btn-primary btn-full" onClick={() => navigate('/add')}>
        ➕ Добавить транзакцию
      </button>
    </div>
  );
}
