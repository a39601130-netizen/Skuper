import { useState } from 'react';
import type { WorkoutDetail } from '../../types';

interface Props {
  workout: WorkoutDetail;
  onComplete: (energyAfter: number, notes: string) => void;
}

export default function WorkoutSummary({ workout, onComplete }: Props) {
  const [energy, setEnergy] = useState(7);
  const [notes, setNotes] = useState('');

  // Группировка подходов по упражнению
  const byExercise: Record<string, typeof workout.sets> = {};
  for (const s of workout.sets) {
    if (!byExercise[s.exercise_name]) byExercise[s.exercise_name] = [];
    byExercise[s.exercise_name].push(s);
  }

  return (
    <div>
      <div className="card">
        <div className="card-title">Итоги тренировки</div>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{workout.sets.length}</div>
            <div className="stat-label">подходов</div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>
              {Object.keys(byExercise).length}
            </div>
            <div className="stat-label">упражнений</div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>
              {workout.sets.reduce((sum, s) => sum + s.weight * s.reps, 0).toFixed(0)}
            </div>
            <div className="stat-label">кг тоннаж</div>
          </div>
        </div>
      </div>

      {Object.entries(byExercise).map(([name, sets]) => (
        <div className="card" key={name}>
          <div className="card-title">{name}</div>
          {sets.map((s) => (
            <div key={s.id} className="list-item" style={{ padding: '4px 0' }}>
              <span className="stat-label">Подход {s.set_number}</span>
              <span>{s.weight}кг × {s.reps}</span>
              {s.rpe && <span className="stat-label"> RPE {s.rpe}</span>}
            </div>
          ))}
        </div>
      ))}

      <div className="card">
        <div className="card-title">Энергия после (1-10)</div>
        <input type="range" min={1} max={10} value={energy}
          onChange={(e) => setEnergy(+e.target.value)} style={{ width: '100%' }} />
        <div style={{ textAlign: 'center', fontSize: 24, fontWeight: 700 }}>{energy}</div>
      </div>

      <div className="card">
        <div className="card-title">Заметки</div>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Как прошла тренировка..."
          rows={3}
          style={{
            width: '100%', padding: 12, fontSize: 14,
            background: 'var(--bg-secondary)', color: 'var(--text-primary)',
            border: '1px solid var(--border)', borderRadius: 10, resize: 'vertical',
          }}
        />
      </div>

      <button className="btn btn-primary btn-full" onClick={() => onComplete(energy, notes)}>
        Завершить тренировку
      </button>
    </div>
  );
}
