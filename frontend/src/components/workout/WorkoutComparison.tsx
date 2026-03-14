import { useEffect, useState } from 'react';
import { getWorkoutComparison } from '../../api/client';
import type { WorkoutDetail } from '../../types';

interface Props {
  workoutId: number;
  onClose: () => void;
}

export default function WorkoutComparison({ workoutId, onClose }: Props) {
  const [current, setCurrent] = useState<WorkoutDetail | null>(null);
  const [previous, setPrevious] = useState<WorkoutDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWorkoutComparison(workoutId)
      .then((data) => {
        setCurrent(data.current);
        setPrevious(data.previous);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [workoutId]);

  if (loading) return <div className="loading">Загрузка...</div>;
  if (!current) return null;

  // Группировка подходов по упражнению
  const groupSets = (sets: WorkoutDetail['sets']) => {
    const map: Record<string, typeof sets> = {};
    for (const s of sets) {
      if (!map[s.exercise_name]) map[s.exercise_name] = [];
      map[s.exercise_name].push(s);
    }
    return map;
  };

  const currentGroups = groupSets(current.sets);
  const previousGroups = previous ? groupSets(previous.sets) : {};

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h2 style={{ fontSize: 16, margin: 0 }}>
          Сравнение · День {current.day_type}
        </h2>
        <button className="btn btn-ghost" style={{ padding: '4px 12px', fontSize: 13 }} onClick={onClose}>
          Закрыть
        </button>
      </div>

      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, textAlign: 'center' }}>
          <div>
            <div className="stat-label">Текущая</div>
            <div style={{ fontWeight: 600 }}>{current.date}</div>
          </div>
          <div>
            <div className="stat-label">Предыдущая</div>
            <div style={{ fontWeight: 600 }}>{previous?.date || '—'}</div>
          </div>
        </div>
      </div>

      {Object.entries(currentGroups).map(([name, sets]) => {
        const prevSets = previousGroups[name] || [];
        const curMax = Math.max(...sets.map((s) => s.weight));
        const prevMax = prevSets.length > 0 ? Math.max(...prevSets.map((s) => s.weight)) : 0;
        const diff = curMax - prevMax;

        return (
          <div className="card" key={name}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div className="card-title">{name}</div>
              {prevMax > 0 && (
                <span style={{
                  color: diff > 0 ? 'var(--success)' : diff < 0 ? 'var(--danger)' : 'var(--text-secondary)',
                  fontWeight: 600, fontSize: 13,
                }}>
                  {diff > 0 ? '+' : ''}{diff}кг
                </span>
              )}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <div>
                {sets.map((s) => (
                  <div key={s.id} style={{ fontSize: 13, marginBottom: 2 }}>
                    {s.weight}кг × {s.reps} {s.rpe ? `RPE${s.rpe}` : ''}
                  </div>
                ))}
              </div>
              <div>
                {prevSets.length > 0 ? prevSets.map((s) => (
                  <div key={s.id} style={{ fontSize: 13, marginBottom: 2, color: 'var(--text-secondary)' }}>
                    {s.weight}кг × {s.reps} {s.rpe ? `RPE${s.rpe}` : ''}
                  </div>
                )) : (
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>—</div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
