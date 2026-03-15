import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWorkoutHistory } from '../api/client';
import type { WorkoutHistory } from '../types';

export default function WorkoutHistoryPage() {
  const navigate = useNavigate();
  const [history, setHistory] = useState<WorkoutHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true); setError('');
    getWorkoutHistory(20)
      .then(setHistory)
      .catch((e) => setError(e.message || 'Ошибка загрузки'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

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

  return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <button className="btn btn-ghost" onClick={() => navigate(-1)} style={{ padding: '4px 12px', fontSize: 14 }}>← Назад</button>
        <h1 className="page-title" style={{ margin: 0 }}>История тренировок</h1>
      </div>

      {history.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">🏋️</div>
          Нет записей о тренировках
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          {history.map((w, i) => (
            <div className="list-item" key={i} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontWeight: 600 }}>
                  День {w.day_type} · Неделя {w.week}
                </span>
                <span className="stat-label">{w.date}</span>
              </div>
              <div style={{ display: 'flex', gap: 12, fontSize: 13, color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                <span>Фаза: {w.phase}</span>
                {w.energy_before > 0 && <span>⚡ {w.energy_before}→{w.energy_after}</span>}
                {w.sleep_hours > 0 && <span>😴 {w.sleep_hours}ч</span>}
                {w.sleep_quality && <span>💤 {w.sleep_quality}</span>}
                {w.back_pain && <span>🔙 {w.back_pain}</span>}
                {w.emotional_wave && <span>🌊 {w.emotional_wave}</span>}
              </div>
              {w.notes && (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                  {w.notes}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
