import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getMonthlySummary } from '../api/client';
import type { MonthlySummary } from '../types';

const MONTH_NAMES = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

function formatMoney(value: number | null | undefined, currency = 'BYN'): string {
  return `${(value ?? 0).toFixed(2)} ${currency}`;
}

export default function DashboardPage() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  const isCurrentMonth = month === now.getMonth() + 1 && year === now.getFullYear();

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (isCurrentMonth) return;
    if (month === 12) { setMonth(1); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  };

  const load = useCallback(() => {
    setLoading(true); setError(''); setSummary(null);
    getMonthlySummary(month, year)
      .then(setSummary)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [month, year]);

  useEffect(load, [location.key, load]);

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;
  if (error) return (
    <div className="page">
      <div className="error-box">
        <div className="error-icon">⚠️</div>
        <div className="error-text">{error}</div>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>
          Повторить
        </button>
      </div>
    </div>
  );
  if (!summary) return (
    <div className="page">
      <div className="empty">
        <div className="empty-icon">📊</div>
        <div>Нет данных</div>
      </div>
    </div>
  );

  const expenseCategories = summary.categories
    .filter((c) => c.type === 'Расход' && c.spent > 0)
    .sort((a, b) => b.spent - a.spent);

  return (
    <div className="page">
      <h1 className="page-title">Финансы</h1>

      {/* Month selector */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        gap: 12, marginBottom: 12,
      }}>
        <button className="btn btn-ghost" onClick={prevMonth} style={{ padding: '4px 12px' }}>
          ←
        </button>
        <span style={{ fontWeight: 600, fontSize: 15, minWidth: 130, textAlign: 'center' }}>
          {MONTH_NAMES[month]} {year}
        </span>
        <button
          className="btn btn-ghost"
          onClick={nextMonth}
          disabled={isCurrentMonth}
          style={{ padding: '4px 12px', opacity: isCurrentMonth ? 0.3 : 1 }}
        >
          →
        </button>
      </div>

      {/* Summary */}
      <div className="grid-2">
        <div className="card" style={{ cursor: 'pointer' }} onClick={() => navigate('/income')}>
          <div className="card-title">Доходы</div>
          <div className="stat-value amount income">{formatMoney(summary.total_income)}</div>
        </div>
        <div className="card" style={{ cursor: 'pointer' }} onClick={() => navigate(`/expenses?month=${month}&year=${year}`)}>
          <div className="card-title">Расходы</div>
          <div className="stat-value amount expense">{formatMoney(summary.total_expense)}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Баланс</div>
        <div className="stat-value">{formatMoney(summary.balance)}</div>
        <div className="stat-label">На счетах: {formatMoney(summary.total_on_accounts)}</div>
      </div>

      {/* Accounts */}
      <div className="card">
        <div className="card-title">Счета</div>
        {summary.accounts.map((acc) => (
          <div className="list-item" key={acc.name}>
            <span className="list-item-icon">{acc.emoji || '💳'}</span>
            <div className="list-item-content">
              <div className="list-item-title">{acc.name}</div>
              {acc.monthly_spent ? (
                <div className="stat-label">Расход: {formatMoney(acc.monthly_spent)}</div>
              ) : null}
            </div>
            <div className="list-item-right">
              <span className="amount">{formatMoney(acc.current, acc.currency)}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Budget warnings */}
      {summary.over_budget.length > 0 && (
        <div className="card" style={{ borderLeft: '3px solid var(--danger)' }}>
          <div className="card-title" style={{ color: 'var(--danger)' }}>Бюджет превышен</div>
          {summary.over_budget.map((cat) => (
            <div key={cat.name} style={{ marginBottom: 4 }}>
              {cat.emoji} {cat.name}: {cat.spent.toFixed(2)} / {cat.budget.toFixed(0)} BYN
            </div>
          ))}
        </div>
      )}
      {summary.near_limit.length > 0 && (
        <div className="card" style={{ borderLeft: '3px solid var(--warning)' }}>
          <div className="card-title" style={{ color: 'var(--warning)' }}>Близко к лимиту</div>
          {summary.near_limit.map((cat) => (
            <div key={cat.name} style={{ marginBottom: 4 }}>
              {cat.emoji} {cat.name}: {cat.spent.toFixed(2)} / {cat.budget.toFixed(0)} BYN
            </div>
          ))}
        </div>
      )}

      {/* Expense categories */}
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
                    {cat.spent.toFixed(2)}
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

      {/* Quick links */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => navigate('/income')}>
          💰 Доходы
        </button>
        <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => navigate(`/expenses?month=${month}&year=${year}`)}>
          📋 Расходы
        </button>
      </div>

      <button className="btn btn-primary btn-full" onClick={() => navigate('/add')}>
        ➕ Добавить транзакцию
      </button>
    </div>
  );
}
