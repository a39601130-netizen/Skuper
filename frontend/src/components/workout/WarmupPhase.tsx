import { useState } from 'react';

const WARMUP_PHASES = [
  { name: 'Общая разминка', duration: '3-5 мин', description: 'Ходьба, велотренажёр или скакалка. Поднять пульс до 100-120.' },
  { name: 'Суставная гимнастика', duration: '3 мин', description: 'Вращения плечами, запястьями, коленями, тазом. По 10 повторений в каждую сторону.' },
  { name: 'Динамическая растяжка', duration: '2 мин', description: 'Махи ногами, выпады с поворотом, круги руками. Не статика!' },
  { name: 'Разминочные подходы', duration: '2-3 мин', description: 'Первое упражнение: пустой гриф × 15, 50% × 10, 70% × 5.' },
];

interface Props {
  onComplete: () => void;
}

export default function WarmupPhase({ onComplete }: Props) {
  const [current, setCurrent] = useState(0);

  const phase = WARMUP_PHASES[current];
  const isLast = current === WARMUP_PHASES.length - 1;

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <div className="card-title">Разминка</div>
          <span className="stat-label">{current + 1}/{WARMUP_PHASES.length}</span>
        </div>

        <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>{phase.name}</div>
        <div className="stat-label" style={{ marginBottom: 8 }}>{phase.duration}</div>
        <div style={{ fontSize: 14, lineHeight: 1.5, color: 'var(--text-secondary)' }}>
          {phase.description}
        </div>

        <div className="progress-bar" style={{ marginTop: 12 }}>
          <div className="progress-fill ok" style={{ width: `${((current + 1) / WARMUP_PHASES.length) * 100}%` }} />
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        {current > 0 && (
          <button className="btn btn-ghost" style={{ flex: 1 }}
            onClick={() => setCurrent(current - 1)}>
            Назад
          </button>
        )}
        <button className="btn btn-primary" style={{ flex: 1 }}
          onClick={() => isLast ? onComplete() : setCurrent(current + 1)}>
          {isLast ? 'Начать упражнения' : 'Далее'}
        </button>
      </div>
    </div>
  );
}
