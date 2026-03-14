import { useState } from 'react';
import type { WorkoutCreate } from '../../types';

interface Props {
  dayType: string;
  onSubmit: (data: WorkoutCreate) => void;
}

export default function PreWorkoutForm({ dayType, onSubmit }: Props) {
  const [energy, setEnergy] = useState(7);
  const [sleep, setSleep] = useState(7);
  const [sleepQuality, setSleepQuality] = useState(7);
  const [backPain, setBackPain] = useState(0);
  const [wave, setWave] = useState('');

  const handleSubmit = () => {
    onSubmit({
      day_type: dayType,
      energy_before: energy,
      sleep_hours: sleep,
      sleep_quality: sleepQuality,
      back_pain: backPain,
      emotional_wave: wave || undefined,
    });
  };

  return (
    <div>
      <div className="card">
        <div className="card-title">Энергия (1-10)</div>
        <input type="range" min={1} max={10} value={energy} onChange={(e) => setEnergy(+e.target.value)}
          style={{ width: '100%' }} />
        <div style={{ textAlign: 'center', fontSize: 24, fontWeight: 700 }}>{energy}</div>
        {energy <= 5 && (
          <div style={{ color: 'var(--warning)', fontSize: 13, marginTop: 4 }}>
            Низкая энергия. Рассмотри сокращённую тренировку.
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">Сон (часов)</div>
        <input type="range" min={3} max={12} step={0.5} value={sleep}
          onChange={(e) => setSleep(+e.target.value)} style={{ width: '100%' }} />
        <div style={{ textAlign: 'center', fontSize: 18 }}>{sleep}ч</div>
      </div>

      <div className="card">
        <div className="card-title">Качество сна (1-10)</div>
        <input type="range" min={1} max={10} value={sleepQuality}
          onChange={(e) => setSleepQuality(+e.target.value)} style={{ width: '100%' }} />
        <div style={{ textAlign: 'center', fontSize: 18 }}>{sleepQuality}</div>
      </div>

      <div className="card">
        <div className="card-title">Боль в спине (0-10)</div>
        <input type="range" min={0} max={10} value={backPain}
          onChange={(e) => setBackPain(+e.target.value)} style={{ width: '100%' }} />
        <div style={{ textAlign: 'center', fontSize: 18 }}>{backPain}</div>
        {backPain >= 5 && (
          <div style={{ color: 'var(--danger)', fontSize: 13, marginTop: 4 }}>
            Высокая боль. Будь осторожен с осевой нагрузкой.
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">Эмоциональная волна</div>
        <div style={{ display: 'flex', gap: 8 }}>
          {['Низ', 'Середина', 'Верх'].map((w) => (
            <button key={w}
              className={`btn ${wave === w ? 'btn-primary' : 'btn-ghost'}`}
              style={{ flex: 1 }}
              onClick={() => setWave(w)}>
              {w}
            </button>
          ))}
        </div>
      </div>

      <button className="btn btn-primary btn-full" onClick={handleSubmit}>
        Начать тренировку
      </button>
    </div>
  );
}
