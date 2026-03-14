import { useEffect, useState } from 'react';
import { getWorkoutHistory } from '../api/client';
import type { WorkoutHistory } from '../types';

export default function WorkoutHistoryPage() {
  const [history, setHistory] = useState<WorkoutHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWorkoutHistory(20)
      .then(setHistory)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;

  return (
    <div className="page">
      <h1 className="page-title">История тренировок</h1>

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
