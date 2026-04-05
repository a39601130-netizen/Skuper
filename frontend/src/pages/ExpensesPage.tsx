import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { getMonthlySummary, getTransactions } from '../api/client';
import { DashboardSkeleton } from '../components/Skeleton';
import { ChevronLeft, AlertTriangle, TrendingDown } from 'lucide-react';
import type { MonthlySummary, Transaction } from '../types';

const MONTH_NAMES = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

const COLORS = [
  '#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16',
  '#e879f9', '#fb923c',
];

function formatMoney(value: number): string {
  return `${value.toFixed(2)} BYN`;
}

function getMonthDateRange(month: number, year: number) {
  const from = `${year}-${String(month).padStart(2, '0')}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const to = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
  return { from, to };
}

function getPrevMonth(month: number, year: number) {
  return month === 1 ? { month: 12, year: year - 1 } : { month: month - 1, year };
}

interface PieData {
  name: string;
  value: number;
  emoji: string;
  pct: number;
}

export default function ExpensesPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const now = new Date();
  const month = Number(searchParams.get('month')) || now.getMonth() + 1;
  const year = Number(searchParams.get('year')) || now.getFullYear();

  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [prevSummary, setPrevSummary] = useState<MonthlySummary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedCat, setExpandedCat] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { from, to } = getMonthDateRange(month, year);
      const prev = getPrevMonth(month, year);
      const [cur, prv, txs] = await Promise.all([
        getMonthlySummary(month, year),
        getMonthlySummary(prev.month, prev.year).catch(() => null),
        getTransactions(100, { date_from: from, date_to: to, type: 'Расход' }),
      ]);
      setSummary(cur);
      setPrevSummary(prv);
      setTransactions(txs);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, [month, year]);

  useEffect(() => { load(); }, [load]);

  const expenseCategories = useMemo(() =>
    (summary?.categories ?? [])
      .filter((c) => c.type === 'Расход' && c.spent > 0)
      .sort((a, b) => b.spent - a.spent),
    [summary?.categories]
  );

  if (loading) return <DashboardSkeleton />;
  if (error) return (
    <div className="page">
      <div className="error-box" role="alert">
        <AlertTriangle size={48} color="var(--danger)" />
        <div className="error-text">{error}</div>
        <button className="btn btn-primary" onClick={load}>Повторить</button>
      </div>
    </div>
  );
  if (!summary) return (
    <div className="page">
      <div className="empty">
        <div className="empty-icon"><TrendingDown size={48} /></div>
        <div className="empty-text">Нет данных</div>
      </div>
    </div>
  );

  const totalExpense = summary.total_expense;

  const prevMap: Record<string, number> = {};
  if (prevSummary) {
    prevSummary.categories
      .filter((c) => c.type === 'Расход')
      .forEach((c) => { prevMap[c.name] = c.spent; });
  }
  const prevTotalExpense = prevSummary?.total_expense ?? 0;

  const threshold = totalExpense * 0.03;
  const mainCats: PieData[] = [];
  let otherSum = 0;
  expenseCategories.forEach((cat) => {
    if (cat.spent < threshold) {
      otherSum += cat.spent;
    } else {
      mainCats.push({
        name: cat.name,
        value: cat.spent,
        emoji: cat.emoji || '',
        pct: totalExpense > 0 ? (cat.spent / totalExpense) * 100 : 0,
      });
    }
  });
  if (otherSum > 0) {
    mainCats.push({
      name: 'Прочее',
      value: otherSum,
      emoji: '📦',
      pct: totalExpense > 0 ? (otherSum / totalExpense) * 100 : 0,
    });
  }

  const top3 = [...transactions].sort((a, b) => b.amount - a.amount).slice(0, 3);

  function compBadge(current: number, previous: number) {
    if (!previous || previous === 0) return null;
    const diff = ((current - previous) / previous) * 100;
    if (Math.abs(diff) < 1) return null;
    const up = diff > 0;
    return (
      <span className={`comp-badge ${up ? 'comp-up' : 'comp-down'}`}
        aria-label={`${up ? 'рост' : 'снижение'} на ${Math.abs(diff).toFixed(0)}%`}>
        <span aria-hidden="true">{up ? '↑' : '↓'}</span>{Math.abs(diff).toFixed(0)}%
      </span>
    );
  }

  function getCatTransactions(catName: string) {
    return transactions.filter((t) => t.category === catName);
  }

  function PieTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: PieData }> }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="pie-tooltip">
        {d.emoji} {d.name}: {formatMoney(d.value)} ({d.pct.toFixed(1)}%)
      </div>
    );
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ padding: '4px 12px' }} aria-label="Назад">
          <ChevronLeft size={16} />
        </button>
        <h1 className="page-title" style={{ margin: 0 }}>
          Расходы — {MONTH_NAMES[month]} {year}
        </h1>
      </div>

      {/* Total with comparison */}
      <div className="card">
        <div className="card-title">Итого расходы</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <div className="stat-value amount expense">{formatMoney(totalExpense)}</div>
          {compBadge(totalExpense, prevTotalExpense)}
        </div>
        {prevTotalExpense > 0 && (
          <div className="stat-label">
            {MONTH_NAMES[getPrevMonth(month, year).month]}: {formatMoney(prevTotalExpense)}
          </div>
        )}
      </div>

      {/* Top 3 */}
      {top3.length > 0 && (
        <div className="card">
          <div className="card-title">Топ-3 расходов</div>
          {top3.map((tx, i) => (
            <div className="list-item" key={tx.id} style={{ padding: '8px 0' }}>
              <span className="list-item-icon" style={{ fontSize: 18, width: 28 }} aria-hidden="true">
                {i === 0 ? '🥇' : i === 1 ? '🥈' : '🥉'}
              </span>
              <div className="list-item-content">
                <div className="list-item-title">{tx.category}</div>
                <div className="list-item-meta">{tx.comment || tx.full_date}</div>
              </div>
              <div className="list-item-right">
                <span className="amount expense">{formatMoney(tx.amount)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Categories with progress bars */}
      <div className="card">
        <div className="card-title">По категориям</div>
        {expenseCategories.map((cat) => {
          const pct = cat.budget > 0 ? Math.min(cat.progress * 100, 100) : 0;
          const status = cat.progress >= 1 ? 'over' : cat.progress >= 0.8 ? 'warn' : 'ok';
          const isExpanded = expandedCat === cat.name;
          const catTxs = isExpanded ? getCatTransactions(cat.name) : [];
          const prevSpent = prevMap[cat.name] ?? 0;

          return (
            <div key={cat.name} style={{ marginBottom: 8 }}>
              <div
                className="expense-cat-row"
                onClick={() => setExpandedCat(isExpanded ? null : cat.name)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setExpandedCat(isExpanded ? null : cat.name); }}}
                role="button"
                tabIndex={0}
                aria-expanded={isExpanded}
                aria-label={`${cat.emoji} ${cat.name}: ${cat.spent.toFixed(2)} BYN${cat.budget > 0 ? ` из ${cat.budget.toFixed(0)}` : ''}`}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, minWidth: 0 }}>
                  <span style={{ fontSize: 18 }} aria-hidden="true">{cat.emoji}</span>
                  <span className="list-item-title" style={{ flex: 1 }}>{cat.name}</span>
                  {compBadge(cat.spent, prevSpent)}
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <span className="amount expense">
                    {cat.spent.toFixed(2)}
                    {cat.budget > 0 && <span className="stat-label"> / {cat.budget.toFixed(0)}</span>}
                  </span>
                  <div className="stat-label">{(totalExpense > 0 ? (cat.spent / totalExpense) * 100 : 0).toFixed(1)}%</div>
                </div>
                <span className="expand-arrow" aria-hidden="true" style={{ transform: isExpanded ? 'rotate(90deg)' : undefined }}>›</span>
              </div>

              {cat.budget > 0 && (
                <div className="progress-bar" style={{ marginTop: 4 }}>
                  <div className={`progress-fill ${status}`} style={{ width: `${pct}%` }} />
                </div>
              )}

              {isExpanded && catTxs.length > 0 && (
                <div className="cat-transactions">
                  {catTxs.map((tx) => (
                    <div className="cat-tx-row" key={tx.id}>
                      <div className="cat-tx-info">
                        <span className="cat-tx-date">{tx.full_date}</span>
                        {tx.comment && <span className="cat-tx-comment">{tx.comment}</span>}
                      </div>
                      <span className="amount expense" style={{ fontSize: 13 }}>{formatMoney(tx.amount)}</span>
                    </div>
                  ))}
                </div>
              )}
              {isExpanded && catTxs.length === 0 && (
                <div className="cat-transactions" style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                  Нет транзакций
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Pie Chart */}
      {mainCats.length > 0 && (
        <div className="card">
          <div className="card-title">Диаграмма расходов</div>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={mainCats}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                innerRadius={50}
                paddingAngle={2}
                onClick={(_: unknown, idx: number) => {
                  const cat = mainCats[idx];
                  if (cat.name !== 'Прочее') {
                    setExpandedCat(expandedCat === cat.name ? null : cat.name);
                    setTimeout(() => {
                      document.querySelector('.expense-cat-row')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }, 100);
                  }
                }}
              >
                {mainCats.map((_entry, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="none" />
                ))}
              </Pie>
              <Tooltip content={<PieTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="pie-legend">
            {mainCats.map((d, i) => (
              <div className="pie-legend-item" key={d.name}>
                <span className="pie-legend-dot" style={{ background: COLORS[i % COLORS.length] }} aria-hidden="true" />
                <span>{d.emoji} {d.name}</span>
                <span className="stat-label" style={{ marginLeft: 'auto' }}>{d.pct.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
