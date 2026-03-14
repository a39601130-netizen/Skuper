import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentWeights, getNextWorkout } from '../api/client';
import type { ExerciseWeight, NextWorkout } from '../types';
import ExerciseProgressChart from '../components/charts/ExerciseProgressChart';
import WorkoutCalendar from '../components/workout/WorkoutCalendar';
import WorkoutComparison from '../components/workout/WorkoutComparison';

export default function WorkoutsPage() {
  const [weights, setWeights] = useState<ExerciseWeight[]>([]);
  const [next, setNext] = useState<NextWorkout | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'next' | 'weights' | 'progress' | 'calendar'>('next');
  const [compareId, setCompareId] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getCurrentWeights(), getNextWorkout()])
      .then(([w, n]) => { setWeights(w); setNext(n); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><div className="loading">Загрузка...</div></div>;

  return (
    <div className="page">
      <h1 className="page-title">Тренировки</h1>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        {(['next', 'weights', 'progress', 'calendar'] as const).map((t) => (
          <button key={t}
            className={`btn ${tab === t ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: 13, padding: '6px 12px' }}
            onClick={() => { setTab(t); setCompareId(null); }}>
            {{ next: 'План', weights: 'Веса', progress: 'Графики', calendar: 'Календарь' }[t]}
          </button>
        ))}
      </div>

      {/* Next Workout */}
      {tab === 'next' && next && (
        <>
          <div className="card">
            <div className="card-title">Следующая тренировка</div>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
              День {next.next_day}
            </div>
            {next.phase && (
              <div className="stat-label">
                Фаза: {next.phase.phase_name || '—'} · Неделя {next.phase.current_week || '?'}
              </div>
            )}
          </div>

          <div className="card" style={{ padding: 0 }}>
            {next.exercises.map((ex) => (
              <div className="list-item" key={ex.exercise_id}>
                <span className="list-item-icon">🏋️</span>
                <div className="list-item-content">
                  <div className="list-item-title">{ex.name}</div>
                  <div className="list-item-meta">{ex.category}</div>
                </div>
                <div className="list-item-right">
                  <div className="amount">{ex.current_weight || 0} кг</div>
                  <div className="stat-label">{ex.target_reps || ''}</div>
                </div>
              </div>
            ))}
          </div>

          <button className="btn btn-primary btn-full" style={{ marginTop: 12 }}
            onClick={() => navigate('/workout/session')}>
            Начать тренировку
          </button>
        </>
      )}

      {/* Current Weights */}
      {tab === 'weights' && (
        <>
          {['A', 'B'].map((day) => {
            const dayWeights = weights.filter((w) => w.day === day);
            if (dayWeights.length === 0) return null;
            return (
              <div key={day}>
                <h2 style={{ fontSize: 16, marginBottom: 8, marginTop: 8 }}>День {day}</h2>
                <div className="card" style={{ padding: 0 }}>
                  {dayWeights.map((w) => (
                    <div className="list-item" key={w.exercise_id}>
                      <div className="list-item-content">
                        <div className="list-item-title">{w.name}</div>
                        <div className="list-item-meta">
                          {w.status === 'ready' ? '✅ Готов к увеличению' : w.target_reps}
                        </div>
                      </div>
                      <div className="list-item-right">
                        <div className="amount">{w.current_weight} кг</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </>
      )}

      {/* Progress Charts */}
      {tab === 'progress' && weights.length > 0 && (
        <>
          {weights.slice(0, 6).map((w) => (
            <ExerciseProgressChart
              key={w.exercise_id}
              exerciseId={w.exercise_id}
              exerciseName={w.name}
            />
          ))}
        </>
      )}

      {/* Calendar */}
      {tab === 'calendar' && !compareId && (
        <WorkoutCalendar onSelectWorkout={(id) => setCompareId(id)} />
      )}

      {tab === 'calendar' && compareId && (
        <WorkoutComparison workoutId={compareId} onClose={() => setCompareId(null)} />
      )}
    </div>
  );
}
