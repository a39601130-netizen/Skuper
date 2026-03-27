import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getTransactions, deleteTransaction } from '../api/client';
import { ListPageSkeleton } from '../components/Skeleton';
import { useToast } from '../components/Toast';
import { AlertTriangle, Plus, Inbox, X } from 'lucide-react';
import type { Transaction } from '../types';

const TYPE_EMOJI: Record<string, string> = {
  'Доход': '💰',
  'Расход': '💸',
  'Перевод': '🔄',
  'Обмен валюты': '💱',
};

export default function HistoryPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const accountFilter = searchParams.get('account') || '';
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState<number | null>(null);
  const { showToast } = useToast();

  const load = () => {
    setLoading(true); setError('');
    const filters = accountFilter ? { account: accountFilter } : undefined;
    getTransactions(50, filters)
      .then(setTransactions)
      .catch((e) => setError(e.message || 'Ошибка загрузки'))
      .finally(() => setLoading(false));
  };

  useEffect(load, [accountFilter]);

  const handleDelete = async (txId: number) => {
    if (deleting) return;
    if (!confirm('Удалить транзакцию?')) return;
    setDeleting(txId);
    try {
      await deleteTransaction(txId);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      showToast('Транзакция удалена', 'success');
      load();
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
      showToast('Ошибка удаления', 'error');
    } finally {
      setDeleting(null);
    }
  };

  if (loading) return <ListPageSkeleton />;
  if (error) return (
    <div className="page">
      <div className="error-box" role="alert">
        <AlertTriangle size={48} color="var(--danger)" />
        <div className="error-text">{error}</div>
        <button className="btn btn-primary" onClick={load}>Повторить</button>
      </div>
    </div>
  );

  return (
    <div className="page">
      <h1 className="page-title">История</h1>

      {accountFilter && (() => {
        const expense = transactions.filter(t => t.type === 'Расход').reduce((s, t) => s + Number(t.amount), 0);
        const income = transactions.filter(t => t.type === 'Доход').reduce((s, t) => s + Number(t.amount), 0);
        return (
          <div>
            <div className="filter-chip-bar">
              <span className="filter-chip">
                {accountFilter}
                <button className="filter-chip-remove" onClick={() => setSearchParams({})} aria-label="Сбросить фильтр">
                  <X size={14} />
                </button>
              </span>
            </div>
            {transactions.length > 0 && (
              <div className="grid-2" style={{ marginBottom: 12 }}>
                {expense > 0 && (
                  <div className="card" style={{ padding: '10px 14px' }}>
                    <div className="card-title">Расходы</div>
                    <div className="stat-value amount expense">-{expense.toFixed(2)} BYN</div>
                  </div>
                )}
                {income > 0 && (
                  <div className="card" style={{ padding: '10px 14px' }}>
                    <div className="card-title">Доходы</div>
                    <div className="stat-value amount income">+{income.toFixed(2)} BYN</div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })()}

      {transactions.length === 0 ? (
        <div className="empty">
          <div className="empty-icon"><Inbox size={48} /></div>
          <div className="empty-text">Нет транзакций</div>
          <div className="empty-hint">Добавьте первую запись о расходе или доходе</div>
          <button className="empty-action" onClick={() => navigate('/add')}>
            <Plus size={16} /> Добавить
          </button>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }} role="list" aria-label="Список транзакций">
          {transactions.map((tx) => {
            const emoji = TYPE_EMOJI[tx.type] || '📦';
            const isExpense = tx.type === 'Расход';
            const isIncome = tx.type === 'Доход';
            const isTransfer = tx.type === 'Перевод';
            return (
              <div className="list-item" key={tx.id} role="listitem">
                <span className="list-item-icon" aria-hidden="true">{emoji}</span>
                <div className="list-item-content">
                  <div className="list-item-title">
                    {tx.category || tx.type}
                    {isTransfer && tx.to_account && ` → ${tx.to_account}`}
                  </div>
                  <div className="list-item-meta">
                    {tx.full_date}
                    {tx.account && ` · ${tx.account}`}
                    {tx.comment && ` · ${tx.comment}`}
                    {tx.hours && ` · ${tx.hours}ч`}
                  </div>
                </div>
                <div className="list-item-right">
                  <div className={`amount ${isExpense ? 'expense' : isIncome ? 'income' : isTransfer ? 'transfer' : ''}`}>
                    {isExpense ? '-' : isIncome ? '+' : ''}{tx.amount} {tx.currency || 'BYN'}
                  </div>
                  {tx.exchange_rate && (
                    <div className="stat-label">
                      курс {tx.exchange_rate} → {tx.amount_to} BYN
                    </div>
                  )}
                  <button
                    className="btn-delete"
                    onClick={() => handleDelete(tx.id)}
                    disabled={deleting === tx.id}
                    aria-label={`Удалить транзакцию ${tx.category || tx.type}`}
                  >
                    {deleting === tx.id ? '...' : 'Удалить'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
