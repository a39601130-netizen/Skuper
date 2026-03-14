import { useEffect, useState, useCallback } from 'react';
import { getTransactions, deleteTransaction, getReferences } from '../api/client';
import type { Transaction, References } from '../types';
import SwipeableListItem from '../components/SwipeableListItem';

const TYPE_EMOJI: Record<string, string> = {
  'Доход': '💰',
  'Расход': '💸',
  'Перевод': '🔄',
  'Обмен валюты': '💱',
};

export default function HistoryPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refs, setRefs] = useState<References | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<{
    type?: string; category?: string; account?: string;
    date_from?: string; date_to?: string;
  }>({});

  useEffect(() => {
    getReferences().then(setRefs).catch(() => {});
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    const cleanFilters = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v)
    );
    getTransactions(50, Object.keys(cleanFilters).length > 0 ? cleanFilters : undefined)
      .then(setTransactions)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(load, [load]);

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить транзакцию?')) return;
    try {
      await deleteTransaction(id);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      load();
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    }
  };

  const clearFilters = () => setFilters({});
  const hasFilters = Object.values(filters).some(Boolean);

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 className="page-title" style={{ margin: 0 }}>История</h1>
        <button className={`btn ${showFilters ? 'btn-primary' : 'btn-ghost'}`}
          style={{ fontSize: 13, padding: '6px 12px' }}
          onClick={() => setShowFilters(!showFilters)}>
          {hasFilters ? 'Фильтры *' : 'Фильтры'}
        </button>
      </div>

      {showFilters && (
        <div className="card" style={{ marginTop: 12 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Тип</label>
              <select value={filters.type || ''} onChange={(e) => setFilters({ ...filters, type: e.target.value })}
                style={selectStyle}>
                <option value="">Все</option>
                {['Расход', 'Доход', 'Перевод'].map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Счёт</label>
              <select value={filters.account || ''} onChange={(e) => setFilters({ ...filters, account: e.target.value })}
                style={selectStyle}>
                <option value="">Все</option>
                {refs?.accounts.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Категория</label>
              <select value={filters.category || ''} onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                style={selectStyle}>
                <option value="">Все</option>
                {refs?.categories.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-secondary)' }}>От</label>
              <input type="date" value={filters.date_from || ''}
                onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
                style={selectStyle} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-secondary)' }}>До</label>
              <input type="date" value={filters.date_to || ''}
                onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
                style={selectStyle} />
            </div>
          </div>
          {hasFilters && (
            <button className="btn btn-ghost btn-full" style={{ marginTop: 8, fontSize: 13 }}
              onClick={clearFilters}>
              Сбросить фильтры
            </button>
          )}
        </div>
      )}

      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : transactions.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📭</div>
          {hasFilters ? 'Нет транзакций по фильтру' : 'Нет транзакций'}
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          {transactions.map((tx) => {
            const emoji = TYPE_EMOJI[tx.type] || '📦';
            const isExpense = tx.type === 'Расход';
            const isIncome = tx.type === 'Доход';
            return (
              <SwipeableListItem key={tx.id} onDelete={() => handleDelete(tx.id)}>
                <div className="list-item">
                  <span className="list-item-icon">{emoji}</span>
                  <div className="list-item-content">
                    <div className="list-item-title">
                      {tx.category || tx.type}
                    </div>
                    <div className="list-item-meta">
                      {tx.date}
                      {tx.account && ` · ${tx.account}`}
                      {tx.comment && ` · ${tx.comment}`}
                    </div>
                  </div>
                  <div className="list-item-right">
                    <div className={`amount ${isExpense ? 'expense' : isIncome ? 'income' : ''}`}>
                      {isExpense ? '-' : isIncome ? '+' : ''}{tx.amount} {tx.currency || 'BYN'}
                    </div>
                  </div>
                </div>
              </SwipeableListItem>
            );
          })}
        </div>
      )}
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  width: '100%', padding: '8px', fontSize: 13,
  background: 'var(--bg-secondary)', color: 'var(--text-primary)',
  border: '1px solid var(--border)', borderRadius: 8, marginTop: 4,
};
