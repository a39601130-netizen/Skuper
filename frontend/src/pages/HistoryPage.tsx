import { useEffect, useState } from 'react';
import { getTransactions, deleteTransaction } from '../api/client';
import type { Transaction } from '../types';

const TYPE_EMOJI: Record<string, string> = {
  'Доход': '💰',
  'Расход': '💸',
  'Перевод': '🔄',
  'Обмен валюты': '💱',
};

export default function HistoryPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    getTransactions(50)
      .then(setTransactions)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleDelete = async (txId: number) => {
    if (!confirm('Удалить транзакцию?')) return;
    try {
      await deleteTransaction(txId);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      load();
    } catch {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    }
  };

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;

  return (
    <div className="page">
      <h1 className="page-title">История</h1>

      {transactions.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📭</div>
          Нет транзакций
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          {transactions.map((tx) => {
            const emoji = TYPE_EMOJI[tx.type] || '📦';
            const isExpense = tx.type === 'Расход';
            const isIncome = tx.type === 'Доход';
            const isTransfer = tx.type === 'Перевод';
            return (
              <div className="list-item" key={tx.id}>
                <span className="list-item-icon">{emoji}</span>
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
                    style={{
                      background: 'none', border: 'none', color: 'var(--danger)',
                      fontSize: 12, cursor: 'pointer', padding: '4px 0',
                    }}
                  >
                    Удалить
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
