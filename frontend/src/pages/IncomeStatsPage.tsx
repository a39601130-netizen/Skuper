import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getIncomeStats } from '../api/client';
import type { IncomeStats } from '../types';

const MONTH_NAMES = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

export default function IncomeStatsPage() {
  const navigate = useNavigate();
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [stats, setStats] = useState<IncomeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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
    setLoading(true); setError('');
    getIncomeStats(month, year)
      .then(setStats)
      .catch((e) => setError(e.message || 'Ошибка загрузки'))
      .finally(() => setLoading(false));
  }, [month, year]);

  useEffect(load, [load]);

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;
  if (error) return (
    <div className="page">
      <div className="error-box">
        <div className="error-icon">⚠️</div>
        <div className="error-text">{error}</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={() => navigate(-1)}>← Назад</button>
          <button className="btn btn-primary" onClick={load}>Повторить</button>
        </div>
      </div>
    </div>
  );
  if (!stats) return <div className="page"><div className="empty"><div className="empty-icon">📊</div>Нет данных</div></div>;

  const avgPerHour = stats.total_hours > 0 ? (stats.total_income / stats.total_hours).toFixed(2) : '—';

  return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ padding: '4px 12px', fontSize: 14 }}>← Назад</button>
        <h1 className="page-title" style={{ margin: 0 }}>Доходы</h1>
      </div>

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
        <div className="card">
          <div className="card-title">Всего</div>
          <div className="stat-value amount income">{stats.total_income.toFixed(2)} BYN</div>
        </div>
        <div className="card">
          <div className="card-title">Смен / Часов</div>
          <div className="stat-value">{stats.days.filter(d => d.hours > 0).length} / {stats.total_hours.toFixed(1)}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Ставка</div>
          <div className="stat-value">{stats.base_hourly_rate} BYN/ч</div>
        </div>
        <div className="card">
          <div className="card-title">Факт/ч</div>
          <div className="stat-value">{avgPerHour} BYN</div>
        </div>
      </div>

      {/* Days */}
      {stats.days.length === 0 ? (
        <div className="empty">Нет доходов за этот месяц</div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          {stats.days.map((day) => {
            const basePay = day.hours > 0 ? day.hours * stats.base_hourly_rate : 0;
            const realRate = day.hours > 0 ? (day.total / day.hours).toFixed(2) : null;
            const comments = day.transactions.filter(t => t.comment).map(t => t.comment);
            return (
              <div className="list-item" key={day.day} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontWeight: 600 }}>{day.date}</span>
                  <span className="amount income">+{day.total.toFixed(2)} BYN</span>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {day.tips > 0 && <span>💵 Чаевые: {day.tips.toFixed(0)} BYN</span>}
                  {day.salary > 0 && <span>💰 Зарплата: {day.salary.toFixed(2)} BYN</span>}
                  {day.other > 0 && <span>📦 Прочее: {day.other.toFixed(0)} BYN</span>}
                  {basePay > 0 && (
                    <span>📋 Ставка: {basePay.toFixed(2)} BYN ({day.hours}ч × {stats.base_hourly_rate}) → {realRate} BYN/ч</span>
                  )}
                </div>
                {comments.length > 0 && (
                  <div style={{ marginTop: 4, fontSize: 12, color: 'var(--text-muted)' }}>
                    {comments.map((c, i) => <div key={i}>💬 {c}</div>)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
