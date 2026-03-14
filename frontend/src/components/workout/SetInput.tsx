import { useState } from 'react';

interface Props {
  exerciseName: string;
  setNumber: number;
  defaultWeight: number;
  weightStep: number;
  targetReps: string;
  onSubmit: (weight: number, reps: number) => void;
}

export default function SetInput({ exerciseName, setNumber, defaultWeight, weightStep, targetReps, onSubmit }: Props) {
  const [weight, setWeight] = useState(defaultWeight);
  const [reps, setReps] = useState(0);

  return (
    <div className="card">
      <div className="card-title">Подход {setNumber}</div>
      <div className="stat-label" style={{ marginBottom: 12 }}>{exerciseName} · Цель: {targetReps}</div>

      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Вес (кг)</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
          <button className="btn btn-ghost" onClick={() => setWeight(Math.max(0, weight - weightStep))}>-</button>
          <input type="number" inputMode="decimal" value={weight}
            onChange={(e) => setWeight(parseFloat(e.target.value) || 0)}
            style={{
              flex: 1, padding: '10px', fontSize: 20, fontWeight: 700, textAlign: 'center',
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', borderRadius: 8,
            }}
          />
          <button className="btn btn-ghost" onClick={() => setWeight(weight + weightStep)}>+</button>
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Повторения</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
          <button className="btn btn-ghost" onClick={() => setReps(Math.max(0, reps - 1))}>-</button>
          <input type="number" inputMode="numeric" value={reps || ''}
            onChange={(e) => setReps(parseInt(e.target.value) || 0)}
            placeholder="0"
            style={{
              flex: 1, padding: '10px', fontSize: 20, fontWeight: 700, textAlign: 'center',
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', borderRadius: 8,
            }}
          />
          <button className="btn btn-ghost" onClick={() => setReps(reps + 1)}>+</button>
        </div>
      </div>

      <button className="btn btn-primary btn-full" onClick={() => onSubmit(weight, reps)}
        disabled={reps === 0}>
        Записать подход
      </button>
    </div>
  );
}
